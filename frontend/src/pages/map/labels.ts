// Label placement for the item map
const POSITIONS = ['top center', 'bottom center', 'middle right', 'middle left'] as const

// Where each marker's name goes so names don't sit on each other or on a marker: above when free, else below, right or left of it.
// Sizes are in map units (unitsPerPx turns the 11px text into them); a name with no free place keeps "above"
export function placeLabels(items: { x: number; y: number; text: string; size: number }[], unitsPerPx: number, down = 1): string[] {
  type Box = [number, number, number, number]
  const overlap = (a: Box, b: Box) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]
  const taken: Box[] = items.map((p) => { const r = (p.size / 2) * unitsPerPx; return [p.x - r, p.y - r, p.x + r, p.y + r] })
  return items.map((p, index) => {
    if (!p.text) return POSITIONS[0]
    const w = p.text.length * 6.1 * unitsPerPx, h = 14 * unitsPerPx, r = (p.size / 2 + 3) * unitsPerPx
    const boxes: Box[] = [
      [p.x - w / 2, p.y - down * (r + h), p.x + w / 2, p.y - down * r], [p.x - w / 2, p.y + down * r, p.x + w / 2, p.y + down * (r + h)],
      [p.x + r, p.y - h / 2, p.x + r + w, p.y + h / 2], [p.x - r - w, p.y - h / 2, p.x - r, p.y + h / 2],
    ].map(([x0, y0, x1, y1]) => [Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1), Math.max(y0, y1)] as Box)
    const free = boxes.findIndex((box) => !taken.some((t, i) => i !== index && overlap(box, t)))
    const choice = free < 0 ? 0 : free
    taken.push(boxes[choice])
    return POSITIONS[choice]
  })
}
