import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  tenantId: number | null
  username: string | null
  setAuth: (token: string, tenantId: number, username: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      tenantId: null,
      username: null,
      setAuth: (token, tenantId, username) => set({ token, tenantId, username }),
      logout: () => set({ token: null, tenantId: null, username: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
