import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ThemeProvider } from './components/theme-provider'
import { Toaster } from './components/ui/toaster'
import { IntlayerProviderWrapper } from './providers'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <IntlayerProviderWrapper>
      <BrowserRouter>
        <ThemeProvider defaultTheme="dark" storageKey="truthound-theme">
          <App />
          <Toaster />
        </ThemeProvider>
      </BrowserRouter>
    </IntlayerProviderWrapper>
  </React.StrictMode>
)
