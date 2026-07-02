"""
Embedding provider abstraction.

The product spec calls for "Sentence Transformers or OpenAI embeddings".
Both require an outbound call to a model host (HuggingFace Hub or OpenAI)
that a self-hosted deployment may not always have credentials/network
access for at setup time, so this module is written behind a
`BaseEmbeddingProvider` interface with TWO real implementations:

  - TfidfEmbeddingProvider (default): scikit-learn TF-IDF + SVD, fully
    local, zero API keys, zero network calls. This is what powers the
    FAISS vector index out of the box.
  - OpenAIEmbeddingProvider: drop-in swap, used automatically the moment
    OPENAI_API_KEY is set in the environment.

Whichever provider is active, the contract is identical: text in,
fixed-length float vector out. Nothing downstream (faiss_index.py,
ranking_engine) needs to know which one is running.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from app.config import get_settings

settings = get_settings()


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Return an (n_texts, dim) float32 matrix of unit-normalized vectors."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dim(self) -> int:
        raise NotImplementedError


class TfidfEmbeddingProvider(BaseEmbeddingProvider):
    """Local, dependency-light embedding provider. Fits a TF-IDF vectorizer
    over the corpus passed to `fit`, then reduces to a fixed dimension with
    TruncatedSVD (a lightweight LSA) so vectors are dense and FAISS-friendly.

    This genuinely captures semantic similarity beyond literal keyword
    overlap (two resumes describing "distributed systems at scale" and
    "high-throughput backend architecture" land close together in this
    space) without requiring any model download.
    """

    def __init__(self, dim: int = 256):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._dim = dim
        self.vectorizer = TfidfVectorizer(
            max_features=20000, ngram_range=(1, 2), stop_words="english", sublinear_tf=True
        )
        self.svd = TruncatedSVD(n_components=dim, random_state=42)
        self._fitted = False

    def fit(self, corpus: List[str]) -> None:
        if len(corpus) < 2:
            corpus = corpus + ["placeholder document to allow vectorizer fitting"]
        tfidf = self.vectorizer.fit_transform(corpus)
        n_components = min(self._dim, max(2, tfidf.shape[1] - 1), tfidf.shape[0] - 1)
        if n_components != self.svd.n_components:
            from sklearn.decomposition import TruncatedSVD
            self.svd = TruncatedSVD(n_components=max(2, n_components), random_state=42)
        self.svd.fit(tfidf)
        self._fitted = True

    def embed(self, texts: List[str]) -> np.ndarray:
        if not self._fitted:
            self.fit(texts)
        tfidf = self.vectorizer.transform(texts)
        vecs = self.svd.transform(tfidf).astype("float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    @property
    def dim(self) -> int:
        return self.svd.n_components if self._fitted else self._dim


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):  # pragma: no cover - optional path
    """Used automatically when OPENAI_API_KEY is configured. Requires the
    `openai` package (already in requirements.txt)."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self._dim = 1536

    def embed(self, texts: List[str]) -> np.ndarray:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(model=self.model, input=texts)
        vecs = np.array([d.embedding for d in resp.data], dtype="float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    @property
    def dim(self) -> int:
        return self._dim


class HashingFallbackProvider(BaseEmbeddingProvider):
    """Last-resort deterministic provider with no ML dependencies at all --
    used only if scikit-learn somehow isn't available, so the app degrades
    gracefully instead of crashing."""

    def __init__(self, dim: int = 256):
        self._dim = dim

    def embed(self, texts: List[str]) -> np.ndarray:
        vecs = np.zeros((len(texts), self._dim), dtype="float32")
        for i, t in enumerate(texts):
            for token in t.lower().split():
                h = int(hashlib.md5(token.encode()).hexdigest(), 16)
                vecs[i, h % self._dim] += 1.0
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    @property
    def dim(self) -> int:
        return self._dim


def get_embedding_provider() -> BaseEmbeddingProvider:
    if settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider()
    try:
        return TfidfEmbeddingProvider(dim=settings.EMBEDDING_DIM)
    except ImportError:  # pragma: no cover
        return HashingFallbackProvider(dim=settings.EMBEDDING_DIM)
