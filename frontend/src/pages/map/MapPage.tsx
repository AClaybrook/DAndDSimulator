import {
  Anchor, Badge, Center, Checkbox, Chip, Grid, Group, Loader, MultiSelect, ScrollArea, SegmentedControl, Stack, Switch, Tabs, Text,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { bg3, type MapData, type MapPoint } from '../../api'
import { PageHeader, Section } from '../../components/Layout'
import { Plot, type PlotClick } from '../../components/Plot'
import { useParty } from '../../party'
import { useUrlState } from '../../urlState'

const RANK = (data: MapData, rarity: string) => (data.rarities.includes(rarity) ? data.rarities.indexOf(rarity) : data.rarities.length)
const LABELLED = new Set(['Key', 'Legendary', 'Very Rare', 'Story'])
const MAP_CONFIG = { scrollZoom: true }

interface Filters { rarities: string[]; missables: boolean; onlyMissables: boolean; names: boolean; partyOnly: boolean; builds: boolean; noTraders: boolean; noInside: boolean }

function visible(p: MapPoint, f: Filters, search: string[], party: Set<string>) {
  if (search.includes(p.name) || party.has(p.key)) return true
  if (f.partyOnly) return false
  if (f.onlyMissables) return Boolean(p.missable)
  if (!f.rarities.includes(p.rarity)) return false
  if (f.builds && p.rarity !== 'Key' && !p.builds.length) return false
  if (f.noTraders && p.trader) return false
  if (f.noInside && p.inside) return false
  return true
}

// Points on a map grouped by spot, best rarity first in each
function spotsOf(data: MapData, mapKey: string, f: Filters, search: string[], party: Set<string>) {
  const image = data.maps.find((m) => m.key === mapKey)?.image
  const bySpot = new Map<string, MapPoint[]>()
  for (const p of data.points) {
    if (p.map !== mapKey || !visible(p, f, search, party)) continue
    const id = image ? `${p.px},${p.py}` : `${p.x},${p.y}`
    bySpot.set(id, [...(bySpot.get(id) ?? []), p])
  }
  return [...bySpot.entries()].map(([id, ps]) => ({ id, points: ps.sort((a, b) => RANK(data, a.rarity) - RANK(data, b.rarity) || a.name.localeCompare(b.name)) }))
}

export function MapPage() {
  const data = useQuery({ queryKey: ['map'], queryFn: bg3.mapData, staleTime: Infinity })
  const { party, collected, toggleCollected } = useParty()
  const [mapKey, setMapKey] = useUrlState('region', 'wilderness')
  const [act, setActState] = useUrlState('act', '1')
  const [search, setSearch] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [tab, setTab] = useState<string | null>('party')
  const [filters, setFilters] = useState<Filters>({
    rarities: ['Key', 'Legendary', 'Story', 'Very Rare', 'Rare'], missables: true, onlyMissables: false, names: false, partyOnly: false, builds: false, noTraders: false, noInside: false,
  })
  const gear = useQuery({ queryKey: ['party-gear', party, act], queryFn: () => bg3.partyGear(party, act), enabled: party.length > 0 })
  // Party members whose gear is marked; all of them until some are unticked
  const [hiddenMembers, setHiddenMembers] = useState<string[]>([])
  const shownGear = useMemo(() => (gear.data ?? []).filter((g) => g.members.some((m) => !hiddenMembers.includes(m))), [gear.data, hiddenMembers])
  const wanted = useMemo(() => new Set(shownGear.filter((g) => !collected.includes(g.key)).map((g) => g.key)), [shownGear, collected])
  const users = useMemo(() => Object.fromEntries((gear.data ?? []).map((g) => [g.key, g.users])), [gear.data])
  const set = (change: Partial<Filters>) => setFilters((f) => ({ ...f, ...change }))
  // The act picks the regions shown, the party's gear and the items with no spot
  const setAct = (a: string) => {
    setActState(a)
    setMapKey(data.data?.maps.find((m) => String(m.act) === a)?.key ?? mapKey)
    setSelected(null)
  }

  const spots = useMemo(() => (data.data ? spotsOf(data.data, mapKey, filters, search, wanted) : []), [data.data, mapKey, filters, search, wanted])
  const figure = useMemo(() => (data.data ? mapFigure(data.data, mapKey, spots, filters, search, wanted, users) : null), [data.data, mapKey, spots, filters, search, wanted, users])
  const counts = useMemo(() => Object.fromEntries((data.data?.maps ?? []).map((m) => [m.key, data.data!.points.filter((p) => p.map === m.key && visible(p, filters, search, wanted)).length])),
    [data.data, filters, search, wanted])

  if (!data.data || !figure) return <Center h={300}><Loader /></Center>
  const d = data.data
  const chosen = spots.find((s) => s.id === selected)
  const names = [...new Set(d.points.map((p) => p.name))].sort()
  const actMaps = d.maps.filter((m) => String(m.act) === act)
  const mapName = (key: string) => { const m = d.maps.find((x) => x.key === key)!; return `${m.label} (Act ${m.act})` }
  const found = search.map((name) => ({ name, maps: [...new Set(d.points.filter((p) => p.name === name).map((p) => mapName(p.map)))] }))
  const onClick = (point: PlotClick) => {
    const id = (point.customdata as string[] | undefined)?.[0]
    if (id) { setSelected(id); setTab('selected') }
  }

  return (
    <>
      <PageHeader title="Item map" subtitle="Where to find the notable gear and key pickups. Click a marker for its items; scroll to zoom."
        actions={<SegmentedControl size="xs" value={act} onChange={setAct} data={d.acts.map((a) => ({ value: String(a), label: `Act ${a}` }))} />} />
      <SegmentedControl fullWidth value={mapKey} onChange={(k) => { setMapKey(k); setSelected(null) }} mb="md"
        data={actMaps.map((m) => ({ value: m.key, label: <Group gap={6} justify="center" wrap="nowrap"><span>{m.label}</span><Badge size="xs" variant="light">{counts[m.key]}</Badge></Group> }))} />
      <Grid gap="md">
        <Grid.Col span={{ base: 12, lg: 8 }}>
          <Section padding="xs">
            <Group gap="sm" wrap="wrap" px={4}>
              <Chip.Group multiple value={filters.rarities} onChange={(rarities) => set({ rarities })}>
                <Group gap={4}>{d.rarities.map((r) => <Chip key={r} value={r} size="xs" color={d.colors[r]} variant="outline">{r === 'Key' ? 'Key pickups' : r}</Chip>)}</Group>
              </Chip.Group>
              <MultiSelect size="xs" placeholder="Find items on any map..." data={names} value={search} onChange={setSearch} searchable clearable style={{ flex: 1, minWidth: 220 }} />
            </Group>
            <Plot figure={figure} height="72vh" onClick={onClick} config={MAP_CONFIG} keepColors />
            <Group gap="md" px={4} pb={4}>
              <Switch size="xs" label="Mark missables" checked={filters.missables} onChange={(e) => set({ missables: e.currentTarget.checked })} />
              <Switch size="xs" label="Only missables" checked={filters.onlyMissables} onChange={(e) => set({ onlyMissables: e.currentTarget.checked })} />
              <Switch size="xs" label="Item names" checked={filters.names} onChange={(e) => set({ names: e.currentTarget.checked })} />
              <Switch size="xs" label="Only my party's gear" checked={filters.partyOnly} onChange={(e) => set({ partyOnly: e.currentTarget.checked })} />
              <Switch size="xs" label="Only example build gear" checked={filters.builds} onChange={(e) => set({ builds: e.currentTarget.checked })} />
              <Switch size="xs" label="Hide traders" checked={filters.noTraders} onChange={(e) => set({ noTraders: e.currentTarget.checked })} />
              <Switch size="xs" label="Hide dungeon items" checked={filters.noInside} onChange={(e) => set({ noInside: e.currentTarget.checked })} />
            </Group>
          </Section>
          {found.length > 0 && <Text size="xs" mt={6}>{found.map((f) => `${f.name}: ${f.maps.join(', ')}`).join(' · ')}</Text>}
        </Grid.Col>
        <Grid.Col span={{ base: 12, lg: 4 }}>
          <Section padding="sm">
            <Tabs value={tab} onChange={setTab}>
              <Tabs.List grow>
                <Tabs.Tab value="party">Party{wanted.size ? ` (${wanted.size})` : ''}</Tabs.Tab>
                <Tabs.Tab value="selected">Selected</Tabs.Tab>
                <Tabs.Tab value="list">List</Tabs.Tab>
                <Tabs.Tab value="elsewhere">Elsewhere</Tabs.Tab>
              </Tabs.List>
              <ScrollArea h="68vh" mt="xs" offsetScrollbars>
                <Tabs.Panel value="party">
                  <Text size="xs" c="dimmed" mb="xs">Gold rings: gear your planner party wears at Act {act}. Tick items as you collect them.</Text>
                  {party.length > 1 && (
                    <Chip.Group multiple value={party.map((b) => b.name).filter((n) => !hiddenMembers.includes(n))}
                      onChange={(shown) => setHiddenMembers(party.map((b) => b.name).filter((n) => !shown.includes(n)))}>
                      <Group gap={4} mb="sm">{party.map((b) => <Chip key={b.uid} value={b.name} size="xs">{b.name.split(' (')[0]}</Chip>)}</Group>
                    </Chip.Group>
                  )}
                  {!party.length && <Text size="sm" c="dimmed">Add characters in the Party planner to see their gear here.</Text>}
                  <Stack gap={8}>
                    {shownGear.map((g) => (
                      <Checkbox key={g.key} size="xs" checked={collected.includes(g.key)} onChange={() => toggleCollected(g.key)}
                        label={<div><Text size="sm" fw={500} td={collected.includes(g.key) ? 'line-through' : undefined}>{g.name}</Text>
                          <Text size="xs" c="dimmed">{g.users.join(', ')}</Text><Text size="xs">{g.where}</Text>
                          {g.missable && <Text size="xs" c="red">Missable: {g.missable}</Text>}</div>} />
                    ))}
                  </Stack>
                </Tabs.Panel>
                <Tabs.Panel value="selected">
                  {chosen ? <SpotDetails data={d} points={chosen.points} users={users} /> : <Text size="sm" c="dimmed">Click a marker on the map.</Text>}
                </Tabs.Panel>
                <Tabs.Panel value="list"><MapList data={d} spots={spots} wanted={wanted} onPick={(id) => { setSelected(id); setTab('selected') }} /></Tabs.Panel>
                <Tabs.Panel value="elsewhere">
                  <Text size="xs" c="dimmed" mb="xs">Notable items with no spot on these maps: camp chests, traders' levelled stock, carried by wandering characters.</Text>
                  <Stack gap={6}>{d.unplaced.filter((u) => String(u.act) === act).map((u) => <ItemLine key={u.key + u.name} data={d} p={u} />)}</Stack>
                </Tabs.Panel>
              </ScrollArea>
            </Tabs>
          </Section>
        </Grid.Col>
      </Grid>
      <Text size="xs" c="dimmed" mt="sm">Item locations: <Anchor href="https://bg3.wiki" target="_blank" size="xs">bg3.wiki</Anchor> (CC BY-NC-SA 4.0). Map images: Baldur's Gate 3 minimap textures © Larian Studios, via bg3.wiki. Unofficial fan tool.</Text>
    </>
  )
}

function ItemLine({ data, p }: { data: MapData; p: MapPoint }) {
  return (
    <div>
      <Anchor href={p.source} target="_blank" size="sm" c={data.colors[p.rarity]}>{p.name}</Anchor>
      <Text span size="xs" c="dimmed"> {p.rarity}{p.slot ? `, ${p.slot.replace('_', ' ')}` : ''}</Text>
      {p.where && <Text size="xs">{p.where}</Text>}
    </div>
  )
}

function SpotDetails({ data, points, users }: { data: MapData; points: MapPoint[]; users: Record<string, string[]> }) {
  const first = points[0]
  return (
    <Stack gap="sm">
      <div>
        <Text fw={600}>{first.location}</Text>
        <Text size="xs" c="dimmed">Minimap X {first.x}, Y {first.y}{first.inside ? ' · inside, marked at the entrance' : ''}</Text>
      </div>
      {points.map((p) => (
        <div key={p.key + p.name}>
          <ItemLine data={data} p={p} />
          {p.notes && <Text size="xs" c="dimmed">{p.notes}</Text>}
          {p.missable && <Text size="xs" c="red">Missable: {p.missable}</Text>}
          {p.tip && p.tip !== p.missable && <Text size="xs" c="yellow">Checklist note: {p.tip}</Text>}
          {users[p.key] && <Text size="xs" c={data.partyColor}>Your party: {users[p.key].join(', ')}</Text>}
          {p.builds.length > 0 && <Text size="xs" c="blue">Used by: {p.builds.join(', ')}</Text>}
        </div>
      ))}
    </Stack>
  )
}

function MapList({ data, spots, wanted, onPick }: { data: MapData; spots: { id: string; points: MapPoint[] }[]; wanted: Set<string>; onPick: (id: string) => void }) {
  const byLocation = new Map<string, { id: string; points: MapPoint[] }>()
  for (const s of spots) {
    const loc = s.points[0].location + (s.points[0].inside ? ' (inside)' : '')
    const entry = byLocation.get(loc) ?? { id: s.id, points: [] }
    entry.points.push(...s.points)
    byLocation.set(loc, entry)
  }
  const ordered = [...byLocation.entries()].sort((a, b) => Math.min(...a[1].points.map((p) => RANK(data, p.rarity))) - Math.min(...b[1].points.map((p) => RANK(data, p.rarity))))
  return (
    <Stack gap="sm">
      {ordered.map(([loc, { id, points }]) => (
        <div key={loc}>
          <Anchor size="sm" fw={600} onClick={() => onPick(id)}>{loc}</Anchor>
          {points.map((p) => (
            <Text key={p.key + p.name} size="xs" c={data.colors[p.rarity]} ml="sm">{p.name}{wanted.has(p.key) ? ' ◎' : ''}</Text>
          ))}
        </div>
      ))}
    </Stack>
  )
}

function hover(data: MapData, points: MapPoint[], users: Record<string, string[]>) {
  const first = points[0]
  const lines = [`<b>${first.location}</b> (X ${first.x}, Y ${first.y})${first.inside ? ' · inside' : ''}`]
  for (const p of points.slice(0, 10)) {
    lines.push(`${p.builds.length ? '★ ' : ''}${p.name} <span style="color:${data.colors[p.rarity]}">(${p.rarity}${p.trader ? ', trader' : ''})</span>` +
      (users[p.key] ? `<br>&nbsp;&nbsp;<span style="color:${data.partyColor}">Party: ${users[p.key].join(', ')}</span>` : '') +
      (p.missable ? `<br>&nbsp;&nbsp;<span style="color:${data.missableColor}">Missable</span>` : ''))
  }
  if (points.length > 10) lines.push(`+${points.length - 10} more, click for the list`)
  return lines.join('<br>')
}

function mapFigure(data: MapData, mapKey: string, spots: { id: string; points: MapPoint[] }[], f: Filters, search: string[], wanted: Set<string>, users: Record<string, string[]>) {
  const m = data.maps.find((x) => x.key === mapKey)!
  const xy = (s: { points: MapPoint[] }) => (m.image ? [s.points[0].px!, s.points[0].py!] : [s.points[0].x, s.points[0].y])
  const traces: object[] = []
  for (const rarity of data.rarities) {
    const chosen = spots.filter((s) => s.points[0].rarity === rarity)
    if (!chosen.length) continue
    const hit = chosen.map((s) => s.points.some((p) => search.includes(p.name)))
    traces.push({
      type: 'scatter', mode: 'markers+text', name: rarity === 'Key' ? 'Key pickup' : rarity,
      x: chosen.map((s) => xy(s)[0]), y: chosen.map((s) => xy(s)[1]),
      text: chosen.map((s, i) => {
        const mine = s.points.find((p) => wanted.has(p.key))
        if (mine) return mine.name
        return f.names || hit[i] || LABELLED.has(s.points[0].rarity) ? s.points[0].name + (s.points.length > 1 ? ` +${s.points.length - 1}` : '') : ''
      }),
      textposition: 'top center', textfont: { size: 11, color: '#f2f2f2' },
      hovertext: chosen.map((s) => hover(data, s.points, users)), hoverinfo: 'text', customdata: chosen.map((s) => [s.id]),
      marker: { color: data.colors[rarity], size: chosen.map((s, i) => Math.min(10 + 2 * (s.points.length - 1), 20) + (hit[i] ? 8 : 0)),
        symbol: chosen.map((s) => (rarity === 'Key' ? 'star' : s.points[0].slot === 'weapon' ? 'diamond' : 'circle')),
        line: { color: hit.map((h) => (h ? '#ff3355' : '#111')), width: hit.map((h) => (h ? 3 : 1.5)) }, opacity: 0.95 },
    })
  }
  const ring = (list: typeof spots, name: string, color: string, size: number) => list.length && traces.push({
    type: 'scatter', mode: 'markers', name, x: list.map((s) => xy(s)[0]), y: list.map((s) => xy(s)[1]), customdata: list.map((s) => [s.id]),
    hovertext: list.map((s) => hover(data, s.points, users)), hoverinfo: 'text', marker: { symbol: 'circle-open', size, color, line: { width: 3 } },
  })
  ring(spots.filter((s) => s.points.some((p) => wanted.has(p.key))), 'Party gear', data.partyColor, 28)
  if (f.missables || f.onlyMissables) ring(spots.filter((s) => s.points.some((p) => p.missable)), 'Missable', data.missableColor, 22)
  const layout: Record<string, unknown> = {
    margin: { l: 0, r: 0, t: 0, b: 0 }, dragmode: 'pan', uirevision: mapKey, font: { color: '#ddd' },
    hoverlabel: { align: 'left', bgcolor: 'rgba(20,20,24,0.95)', bordercolor: '#555', font: { color: '#eee', size: 12 } },
    legend: { orientation: 'h', y: 1, x: 0.01, bgcolor: 'rgba(0,0,0,0.55)' },
  }
  if (m.image) {
    Object.assign(layout, {
      images: [{ source: m.image, xref: 'x', yref: 'y', x: 0, y: 0, sizex: m.width, sizey: m.height, xanchor: 'left', yanchor: 'top', sizing: 'stretch', layer: 'below' }],
      xaxis: { range: [0, m.width], visible: false, constrain: 'domain' }, yaxis: { range: [m.height, 0], visible: false, scaleanchor: 'x' }, plot_bgcolor: '#000',
    })
  } else {
    Object.assign(layout, { plot_bgcolor: '#14151c', xaxis: { title: { text: 'Minimap X' }, gridcolor: '#333' }, yaxis: { title: { text: 'Minimap Y' }, scaleanchor: 'x', gridcolor: '#333' } })
  }
  if (!spots.length) Object.assign(layout, { annotations: [{ text: 'Nothing on this map matches the filters', showarrow: false, xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, font: { size: 16 } }] })
  return { data: traces, layout }
}
