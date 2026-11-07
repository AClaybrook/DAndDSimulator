# Working on this repository

## UI preferences (the owner's, for every app and page)

- **Progressive disclosure.** Lead with a high level summary: the main takeaways, visually, up front (charts, a few headline numbers). Details sit one
  level down and open on demand: collapsible sections, tabs, drawers, tooltips and "?" popovers instead of paragraphs. Think of an expanding hierarchy
  you drill into, not a wall of controls and text.
- **Graphs over text.** Plots are the main way to read results; numbers go in tooltips and tables. Some text is fine, walls of it aren't.
- **One home per concept.** A number (damage, AC, score) is shown in one place, not repeated across sections.
- **Real tables.** Sortable, filterable, with a column picker, instead of static HTML tables.
- **Fast.** Edits should feel instant: state lives in the browser, the server is only called to compute.

## Layout

- `computations/` damage engine (analytic, exact distributions, simulation), `game_data/` D&D data, `bg3/` Baldur's Gate 3 builds, items, map,
  leaderboard and the local database (`local_data/bg3.sqlite`, personal data, gitignore it before making the repository public).
- `api/` FastAPI backend over the engine, `frontend/` React + TypeScript + Vite app (Mantine, TanStack Table and Query, Plotly.js).
- `app.py` + `components/` is the original Dash app, kept until the new front end matches it.

## Checks

- `uv run ruff check .` and `uv run pytest` (CI runs both, plus `uv run python -m benchmarks.benchmark`).
- Front end: `cd frontend && npm run build` (type checks) and `npm run lint` when present.
