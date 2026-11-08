import React, { useState } from 'react'

type Parcel = { id: string; crop: string; soil_water_mm: number; health: number; pending_kg: number }

export default function App() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [info, setInfo] = useState<any>(null)
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

  return (
    <main style={{ fontFamily: 'system-ui', padding: 16, maxWidth: 560, margin: '0 auto' }}>
      <h1>TecRural · juego</h1>
      <p style={{ background: '#fff3cd', padding: 8 }}>Juego/experimental. No es recomendación real. Profesional desactivado.</p>
      <button onClick={newGame} style={{ padding: 12, fontSize: 18 }}>Nueva finca Costa Tropical</button>{' '}
      <button onClick={advance} disabled={!gameId} style={{ padding: 12, fontSize: 18 }}>Avanzar 1 día</button>
      {info && (
        <section>
          <h2>Caja: {info.cash_eur} € · Agua: {info.reservoir_m3} m³ · Día: {info.day}</h2>
          <div style={{ display: 'grid', gap: 8 }}>
            {(info.parcels as Parcel[]).map(p => (
              <div key={p.id} style={{ border: '1px solid #1a6b3c', borderRadius: 8, padding: 8 }}>
                <b>{p.id} · {p.crop}</b><br />
                Humedad estimada: {p.soil_water_mm} mm · Sanidad juego: {p.health} · Fruta: {p.pending_kg} kg
              </div>
            ))}
          </div>
          {info.prov && <pre style={{ fontSize: 12 }}>{JSON.stringify(info.prov, null, 2)}</pre>}
        </section>
      )}
    </main>
  )
}
