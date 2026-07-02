import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { JobDescription, RankingResult, User } from "../types";

interface AppState {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;

  // Active job / flow
  activeJd: JobDescription | null;
  setActiveJd: (jd: JobDescription | null) => void;
  candidateCount: number;
  setCandidateCount: (n: number) => void;

  // Rankings
  rankings: RankingResult[];
  setRankings: (r: RankingResult[]) => void;

  // Compare
  compareIds: number[];
  toggleCompare: (id: number) => void;
  clearCompare: () => void;

  // Uploads
  isUploading: boolean;
  setIsUploading: (v: boolean) => void;
  uploadErrors: string[];
  setUploadErrors: (e: string[]) => void;

  // Ranking run
  isRanking: boolean;
  setIsRanking: (v: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      token: null,
      setAuth: (user, token) => {
        localStorage.setItem("auth_token", token);
        set({ user, token });
      },
      clearAuth: () => {
        localStorage.removeItem("auth_token");
        set({ user: null, token: null });
      },

      // Active JD
      activeJd: null,
      setActiveJd: (jd) => set({ activeJd: jd, rankings: [], compareIds: [] }),
      candidateCount: 0,
      setCandidateCount: (n) => set({ candidateCount: n }),

      // Rankings
      rankings: [],
      setRankings: (r) => set({ rankings: r }),

      // Compare (max 4)
      compareIds: [],
      toggleCompare: (id) => {
        const { compareIds } = get();
        if (compareIds.includes(id)) {
          set({ compareIds: compareIds.filter((x) => x !== id) });
        } else if (compareIds.length < 4) {
          set({ compareIds: [...compareIds, id] });
        }
      },
      clearCompare: () => set({ compareIds: [] }),

      // Upload state
      isUploading: false,
      setIsUploading: (v) => set({ isUploading: v }),
      uploadErrors: [],
      setUploadErrors: (e) => set({ uploadErrors: e }),

      // Ranking state
      isRanking: false,
      setIsRanking: (v) => set({ isRanking: v }),
    }),
    {
      name: "ai-recruiter-store",
      // only persist auth + active JD between page reloads
      partialize: (s) => ({ user: s.user, token: s.token, activeJd: s.activeJd }),
    }
  )
);
