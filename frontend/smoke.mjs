// Smoke test: every page loads and its main controls work in a real browser, without page errors or failed API calls.
// Needs the app running: `uv run python -m api` (from the repository root), then `npm run smoke` (SMOKE_URL to point elsewhere)
import { chromium } from 'playwright'

const base = process.env.SMOKE_URL ?? 'http://localhost:8000'
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } })
const problems = []
page.on('pageerror', (e) => problems.push(`page error: ${e.message}`))
page.on('console', (m) => m.type() === 'error' && problems.push(`console: ${m.text()}`))
page.on('response', (r) => r.url().includes('/api/') && r.status() >= 400 && problems.push(`${r.status()} ${r.url()}`))

async function step(name, action) {
  const before = problems.length
  try {
    await action()
    console.log(`${problems.length > before ? 'FAIL' : 'ok  '} ${name}`)
  } catch (e) {
    problems.push(`${name}: ${e.message.split('\n')[0]}`)
    console.log(`FAIL ${name}`)
  }
}
const visible = (locator) => locator.first().waitFor({ state: 'visible', timeout: 30000 })

await step('Party planner: example party and its damage', async () => {
  await page.goto(`${base}/#/planner`)
  await visible(page.getByText("Lae'zel", { exact: false }))
  await visible(page.getByRole('tab', { name: 'Gear' }))
})
await step('Planner: buffs grid changes the damage', async () => {
  const before = await page.locator('.numeric').first().innerText()
  await page.getByRole('tab', { name: 'Buffs', exact: true }).click()
  await page.getByRole('checkbox', { name: 'Haste, Act 1' }).check()
  await page.waitForFunction((was) => document.querySelector('.numeric')?.textContent !== was, before, { timeout: 15000 })
  await page.getByRole('checkbox', { name: 'Haste, Act 1' }).uncheck()
  await page.getByRole('tab', { name: 'Gear', exact: true }).click()
})
await step('Planner: send the party to the simulator', async () => {
  await page.getByRole('button', { name: 'To simulator' }).click()
  await page.getByRole('menuitem', { name: /Whole party at/ }).first().click()
  await page.waitForURL(/#\/simulator/)
})
await step('Simulator: results and a table tab', async () => {
  await visible(page.getByText('damage per round'))
  await page.getByRole('tab', { name: 'Attack breakdown' }).click()
  await visible(page.getByRole('button', { name: 'Download CSV' }))
})
await step('Simulator: edit a character beside the results', async () => {
  await page.getByRole('tab', { name: 'Chart' }).click()
  await page.getByRole('button', { name: 'Edit' }).first().click()
  await page.getByRole('tab', { name: /Attacks/ }).click()
  await visible(page.getByText('Crit on'))
  await visible(page.getByText('damage per round')) // The results stay in view while editing
  await page.getByRole('button', { name: 'Characters' }).click()
  await visible(page.getByRole('button', { name: 'Add' }))
})
await step('Leaderboard: rankings, filters kept in the URL', async () => {
  await page.keyboard.press('2')
  await visible(page.getByRole('button', { name: 'Download CSV' }))
  await page.getByText('3 (AoE)', { exact: true }).click()
  if (!page.url().includes('enemies=3')) throw new Error(`filters not in the URL: ${page.url()}`)
})
await step('Item map: Act 1 and Act 2', async () => {
  await page.keyboard.press('3')
  await visible(page.getByText('Wilderness', { exact: true }))
  await page.getByText('Act 2', { exact: true }).click()
  await visible(page.getByText('Shadow-Cursed Lands', { exact: true }))
})
await step('Light theme', async () => {
  await page.keyboard.press('t')
  const scheme = await page.evaluate(() => document.documentElement.getAttribute('data-mantine-color-scheme'))
  if (scheme !== 'light') throw new Error(`theme is ${scheme}`)
})

await browser.close()
if (problems.length) {
  console.error(`\n${problems.length} problem(s):\n${problems.join('\n')}`)
  process.exit(1)
}
