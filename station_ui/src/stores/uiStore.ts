/**
 * UI state store.
 * Manages theme, sidebar, and other UI preferences.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'dark' | 'light';
export type BatchListLayout = 'vertical' | 'horizontal' | 'grid';

interface UIState {
  // State
  theme: Theme;
  sidebarCollapsed: boolean;
  batchListLayout: BatchListLayout;

  // Actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setBatchListLayout: (layout: BatchListLayout) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'dark',
      sidebarCollapsed: false,
      batchListLayout: 'vertical',

      // Actions
      setTheme: (theme) => {
        // Update HTML class for Tailwind dark mode
        if (theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
        set({ theme });
      },

      toggleTheme: () =>
        set((state) => {
          const newTheme = state.theme === 'dark' ? 'light' : 'dark';
          if (newTheme === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
          return { theme: newTheme };
        }),

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setBatchListLayout: (layout) => set({ batchListLayout: layout }),
    }),
    {
      name: 'station-ui-settings',
      partialize: (state) => ({ theme: state.theme, batchListLayout: state.batchListLayout }),
      onRehydrateStorage: () => (state) => {
        // Apply theme on rehydration
        if (state?.theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },
    }
  )
);
