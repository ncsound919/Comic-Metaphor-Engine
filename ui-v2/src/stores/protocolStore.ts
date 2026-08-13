import { create } from 'zustand';
import { api, type ProtocolSummary } from '../lib/api';

interface ProtocolState {
  protocols: ProtocolSummary[];
  selectedProtocol: ProtocolSummary | null;
  isLoading: boolean;
  error: string | null;
  fetchProtocols: () => Promise<void>;
  selectProtocol: (protocol: ProtocolSummary | null) => void;
}

export const useProtocolStore = create<ProtocolState>((set) => ({
  protocols: [],
  selectedProtocol: null,
  isLoading: false,
  error: null,
  fetchProtocols: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.listProtocols({ limit: 100 });
      set({ protocols: data.protocols, isLoading: false });
    } catch (e) {
      set({ isLoading: false, error: e instanceof Error ? e.message : 'Failed to load protocols' });
    }
  },
  selectProtocol: (protocol) => set({ selectedProtocol: protocol }),
}));
