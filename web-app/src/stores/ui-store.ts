import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'
type AccentColor = 'indigo' | 'blue' | 'violet' | 'rose' | 'emerald' | 'amber'

interface UiState {
  sidebarCollapsed: boolean
  theme: Theme
  accentColor: AccentColor
}

interface UiActions {
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setTheme: (theme: Theme) => void
  setAccentColor: (color: AccentColor) => void
}

function resolveSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyThemeClass(theme: Theme) {
  const resolved = theme === 'system' ? resolveSystemTheme() : theme
  document.documentElement.classList.toggle('dark', resolved === 'dark')
}

const ACCENT_VARS: Record<AccentColor, { primary: string; ring: string; primaryDark: string; ringDark: string }> = {
  indigo:  { primary: '245 58% 51%', ring: '245 58% 51%', primaryDark: '245 58% 61%', ringDark: '245 58% 61%' },
  blue:    { primary: '221 83% 53%',  ring: '221 83% 53%',  primaryDark: '217 91% 60%',  ringDark: '224 76% 48%' },
  violet:  { primary: '262 83% 58%',  ring: '262 83% 58%',  primaryDark: '263 70% 50%',  ringDark: '263 70% 50%' },
  rose:    { primary: '346 77% 50%',  ring: '346 77% 50%',  primaryDark: '346 77% 60%',  ringDark: '346 77% 60%' },
  emerald: { primary: '160 84% 39%',  ring: '160 84% 39%',  primaryDark: '160 67% 52%',  ringDark: '160 67% 52%' },
  amber:   { primary: '38 92% 50%',   ring: '38 92% 50%',   primaryDark: '38 92% 50%',   ringDark: '38 92% 50%' },
}

function applyAccentColor(color: AccentColor) {
  const vars = ACCENT_VARS[color]
  const root = document.documentElement.style
  root.setProperty('--primary', vars.primary)
  root.setProperty('--ring', vars.ring)

  const darkSheet = Array.from(document.styleSheets).flatMap((s) => {
    try { return Array.from(s.cssRules) } catch { return [] }
  }).find((r) => r instanceof CSSStyleRule && r.selectorText === '.dark') as CSSStyleRule | undefined

  if (darkSheet) {
    darkSheet.style.setProperty('--primary', vars.primaryDark)
    darkSheet.style.setProperty('--ring', vars.ringDark)
  }
}

export const useUiStore = create<UiState & UiActions>()(
  persist(
    (set, get) => ({
      sidebarCollapsed: false,
      theme: 'system',
      accentColor: 'indigo',

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),

      setTheme: (theme) => {
        applyThemeClass(theme)
        set({ theme })
      },

      setAccentColor: (color) => {
        applyAccentColor(color)
        set({ accentColor: color })
      },
    }),
    {
      name: 'kira-ui',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyThemeClass(state.theme)
          applyAccentColor(state.accentColor)
        }
      },
    },
  ),
)

if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme } = useUiStore.getState()
    if (theme === 'system') applyThemeClass('system')
  })
}

export type { Theme, AccentColor }
