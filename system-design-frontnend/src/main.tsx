import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import AppWithRouter from './Router.tsx'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppWithRouter />
  </StrictMode>,
)
