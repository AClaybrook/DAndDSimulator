import '@mantine/core/styles.css'
import './index.css'
import { MantineProvider, createTheme } from '@mantine/core'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

const theme = createTheme({ primaryColor: 'indigo', defaultRadius: 'md' })
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
