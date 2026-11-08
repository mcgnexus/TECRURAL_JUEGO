import React, { useState } from 'react'
import IsoMap from './IsoMap'

type Parcel = { id: string; crop: string; soil_water_mm: number; health: number; pending_kg: number }

const VARIEDAD: Record<string, { v: string; edad: number }> = {
  P1: { v: 'Hass', edad: 6 }, P2: { v: 'Osteen', edad: 8 }, P3: { v: 'Fino de Jete', edad: 10 },
}

export default function App() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [info, setInfo] = useState<any>(null)
  const [sel, setSel] = useState<string | null>('P1')
  const [api] = useState('http://localhost:8000')

  async function newGame() {
    const r = await fetch(`${api}/games`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    const j = await r.json()
    setGameId(j.game_id)
    await refresh(j.game_id)
  }
  async function refresh(gid: string) {
    const r = await fetch(`${api}/games/${gid}`)
    setInfo(await r.json())
  }
  async function advance() {
    if (!gameId) return
    const r = await fetch(`${api}/games/${gameId}/advance`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actions: [{ parcel_id: 'P1', irrigation_mm: 4 }], precip_mm: 2, et0_mm: 3.5, kind: 'simulado' }) })
    const j = await r.json()
    setInfo({ cash_eur: j.indicators.cash_eur, reservoir_m3: j.indicators.reservoir_m3, day: j.state.day,
      parcels: j.state.parcels.map((p: any) => ({ id: p.id, crop: p.crop, soil_water_mm: p.soil_water_mm, health: p.health_0_1, pending_kg: p.pending_fruit_kg })),
      lastEvents: j.events, prov: j.provenance })
  }

  const parcels: Parcel[] = info?.parcels || [
    { id: 'P1', crop: 'aguacate', soil_water_mm: 45, health: 0.9, pending_kg: 500 },
    { id: 'P2', crop: 'mango', soil_water_mm: 40, health: 0.9, pending_kg: 500 },
    { id: 'P3', crop: 'chirimoyo', soil_water_mm: 38, health: 0.9, pending_kg: 500 },
  ]
  const cur = parcels.find(p => p.id === sel) || parcels[0]

  return (
    <main style={{ fontFamily: 'system-ui', padding: 12, maxWidth: 560, margin: '0 auto' }}>
      <h1 style={{ fontSize: 22 }}>TecRural · juego</h1>
      <p style={{ background: '#fff3cd', padding: 8, fontSize: 15 }}>Juego/experimental. No es recomendación real. Profesional desactivado.</p>
      <IsoMap parcels={parcels.map(p => ({ ...p, variety: '', edad: 0, soil: p.soil_water_mm }))} selected={sel} onSelect={setSel} />
      <section aria-label="Panel de parcela" style={{ border: '2px solid #1a6b3c', borderRadius: 12, padding: 12, marginTop: 8 }}>
        <b style={{ fontSize: 18 }}>{cur.id} · {cur.crop} · {VARIEDAD[cur.id]?.v} · {VARIEDAD[cur.id]?.edad} años (juego)</b><br />
        <span style={{ fontSize: 16 }}>Humedad estimada: {cur.soil_water_mm} mm (no medida)</span><br />
        <span style={{ fontSize: 16 }}>Sanidad juego: {cur.health} · Fruta: {cur.pending_kg} kg</span><br />
        <span style={{ fontSize: 13, color: '#555' }}>Clima/suelo/tareas/costes: ver panel principal al conectar API. Calidad de dato: simulado.</span>
      </section>
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button onClick={newGame} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Nueva finca</button>
        <button onClick={advance} disabled={!gameId} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Avanzar 1 día</button>
      </div>
      {info && (
        <section>
          <h2 style={{ fontSize: 18 }}>Caja: {info.cash_eur} € · Agua: {info.reservoir_m3} m³ · Día: {info.day}</h2>
          {info.prov && <pre style={{ fontSize: 12 }}>{JSON.stringify(info.prov, null, 2)}</pre>}
        </section>
      )}
    </main>
  )
}
