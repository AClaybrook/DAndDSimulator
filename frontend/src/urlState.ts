// Page settings kept in the URL after the page's hash (#/leaderboard?scenario=nova&enemies=2), so a reload or a shared link keeps them
import { useCallback, useState } from 'react'

const params = () => new URLSearchParams(window.location.hash.split('?')[1] ?? '')

function write(key: string, value: string | null) {
  const [page] = window.location.hash.split('?')
  const p = params()
  if (value === null) p.delete(key)
  else p.set(key, value)
  const query = p.toString()
  // replaceState doesn't fire hashchange, so the page isn't reloaded and the back button isn't filled with every click
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${page || '#/'}${query ? `?${query}` : ''}`)
}

// Like useState, read from and written to the URL; the default isn't written, so links stay short
export function useUrlState(key: string, fallback: string): [string, (v: string) => void] {
  const [value, setValue] = useState(() => params().get(key) ?? fallback)
  const set = useCallback((v: string) => { setValue(v); write(key, v === fallback ? null : v) }, [key, fallback])
  return [value, set]
}

export function useUrlList(key: string, fallback: string[]): [string[], (v: string[]) => void] {
  const [value, setValue] = useState(() => {
    const raw = params().get(key)
    return raw === null ? fallback : raw.split(',').filter(Boolean)
  })
  const fallbackKey = fallback.join(',')
  const set = useCallback((v: string[]) => { setValue(v); write(key, v.join(',') === fallbackKey ? null : v.join(',')) }, [key, fallbackKey])
  return [value, set]
}
