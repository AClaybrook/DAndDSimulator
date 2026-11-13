import { Button, List, Modal, Select, Stack, Text } from '@mantine/core'
import { IconUsersGroup } from '@tabler/icons-react'
import { useState } from 'react'
import type { PlannerOptions } from '../../api'
import { useParty } from '../../party'

// Saved parties: build doc builds with their gear changes, the trade-offs worked out for them as variants (Variants tab), and the takeaways
export function SavedParties({ options }: { options: PlannerOptions }) {
  const { setParty } = useParty()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState<string | null>(options.savedParties[0]?.name ?? null)
  const chosen = options.savedParties.find((p) => p.name === name)
  if (!options.savedParties.length) return null
  const load = () => {
    if (!chosen) return
    setParty(chosen.builds)
    setOpen(false)
  }
  return (
    <>
      <Button size="xs" variant="default" leftSection={<IconUsersGroup size={14} />} onClick={() => setOpen(true)}>Saved parties</Button>
      <Modal opened={open} onClose={() => setOpen(false)} title="Saved parties" size="lg">
        <Stack>
          <Select label="Party" value={name} onChange={setName} data={options.savedParties.map((p) => p.name)} />
          {chosen && (
            <>
              <Text size="sm" c="dimmed">
                {chosen.builds.length} builds: {chosen.builds.map((b) => b.name).join(', ')}. Each build's trade-offs are in its Variants tab
                ({chosen.builds.reduce((n, b) => n + b.variants.length, 0)} variants).
              </Text>
              <div>
                <Text className="section-label" mb={4}>Takeaways</Text>
                <List size="sm" spacing={4}>{chosen.notes.map((n) => <List.Item key={n}>{n}</List.Item>)}</List>
              </div>
            </>
          )}
          <Button onClick={load} disabled={!chosen}>Load this party (replaces the current one)</Button>
        </Stack>
      </Modal>
    </>
  )
}
