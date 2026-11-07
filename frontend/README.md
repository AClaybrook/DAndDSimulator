# Front end

React + TypeScript + Vite, with Mantine (components), TanStack Query (API calls) and Table (sortable tables), Plotly.js (the backend's
figures) and Zustand (state kept in the browser). The backend is the FastAPI app in `api/`.

```bash
npm install
npm run dev     # http://localhost:5173, with /api forwarded to the backend: run `uv run python -m api` from the repository root
npm run build   # type check and build into dist/, which the backend serves at http://localhost:8000
npm run lint
```
