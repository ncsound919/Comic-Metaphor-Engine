import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  activeNavItem: string;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setActiveNavItem: (item: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarCollapsed: false,
      activeNavItem: 'search',
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setActiveNavItem: (item) => set({ activeNavItem: item }),
    }),
    { name: 'comic-metaphor-ui-storage' }
  )
);