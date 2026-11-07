import { AppShell, Burger, Group, NavLink, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconChartHistogram, IconMap, IconSwords, IconTrophy } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { LeaderboardPage } from './pages/leaderboard/LeaderboardPage'
import { MapPage } from './pages/map/MapPage'
import { PlannerPage } from './pages/planner/PlannerPage'
import { SimulatorPage } from './pages/simulator/SimulatorPage'

const PAGES = [
  { key: 'planner', label: 'Party planner', icon: IconSwords, page: PlannerPage },
  { key: 'leaderboard', label: 'Leaderboard', icon: IconTrophy, page: LeaderboardPage },
  { key: 'map', label: 'Act 1 map', icon: IconMap, page: MapPage },
  { key: 'simulator', label: 'Simulator', icon: IconChartHistogram, page: SimulatorPage },
]

// Pages live in the URL hash (#/simulator), so a reload or a shared link opens the same page
const currentPage = () => window.location.hash.replace('#/', '') || 'planner'

export default function App() {
  const [opened, { toggle, close }] = useDisclosure()
  const [page, setPage] = useState(currentPage)
  useEffect(() => {
    const onHash = () => setPage(currentPage())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const active = PAGES.find((p) => p.key === page) ?? PAGES[0]

  return (
    <AppShell header={{ height: 48 }} navbar={{ width: 200, breakpoint: 'sm', collapsed: { mobile: !opened } }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" gap="sm">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Title order={4}>D&amp;D Damage Simulator</Title>
          <Text size="sm" c="dimmed" visibleFrom="sm">· {active.label}</Text>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        {PAGES.map((p) => (
          <NavLink key={p.key} href={`#/${p.key}`} label={p.label} leftSection={<p.icon size={18} />} active={p.key === active.key}
            onClick={close} />
        ))}
      </AppShell.Navbar>
      <AppShell.Main><active.page /></AppShell.Main>
    </AppShell>
  )
}
