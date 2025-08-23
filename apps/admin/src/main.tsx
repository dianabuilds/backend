import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// Ensure TS picks up our type augmentations (custom DOM attributes like onCommit)
import './types/react-augment.d.ts'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
