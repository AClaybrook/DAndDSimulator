import { ActionIcon, AppShell, Burger, Container, Drawer, Group, Kbd, Modal, NavLink, Stack, Table, Tabs, Text, Tooltip, useComputedColorScheme, useMantineColorScheme } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useShortcuts } from './hotkeys'
import { IconChartHistogram, IconKeyboard, IconMap, IconMoon, IconSun, IconSwords, IconTrophy } from '@tabler/icons-react'
import { useEffect, useRef, useState } from 'react'
import { SessionMenu } from './components/SessionMenu'
import { LeaderboardPage } from './pages/leaderboard/LeaderboardPage'
import { MapPage } from './pages/map/MapPage'
import { PlannerPage } from './pages/planner/PlannerPage'
import { SimulatorPage } from './pages/simulator/SimulatorPage'

const SHORTCUTS: [string, string][] = [
  ['1 – 4', 'Party planner, Leaderboard, Item map, Simulator'], ['t', 'Light or dark theme'], ['r', 'Simulator: simulate again'], ['?', 'This list'],
]

const PAGES = [
  { key: 'planner', label: 'Party planner', icon: IconSwords, page: PlannerPage },
  { key: 'leaderboard', label: 'Leaderboard', icon: IconTrophy, page: LeaderboardPage },
  { key: 'map', label: 'Item map', icon: IconMap, page: MapPage },
  { key: 'simulator', label: 'Simulator', icon: IconChartHistogram, page: SimulatorPage },
]

// Pages live in the URL hash (#/simulator), so a reload or a shared link opens the same page
const currentPage = () => window.location.hash.replace('#/', '').split('?')[0] || 'planner'

export default function App() {
  const [menu, { toggle, close }] = useDisclosure()
  const [help, helpControls] = useDisclosure()
  const { setColorScheme } = useMantineColorScheme()
  const scheme = useComputedColorScheme('dark')
  const toggleScheme = () => setColorScheme(scheme === 'dark' ? 'light' : 'dark')
  const [page, setPage] = useState(currentPage)
  useEffect(() => {
    const onHash = () => setPage(currentPage())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const active = PAGES.find((p) => p.key === page) ?? PAGES[0]
  // Each page's URL settings (leaderboard filters, map act) come back when you return to it
  const queries = useRef<Record<string, string>>({})
  const go = (key: string | null) => {
    if (key) {
      queries.current[active.key] = window.location.hash.split('?')[1] ?? ''
      const query = queries.current[key]
      window.location.hash = `#/${key}${query ? `?${query}` : ''}`
    }
    close()
  }

  useShortcuts([
    ...PAGES.map((p, i): [string, () => void] => [String(i + 1), () => go(p.key)]),
    ['t', toggleScheme],
    ['shift+/', helpControls.toggle],
  ])

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
          <div style={{ flex: 1 }} />
          <Group gap={6} wrap="nowrap">
            <Tooltip label="Keyboard shortcuts (?)">
              <ActionIcon variant="default" size="lg" onClick={helpControls.open} aria-label="Keyboard shortcuts" visibleFrom="sm"><IconKeyboard size={18} /></ActionIcon>
            </Tooltip>
            <Tooltip label={`${scheme === 'dark' ? 'Light' : 'Dark'} theme (t)`}>
              <ActionIcon variant="default" size="lg" onClick={toggleScheme} aria-label="Theme">{scheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}</ActionIcon>
            </Tooltip>
            <SessionMenu />
          </Group>
        </Group>
      </AppShell.Header>
      <Modal opened={help} onClose={helpControls.close} title="Keyboard shortcuts" size="sm">
        <Table>
          <Table.Tbody>
            {SHORTCUTS.map(([keys, what]) => <Table.Tr key={keys}><Table.Td><Kbd>{keys}</Kbd></Table.Td><Table.Td>{what}</Table.Td></Table.Tr>)}
          </Table.Tbody>
        </Table>
      </Modal>
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
