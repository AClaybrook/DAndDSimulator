// Page shortcuts: they work everywhere except while typing (text fields), so radios and switches don't swallow them
import { useHotkeys } from '@mantine/hooks'

const TEXT_INPUTS = new Set(['text', 'search', 'number', 'email', 'url', 'password', 'tel'])

function typing() {
  const el = document.activeElement as HTMLInputElement | null
  if (!el) return false
  return el.isContentEditable || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || (el.tagName === 'INPUT' && TEXT_INPUTS.has(el.type))
}

export function useShortcuts(keys: [string, () => void][]) {
  useHotkeys(keys.map(([key, action]) => [key, () => { if (!typing()) action() }]), [])
}
