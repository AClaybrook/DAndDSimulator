// Shared planner data: options, the party's evaluation (recomputed shortly after each edit) and the shared enemy
import { useDebouncedValue } from '@mantine/hooks'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
import { api, bg3 } from '../../api'
import { useParty } from '../../party'
import { useSimulator } from '../../store'

export function usePlannerOptions() {
  return useQuery({ queryKey: ['planner-options'], queryFn: bg3.plannerOptions, staleTime: Infinity })
}

// The enemy and fight length are the simulator's: one enemy for the whole app
export function useSharedEnemy() {
  const { enemy, settings, setAll } = useSimulator()
  useEffect(() => {
    if (!enemy) api.defaults().then((d) => setAll(d.characters, d.enemy))
  }, [enemy, setAll])
  return { enemy, rounds: settings.roundsPerFight }
}

export function useEvaluation() {
  const { party, attackBonus } = useParty()
  const { enemy, rounds } = useSharedEnemy()
  const key = useMemo(() => JSON.stringify({ party, enemy, rounds, attackBonus }), [party, enemy, rounds, attackBonus])
  const [debounced] = useDebouncedValue(key, 250)
  return useQuery({
    queryKey: ['evaluate', debounced],
    queryFn: () => {
      const v = JSON.parse(debounced)
      return bg3.evaluate(v.party, v.enemy, v.rounds, v.attackBonus)
    },
    enabled: party.length > 0 && Boolean(enemy),
    placeholderData: (previous) => previous,
  })
}
