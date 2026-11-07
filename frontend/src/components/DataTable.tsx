import { ActionIcon, Checkbox, Group, Menu, Table, Text, TextInput } from '@mantine/core'
import { IconArrowDown, IconArrowUp, IconColumns, IconSearch } from '@tabler/icons-react'
import {
  flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable,
  type ColumnDef, type SortingState, type VisibilityState,
} from '@tanstack/react-table'
import { useMemo, useState, type CSSProperties, type ReactNode } from 'react'
import type { Table as TableData, Value } from '../api'
import { formatValue } from '../format'

interface SortTableProps<T> {
  data: T[]
  columns: ColumnDef<T, unknown>[]
  initialSorting?: SortingState
  hidden?: string[] // Columns hidden until picked
  toolbar?: ReactNode // Extra controls left of the filter
  description?: ReactNode
  onRowClick?: (row: T) => void
  rowStyle?: (row: T) => CSSProperties | undefined
  maxHeight?: number | string
  filterable?: boolean
}

// A sortable, filterable table with a column picker. Click a header to sort, type to filter every column
export function SortTable<T>({ data, columns, initialSorting = [], hidden = [], toolbar, description, onRowClick, rowStyle, maxHeight, filterable = true }: SortTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting)
  const [filter, setFilter] = useState('')
  const [visibility, setVisibility] = useState<VisibilityState>(Object.fromEntries(hidden.map((h) => [h, false])))
  // eslint-disable-next-line react-hooks/incompatible-library
  const model = useReactTable({
    data, columns, state: { sorting, globalFilter: filter, columnVisibility: visibility },
    onSortingChange: setSorting, onGlobalFilterChange: setFilter, onColumnVisibilityChange: setVisibility,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div>
      {(filterable || toolbar || description) && (
        <Group justify="space-between" mb="xs" wrap="wrap" gap="xs">
          {description ? <Text size="xs" c="dimmed" maw={600}>{description}</Text> : <span />}
          <Group gap={6} wrap="nowrap">
            {toolbar}
            {filterable && (
              <TextInput size="xs" placeholder="Filter rows" leftSection={<IconSearch size={14} />} value={filter} onChange={(e) => setFilter(e.currentTarget.value)} w={170} />
            )}
            <Menu closeOnItemClick={false} position="bottom-end">
              <Menu.Target>
                <ActionIcon variant="default" aria-label="Columns" size="md"><IconColumns size={16} /></ActionIcon>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Label>Columns</Menu.Label>
                {model.getAllLeafColumns().map((column) => (
                  <Menu.Item key={column.id}>
                    <Checkbox size="xs" label={String(column.columnDef.header ?? column.id)} checked={column.getIsVisible()} onChange={column.getToggleVisibilityHandler()} />
                  </Menu.Item>
                ))}
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Group>
      )}
      <Table.ScrollContainer minWidth={500} maxHeight={maxHeight}>
        <Table striped highlightOnHover stickyHeader fz="xs" className="numeric" verticalSpacing={6}>
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
              <Table.Tr key={row.id} onClick={onRowClick ? () => onRowClick(row.original) : undefined}
                style={{ cursor: onRowClick ? 'pointer' : undefined, ...rowStyle?.(row.original) }}>
                {row.getVisibleCells().map((cell) => <Table.Td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</Table.Td>)}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
      {model.getRowModel().rows.length === 0 && <Text size="sm" c="dimmed" ta="center" py="md">No rows match</Text>}
    </div>
  )
}

type Row = Record<string, Value>

// The backend's {columns, rows} tables
export function DataTable({ table, maxHeight }: { table: TableData; maxHeight?: number }) {
  const data = useMemo<Row[]>(() => table.rows.map((r) => Object.fromEntries(table.columns.map((c, i) => [c, r[i]]))), [table])
  const columns = useMemo<ColumnDef<Row, unknown>[]>(
    () => table.columns.map((c) => ({ id: c, accessorFn: (row: Row) => row[c], header: c, cell: (info) => formatValue(info.getValue() as Value), sortUndefined: 'last' })),
    [table],
  )
  return <SortTable data={data} columns={columns} description={table.description} maxHeight={maxHeight} />
}
