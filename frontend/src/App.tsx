import { AppShell, Burger, Container, Drawer, Group, NavLink, Stack, Tabs, Text } from '@mantine/core'
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
  const [menu, { toggle, close }] = useDisclosure()
  const [page, setPage] = useState(currentPage)
  useEffect(() => {
    const onHash = () => setPage(currentPage())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const active = PAGES.find((p) => p.key === page) ?? PAGES[0]
  const go = (key: string | null) => { if (key) window.location.hash = `#/${key}`; close() }

  return (
    <AppShell header={{ height: 56 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="lg" gap="xl" wrap="nowrap">
          <Group gap={8} wrap="nowrap">
            <Burger opened={menu} onClick={toggle} hiddenFrom="sm" size="sm" />
            <div className="logo">d20</div>
            <Text fw={700} size="md" visibleFrom="xs">Damage Lab</Text>
            <Text size="xs" c="dimmed" visibleFrom="lg">D&amp;D 5e and Baldur's Gate 3</Text>
          </Group>
          <Tabs value={active.key} onChange={go} variant="pills" radius="md" visibleFrom="sm" classNames={{ list: 'nav-tabs' }}>
            <Tabs.List>
              {PAGES.map((p) => <Tabs.Tab key={p.key} value={p.key} leftSection={<p.icon size={16} />}>{p.label}</Tabs.Tab>)}
            </Tabs.List>
          </Tabs>
        </Group>
      </AppShell.Header>
      <Drawer opened={menu} onClose={close} size={260} title="Damage Lab">
        <Stack gap={4}>
          {PAGES.map((p) => <NavLink key={p.key} label={p.label} leftSection={<p.icon size={18} />} active={p.key === active.key} onClick={() => go(p.key)} />)}
        </Stack>
      </Drawer>
      <AppShell.Main>
        <Container size="100%" px="lg" py="lg" maw={1680}>
          <active.page />
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}
