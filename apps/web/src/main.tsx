import React from 'react'
import { createRoot } from 'react-dom/client'
import PilotApp from './PilotApp'
createRoot(document.getElementById('root')!).render(<PilotApp />)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
