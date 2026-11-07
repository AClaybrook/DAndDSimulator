import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `npm run dev` serves the app on 5173 and forwards /api to the FastAPI backend (uv run python -m api)
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { chunkSizeWarningLimit: 5000 },
})
