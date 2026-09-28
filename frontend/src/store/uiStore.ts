import { create } from 'zustand'

interface UIState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  setSidebar: (v: boolean) => void
  /* 本次任务的模型选择，提交给后端并持久化 */
  model: string
  setModel: (m: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebar: (v) => set({ sidebarCollapsed: v }),
  model: 'auto',
  setModel: (m) => set({ model: m }),
}))
