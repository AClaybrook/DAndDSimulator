import '@mantine/core/styles.css'
import './index.css'
import { MantineProvider, createTheme, type MantineColorsTuple } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// A violet accent on a neutral, slightly cool dark palette
const violet: MantineColorsTuple = ['#f3efff', '#e2dbfb', '#c2b3f3', '#a088ec', '#8464e6', '#734de3', '#6a41e2', '#5933c9', '#4e2db4', '#42259f']
const dark: MantineColorsTuple = ['#d5d7e0', '#acaebf', '#8c8fa3', '#666980', '#4d4f66', '#34354a', '#2a2b3d', '#1f202e', '#16171f', '#101118']

const theme = createTheme({
  primaryColor: 'violet',
  colors: { violet, dark },
  defaultRadius: 'md',
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  headings: { fontWeight: '650' },
  components: {
    Paper: { defaultProps: { radius: 'lg' } },
    Tooltip: { defaultProps: { withArrow: true, openDelay: 200 } },
  },
})
const queries = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } } })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="dark">
      <QueryClientProvider client={queries}>
        <App />
      </QueryClientProvider>
    </MantineProvider>
  </StrictMode>,
)
