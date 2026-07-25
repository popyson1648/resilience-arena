import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { IntlProvider, createTheme } from 'smarthr-ui'
import { ThemeProvider } from 'styled-components'
import 'smarthr-ui/smarthr-ui.css'

import { App } from './App'

const theme = createTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <IntlProvider locale="ja">
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    </IntlProvider>
  </StrictMode>,
)
