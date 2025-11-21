import { create } from 'zustand'

type Tool = 'select' | 'bbox'

interface WorkspaceState {
  selectedClassId: number | null
  setSelectedClassId: (id: number | null) => void
  tool: Tool
  setTool: (tool: Tool) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedClassId: null,
  setSelectedClassId: (id) => set({ selectedClassId: id }),
  tool: 'bbox',
  setTool: (tool) => set({ tool }),
}))

