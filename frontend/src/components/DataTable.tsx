import { ActionIcon, Checkbox, Group, Menu, Table, Text, TextInput } from '@mantine/core'
import { IconArrowDown, IconArrowUp, IconColumns, IconSearch } from '@tabler/icons-react'
import {
  flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable,
  type ColumnDef, type SortingState, type VisibilityState,
} from '@tanstack/react-table'
import { useMemo, useState } from 'react'
import type { Table as TableData, Value } from '../api'

type Row = Record<string, Value>

const format = (v: Value) => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : Array.isArray(v) ? v.join(', ') : String(v ?? ''))

// A sortable, filterable table with a column picker, from the backend's {columns, rows}
export function DataTable({ table }: { table: TableData }) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [filter, setFilter] = useState('')
  const [visibility, setVisibility] = useState<VisibilityState>({})
  const data = useMemo<Row[]>(() => table.rows.map((r) => Object.fromEntries(table.columns.map((c, i) => [c, r[i]]))), [table])
  const columns = useMemo<ColumnDef<Row>[]>(
    () => table.columns.map((c) => ({
      id: c, accessorFn: (row: Row) => row[c], header: c, cell: (info) => format(info.getValue() as Value),
      sortingFn: 'basic', sortUndefined: 'last',
    })),
    [table],
  )
  const model = useReactTable({
    data, columns, state: { sorting, globalFilter: filter, columnVisibility: visibility },
    onSortingChange: setSorting, onGlobalFilterChange: setFilter, onColumnVisibilityChange: setVisibility,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div>
      <Group justify="space-between" mb="xs" wrap="nowrap">
        {table.description ? <Text size="xs" c="dimmed">{table.description}</Text> : <span />}
        <Group gap={4} wrap="nowrap">
          <TextInput size="xs" placeholder="Filter" leftSection={<IconSearch size={14} />} value={filter} onChange={(e) => setFilter(e.currentTarget.value)} w={160} />
          <Menu closeOnItemClick={false} position="bottom-end">
            <Menu.Target>
              <ActionIcon variant="subtle" aria-label="Columns"><IconColumns size={16} /></ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              {model.getAllLeafColumns().map((column) => (
                <Menu.Item key={column.id}>
                  <Checkbox size="xs" label={column.id} checked={column.getIsVisible()} onChange={column.getToggleVisibilityHandler()} />
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
      <Table.ScrollContainer minWidth={400}>
        <Table striped highlightOnHover withTableBorder fz="xs" className="numeric">
          <Table.Thead>
            {model.getHeaderGroups().map((group) => (
              <Table.Tr key={group.id}>
                {group.headers.map((header) => (
                  <Table.Th key={header.id} className="sortable" onClick={header.column.getToggleSortingHandler()}>
                    <Group gap={2} wrap="nowrap">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && <IconArrowUp size={12} />}
                      {header.column.getIsSorted() === 'desc' && <IconArrowDown size={12} />}
                    </Group>
                  </Table.Th>
                ))}
              </Table.Tr>
            ))}
          </Table.Thead>
          <Table.Tbody>
            {model.getRowModel().rows.map((row) => (
              <Table.Tr key={row.id}>
                {row.getVisibleCells().map((cell) => <Table.Td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</Table.Td>)}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </div>
  )
}
