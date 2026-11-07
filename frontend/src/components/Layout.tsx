// Building blocks every page uses, so pages look alike: a header with actions, headline numbers, titled cards
import { Group, Paper, Stack, Text, Title, Tooltip } from '@mantine/core'
import type { ReactNode } from 'react'

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <Group justify="space-between" align="flex-end" mb="md" wrap="wrap" gap="sm">
      <div>
        <Title order={2} fw={650}>{title}</Title>
        {subtitle && <Text size="sm" c="dimmed" mt={2}>{subtitle}</Text>}
      </div>
      {actions && <Group gap="xs" wrap="wrap">{actions}</Group>}
    </Group>
  )
}

// A headline number with its label, the first thing to read on a page
export function Stat({ label, value, detail, color, help }: { label: string; value: ReactNode; detail?: ReactNode; color?: string; help?: string }) {
  const body = (
    <Paper p="sm" withBorder style={{ borderTop: color ? `3px solid ${color}` : undefined, height: '100%' }}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600} lts={0.4}>{label}</Text>
      <Text fz={26} fw={700} className="numeric" lh={1.2} mt={2}>{value}</Text>
      {detail && <Text size="xs" c="dimmed" mt={2} lineClamp={2}>{detail}</Text>}
    </Paper>
  )
  return help ? <Tooltip label={help} multiline w={280}>{body}</Tooltip> : body
}

// A titled card; actions sit on the right of the title
export function Section({ title, actions, children, padding = 'md' }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; padding?: string }) {
  return (
    <Paper p={padding} withBorder>
      <Stack gap="sm">
        {(title || actions) && (
          <Group justify="space-between" wrap="nowrap" gap="xs">
            {typeof title === 'string' ? <Text fw={600}>{title}</Text> : title}
            {actions && <Group gap={6} wrap="nowrap">{actions}</Group>}
          </Group>
        )}
        {children}
      </Stack>
    </Paper>
  )
}

// Plotly layout for charts drawn in the browser, matching the dark theme of the backend's figures
export function chartLayout(extra: Record<string, unknown> = {}): Record<string, unknown> {
  const axis = { gridcolor: 'rgba(255,255,255,0.08)', zerolinecolor: 'rgba(255,255,255,0.15)', linecolor: 'rgba(255,255,255,0.2)' }
  return {
    font: { color: '#C9C9C9', family: 'inherit', size: 12 },
    hoverlabel: { bgcolor: '#25262b', bordercolor: '#444', font: { color: '#eee' } },
    legend: { orientation: 'h', y: -0.18 },
    ...extra,
    xaxis: { ...axis, ...(extra.xaxis as object) },
    yaxis: { ...axis, ...(extra.yaxis as object) },
  }
}
