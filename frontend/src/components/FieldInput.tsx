import { NumberInput, Select, SimpleGrid, Switch, TextInput } from '@mantine/core'
import type { Value } from '../api'
import { STATS, type Field, type FieldGroup } from '../fields'

interface Props {
  field: Field
  value: Value | undefined
  onChange: (value: Value) => void
}

export function FieldInput({ field, value, onChange }: Props) {
  const common = { label: field.label, description: field.help, size: 'xs' as const }
  switch (field.kind) {
    case 'bool':
      return <Switch {...common} description={undefined} title={field.help} checked={Boolean(value)} onChange={(e) => onChange(e.currentTarget.checked)} mt="xs" />
    case 'int':
    case 'float':
      return (
        <NumberInput {...common} value={value === null || value === undefined ? '' : Number(value)} min={field.min} max={field.max}
          allowDecimal={field.kind === 'float'} step={field.kind === 'float' ? 0.5 : 1}
          onChange={(v) => onChange(v === '' ? null : Number(v))} />
      )
    case 'stat':
      return <Select {...common} data={STATS.map((s) => ({ value: s, label: s[0].toUpperCase() + s.slice(1) }))} value={String(value ?? '')}
        onChange={(v) => v && onChange(v)} allowDeselect={false} />
    case 'select':
      return <Select {...common} data={field.options ?? []} value={String(value ?? '')} onChange={(v) => v && onChange(v)} allowDeselect={false} searchable />
    case 'list':
      return (
        <TextInput {...common} defaultValue={Array.isArray(value) ? value.join(', ') : ''}
          onBlur={(e) => onChange(e.currentTarget.value.split(',').map((x) => x.trim()).filter(Boolean))} />
      )
    default:
      return <TextInput {...common} value={String(value ?? '')} onChange={(e) => onChange(e.currentTarget.value)} />
  }
}

// Groups of fields, each under a small heading, all visible: no folding to open
export function FieldGroups({ groups, values, onChange, columns = 2 }: {
  groups: FieldGroup[]; values: Record<string, unknown>; onChange: (key: string, value: Value) => void; columns?: number
}) {
  return (
    <>
      {groups.map((group) => (
        <div key={group.title} style={{ marginBottom: 14 }}>
          <div className="section-label" style={{ marginBottom: 4 }}>{group.title}</div>
          <SimpleGrid cols={{ base: 1, sm: columns }} spacing="xs" verticalSpacing={4}>
            {group.fields.map((field) => (
              <FieldInput key={field.key} field={field} value={values[field.key] as Value} onChange={(v) => onChange(field.key, v)} />
            ))}
          </SimpleGrid>
        </div>
      ))}
    </>
  )
}
