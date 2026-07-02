"""
Thin FAISS wrapper: build an in-memory index per ranking run (one JD against
its candidate pool), query nearest neighbours by cosine similarity. FAISS
indexes are rebuilt per job-description rather than persisted globally,
since semantic matching here is JD-relative -- the candidate pool, JD text,
and the embedding space all need to be fit together for a meaningful score.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from app.vector_store.embedding_provider import BaseEmbeddingProvider, get_embedding_provider


class CandidateVectorIndex:
    """Wraps a FAISS IndexFlatIP (inner product == cosine similarity since
    vectors are unit-normalized) over a single batch of candidate resumes."""

    def __init__(self, provider: BaseEmbeddingProvider | None = None):
        self.provider = provider or get_embedding_provider()
        self.index = None
        self.candidate_ids: List[int] = []

    def build(self, candidate_ids: List[int], texts: List[str]) -> None:
        import faiss

        if hasattr(self.provider, "fit"):
            self.provider.fit(texts)
        vectors = self.provider.embed(texts)
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vectors)
        self.candidate_ids = candidate_ids
        self._vectors = vectors  # retained for pairwise similarity / clustering

    def query(self, text: str, top_k: int | None = None) -> List[Tuple[int, float]]:
        """Return [(candidate_id, similarity_0_to_1), ...] sorted descending."""
        if self.index is None:
            return []
        top_k = top_k or len(self.candidate_ids)
        query_vec = self.provider.embed([text])
        scores, idx = self.index.search(query_vec, min(top_k, len(self.candidate_ids)))
        results = []
        for score, i in zip(scores[0], idx[0]):
            if i == -1:
                continue
            # inner product of unit vectors is in [-1, 1]; rescale to [0, 1]
            similarity = float((score + 1.0) / 2.0)
            results.append((self.candidate_ids[i], similarity))
        return sorted(results, key=lambda r: r[1], reverse=True)

    def pairwise_similarity_matrix(self) -> np.ndarray:
        """Full candidate-x-candidate cosine similarity matrix, used by the
        duplicate-candidate detector and the resume-similarity graph bonus
        feature."""
        if not hasattr(self, "_vectors"):
            return np.zeros((0, 0))
        return self._vectors @ self._vectors.T

    def similarity_between(self, candidate_id_a: int, candidate_id_b: int) -> float:
        if candidate_id_a not in self.candidate_ids or candidate_id_b not in self.candidate_ids:
            return 0.0
        ia = self.candidate_ids.index(candidate_id_a)
        ib = self.candidate_ids.index(candidate_id_b)
        sim = float(self._vectors[ia] @ self._vectors[ib])
        return (sim + 1.0) / 2.0
