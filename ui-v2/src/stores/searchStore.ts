import { create } from 'zustand';
import { api, type SearchResult } from '../lib/api';

interface SearchState {
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  error: string | null;
  lastSearched: string | null;
  setQuery: (query: string) => void;
  search: (query: string) => Promise<SearchResult[]>;
  clearResults: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  results: [],
  isSearching: false,
  error: null,
  lastSearched: null,
  setQuery: (query) => set({ query }),
  search: async (query) => {
    set({ isSearching: true, error: null });
    try {
      const data = await api.search(query, 6);
      set({ isSearching: false, results: data.results, lastSearched: query });
      return data.results;
    } catch (e) {
      set({
        isSearching: false,
        results: [],
        error: e instanceof Error ? e.message : 'Search failed',
      });
      return [];
    }
  },
  clearResults: () => set({ results: [], lastSearched: null }),
}));
