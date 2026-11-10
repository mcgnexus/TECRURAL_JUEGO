import React, { useEffect, useState } from 'react'
import IsoMap from './IsoMap'

type Parcel = { id: string; crop: string; area_ha: number; soil_water_mm: number; health: number; pending_kg: number; inventory_kg?: number; phenology?: string; cum_n_kg?: number }

const VARIEDAD: Record<string, { v: string; edad: number }> = {
  P1: { v: 'Hass', edad: 6 }, P2: { v: 'Osteen', edad: 8 }, P3: { v: 'Fino de Jete', edad: 10 },
}
// URL configurable en despliegue; por defecto local. Nunca promete persistencia.
const API = ((import.meta as any).env?.VITE_API_URL as string) || 'http://localhost:8000'
const LS_KEY = 'tecrural-fase1'
const TOK_KEY = 'tecrural-token'

type Acts = Record<string, { mm: string; harvest: boolean; sell: string; channel: string; prune: boolean; scout: boolean; fert: boolean; fertId: string; fertKg: string; spray: string }>

const defaultActs = (): Acts => ({
  P1: { mm: '4', harvest: false, sell: '', channel: 'base', prune: false, scout: false, fert: false, fertId: '', fertKg: '', spray: '' },
  P2: { mm: '0', harvest: false, sell: '', channel: 'base', prune: false, scout: false, fert: false, fertId: '', fertKg: '', spray: '' },
  P3: { mm: '0', harvest: false, sell: '', channel: 'base', prune: false, scout: false, fert: false, fertId: '', fertKg: '', spray: '' },
})

function authHeaders(): Record<string, string> {
  try {
    const t = localStorage.getItem(TOK_KEY)
    return t ? { Authorization: `Bearer ${t}` } : {}
  } catch { return {} }
}

export default function App() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [info, setInfo] = useState<any>(() => {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || 'null') } catch { return null }
  })
  const [sel, setSel] = useState('P1')
  const [acts, setActs] = useState<Acts>(defaultActs())
  const [areas, setAreas] = useState<Record<string, string>>({ P1: '1', P2: '0.8', P3: '0.6' })
  const [msg, setMsg] = useState<string | null>(null)
  const [hist, setHist] = useState<any[]>([])
  const [online, setOnline] = useState(navigator.onLine)
  const [tut, setTut] = useState(() => !localStorage.getItem('tecrural-tut'))
  const [phone, setPhone] = useState('+34600000000')
  const [code, setCode] = useState('')
  const [me, setMe] = useState<any>(null)
  const [forecast, setForecast] = useState<any>(null)
  const [versions, setVersions] = useState<any[]>([])
  const [sys, setSys] = useState<any>(null)

  useEffect(() => {
    const f = () => setOnline(navigator.onLine)
    window.addEventListener('online', f); window.addEventListener('offline', f)
    return () => { window.removeEventListener('online', f); window.removeEventListener('offline', f) }
  }, [])
  useEffect(() => { try { localStorage.setItem(LS_KEY, JSON.stringify(info)) } catch {} }, [info])

  async function api(path: string, opts?: RequestInit) {
    if (!navigator.onLine) throw new Error('offline')
    const r = await fetch(`${API}${path}`, opts)
    if (!r.ok) { const t = await r.text(); throw new Error(`${r.status}: ${t.slice(0, 200)}`) }
    return r.json()
  }
  const H = () => ({ 'Content-Type': 'application/json', ...authHeaders() })

  async function newGame() {
    try {
      const j = await api('/games', { method: 'POST', headers: H(), body: JSON.stringify({}) })
      setGameId(j.game_id)
      setMsg(j.ephemeral ? 'Partida efímera sin cuenta (temporal, puede perderse).' : 'Partida vinculada a tu cuenta de ensayo (sin garantía de persistencia).')
      await refresh(j.game_id)
    } catch { setMsg('Sin conexión: no se puede crear partida. No se inventan datos sin servidor.') }
  }
  async function refresh(gid: string) {
    const j = await api(`/games/${gid}`, { headers: authHeaders() })
    setInfo(j)
    try { setAreas(Object.fromEntries(j.parcels.map((p: Parcel) => [p.id, String(p.area_ha ?? '')]))) } catch {}
    try { const h = await api(`/games/${gid}/history`, { headers: authHeaders() }); setHist(h.history || []) } catch {}
    try { const v = await api(`/games/${gid}/versions`, { headers: authHeaders() }); setVersions(v.versions || []) } catch { setVersions([]) }
  }
  function payload() {
    return {
      actions: Object.entries(acts).map(([parcel_id, a]) => ({
        parcel_id,
        irrigation_mm: Math.max(0, Math.min(100, parseFloat(a.mm) || 0)),
        harvest: a.harvest,
        sell_kg: a.sell === '' ? (a.harvest ? undefined : undefined) : Math.max(0, parseFloat(a.sell) || 0),
        channel: a.channel || 'base',
        prune: a.prune, scout: a.scout, fertilize_abstract: a.fert,
        fertilizer_id: a.fertId || undefined, fertilizer_kg: Math.max(0, parseFloat(a.fertKg) || 0),
        spray_id: a.spray || undefined,
      })),
      precip_mm: 2, et0_mm: 3.5, kind: 'simulado',
    }
  }
  async function advance(week: boolean) {
    if (!gameId) return
    setMsg(null)
    try {
      const j = await api(`/games/${gameId}${week ? '/advance_week' : '/advance'}`,
        { method: 'POST', headers: H(), body: JSON.stringify(payload()) })
      afterAdvance(j)
    } catch (e: any) { setMsg(`No se pudo avanzar: ${e.message || e}. Sin conexión el juego no finge datos.`) }
  }
  async function advanceWeather() {
    if (!gameId) return
    setMsg('Consultando clima de Motril (AEMET/Open-Meteo)…')
    try {
      const j = await api(`/games/${gameId}/advance_weather`,
        { method: 'POST', headers: H(), body: JSON.stringify({ actions: payload().actions, provider: 'auto', days: 1 }) })
      afterAdvance(j, `Clima: ${j.weather_snapshot?.serie_kind || ''} ${(j.weather_snapshot?.dias || []).join(',')} · estación Motril 18140 (≠ microclima).`)
    } catch (e: any) { setMsg(`Clima no disponible: ${e.message || e}. Prueba con avance simulado.`) }
  }
  function afterAdvance(j: any, extra?: string) {
    setInfo({ cash_eur: j.indicators.cash_eur, reservoir_m3: j.indicators.reservoir_m3, day: j.state.day,
      debt_eur: j.indicators.debt_eur, energy_kwh: j.indicators.energy_kwh, inflow_m3: j.indicators.inflow_m3,
      inventory_kg: j.indicators.inventory_kg,
      parcels: j.state.parcels.map((p: any) => ({ id: p.id, crop: p.crop, area_ha: p.area_ha, soil_water_mm: p.soil_water_mm, health: p.health_0_1, pending_kg: p.pending_fruit_kg, inventory_kg: p.inventory_kg, phenology: p.phenology, cum_n_kg: p.cum_n_kg })),
      prov: j.provenance, forecast: j.forecast, ledger: j.water_ledger })
    if (gameId) api(`/games/${gameId}/history`, { headers: authHeaders() }).then(h => setHist(h.history || [])).catch(() => {})
    if (extra) setMsg(extra)
  }
  async function saveAreas() {
    if (!gameId) return
    const parcels: Record<string, { area_ha: number }> = {}
    for (const [k, v] of Object.entries(areas)) {
      const n = parseFloat(v)
      if (!(n >= 0.1 && n <= 10)) { setMsg(`Superficie ${k} fuera de rango 0.1–10 ha (restricción de interfaz, juego).`); return }
      parcels[k] = { area_ha: n }
    }
    try { const j = await api(`/games/${gameId}`, { method: 'PUT', headers: H(), body: JSON.stringify({ parcels }) }); setInfo(j); setMsg('Finca guardada (juego).') }
    catch (e: any) { setMsg(`No se pudo guardar: ${e.message || e}`) }
  }
  async function restart() {
    if (!gameId) return
    const j = await api(`/games/${gameId}/restart`, { method: 'POST', headers: authHeaders() })
    setInfo(j); setHist([]); setForecast(null); setMsg('Partida reiniciada a finca inicial (juego).')
  }
  async function loadForecast() {
    if (!gameId) return
    try { const j = await api(`/games/${gameId}/forecast`, { headers: authHeaders() }); setForecast(j); setMsg('Previsión de juego por intervalos (orientativa, sin calibrar).') }
    catch (e: any) { setMsg(`Sin previsión: ${e.message || e}`) }
  }
  async function requestCode() {
    try {
      const j = await api('/accounts/request_code', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone }) })
      setMsg(j.code_debug ? `Código de ensayo (solo desarrollo): ${j.code_debug}. Caduca en 10 min.` : 'Código enviado (simulado).')
    } catch (e: any) { setMsg(`No se pudo pedir código: ${e.message || e}`) }
  }
  async function verifyCode() {
    try {
      const j = await api('/accounts/verify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone, code }) })
      try { localStorage.setItem(TOK_KEY, j.token) } catch {}
      setMsg('Cuenta verificada (ensayo, SMS simulado). Sesión 24 h.')
      await loadMe()
    } catch (e: any) { setMsg(`Código incorrecto o caducado: ${e.message || e}`) }
  }
  async function loadMe() {
    try { setMe(await api('/accounts/me', { headers: authHeaders() })) }
    catch (e: any) { setMsg(`Sin sesión válida: ${e.message || e}`) }
  }
  async function saveVersion() {
    if (!gameId) return
    try { const j = await api(`/games/${gameId}/save`, { method: 'POST', headers: authHeaders() }); setMsg(`Versión ${j.v} guardada (ensayo, sin garantía).`); await refresh(gameId) }
    catch (e: any) { setMsg(`No se pudo versionar (efímera o sin sesión): ${e.message || e}`) }
  }
  async function loadSys() {
    try {
      const [priv, prof, mon, chk] = await Promise.all([
        api('/privacy'), api('/professional/status'),
        api('/monitoring/health').catch(() => null),
        api('/launch/checklist').catch(() => null),
      ])
      setSys({ priv, prof, mon, chk })
    } catch (e: any) { setMsg(`Sistema no disponible: ${e.message || e}`) }
  }

  const parcels: Parcel[] = info?.parcels || [
    { id: 'P1', crop: 'aguacate', area_ha: 1, soil_water_mm: 45, health: 0.9, pending_kg: 500 },
    { id: 'P2', crop: 'mango', area_ha: 0.8, soil_water_mm: 40, health: 0.9, pending_kg: 500 },
    { id: 'P3', crop: 'chirimoyo', area_ha: 0.6, soil_water_mm: 38, health: 0.9, pending_kg: 500 },
  ]
  const cur = parcels.find(p => p.id === sel) || parcels[0]
  const setA = (id: string, patch: Partial<Acts[string]>) => setActs(a => ({ ...a, [id]: { ...a[id], ...patch } }))

  return (
    <main style={{ fontFamily: 'system-ui', padding: 12, maxWidth: 560, margin: '0 auto' }}>
      <a href="#panel" style={{ position: 'absolute', left: -9999 }} onFocus={e => (e.target as HTMLElement).style.left = '8px'} onBlur={e => (e.target as HTMLElement).style.left = '-9999px'}>Saltar al panel de parcela</a>
      <h1 style={{ fontSize: 22 }}>TecRural · juego</h1>
      {!online && <p role="alert" style={{ background: '#f8d7da', padding: 8 }}>Sin conexión: no se puede avanzar ni guardar. El juego no finge datos sin servidor.</p>}
      <p style={{ background: '#fff3cd', padding: 8, fontSize: 14 }}>Juego/experimental. Humedad <b>estimada, no medida</b>. Precios y costes de <b>juego</b>. Profesional desactivado. Entorno de ensayo: registro SMS simulado y guardado sin garantía. <span style={{ color: '#555' }}>Fuentes: motor {info?.prov?.model_version || 'sim-0.3.0'} · {info?.prov?.parameter_set || 'game-0.3'} · clima: {info?.prov?.weather_kind || 'simulado'}.</span></p>
      {tut && (
        <section aria-label="Tutorial" style={{ border: '2px dashed #1a6b3c', borderRadius: 12, padding: 12 }}>
          <b>Tutorial (30 s):</b>
          <ol style={{ fontSize: 15 }}>
            <li>Toca una parcela del mapa o elígela en el desplegable.</li>
            <li>Ajusta riego y marca tareas; guarda superficies si las cambias.</li>
            <li>Avanza 1 día o 1 semana y lee el historial: explica efectos y costes.</li>
          </ol>
          <button onClick={() => { localStorage.setItem('tecrural-tut', '1'); setTut(false) }} style={{ minHeight: 48, fontSize: 16 }}>Entendido</button>
        </section>
      )}
      <section aria-label="Cuenta de ensayo" style={{ border: '1px solid #999', borderRadius: 12, padding: 12, marginTop: 8 }}>
        <b>Cuenta (ensayo, SMS simulado)</b>
        <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
          <label>Teléfono E.164:
            <input value={phone} onChange={e => setPhone(e.target.value)} inputMode="tel" aria-label="Teléfono E.164" style={{ fontSize: 16, minHeight: 44, width: 170, marginLeft: 6 }} />
          </label>
          <label>Código:
            <input value={code} onChange={e => setCode(e.target.value)} inputMode="numeric" aria-label="Código de verificación" style={{ fontSize: 16, minHeight: 44, width: 110, marginLeft: 6 }} />
          </label>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <button onClick={requestCode} style={{ flex: 1, minHeight: 48 }}>Pedir código</button>
          <button onClick={verifyCode} style={{ flex: 1, minHeight: 48 }}>Verificar</button>
          <button onClick={loadMe} style={{ flex: 1, minHeight: 48 }}>Mi cuenta</button>
        </div>
        {me && <p style={{ fontSize: 14 }}>Cuenta {me.id} · {me.phone} · verificada: {String(me.verified)} · publicidad: {String(me.marketing_consent)}</p>}
      </section>
      <label style={{ fontSize: 15 }}>Parcela (teclado y lector de pantalla):
        <select value={sel} onChange={e => setSel(e.target.value)} aria-label="Elegir parcela" style={{ fontSize: 16, minHeight: 48, marginLeft: 8 }}>
          {parcels.map(p => <option key={p.id} value={p.id}>{p.id} · {p.crop}</option>)}
        </select>
      </label>
      <IsoMap parcels={parcels.map(p => ({ ...p, soil: p.soil_water_mm, health: p.health }))} selected={sel} onSelect={setSel} />
      <section id="panel" aria-label="Panel de parcela" tabIndex={-1} style={{ border: '2px solid #1a6b3c', borderRadius: 12, padding: 12, marginTop: 8 }}>
        <b style={{ fontSize: 18 }}>{cur.id} · {cur.crop} · {VARIEDAD[cur.id]?.v} · {VARIEDAD[cur.id]?.edad} años (juego)</b><br />
        <span style={{ fontSize: 16 }}>Humedad estimada: {cur.soil_water_mm} mm (no medida) · Sanidad juego: {cur.health} · Fruta: {cur.pending_kg} kg · Inventario: {cur.inventory_kg ?? 0} kg · {cur.phenology || ''}</span><br />
        <label>Superficie ha (0.1–10, restricción interfaz):
          <input value={areas[cur.id] || ''} onChange={e => setAreas({ ...areas, [cur.id]: e.target.value })} inputMode="decimal" aria-label={`Superficie ${cur.id}`} style={{ fontSize: 16, minHeight: 44, width: 90, marginLeft: 6 }} />
        </label>
        <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
          <label>Riego mm (0–100):
            <input value={acts[cur.id]?.mm || '0'} onChange={e => setA(cur.id, { mm: e.target.value })} inputMode="decimal" aria-label={`Riego ${cur.id}`} style={{ fontSize: 16, minHeight: 44, width: 90, marginLeft: 6 }} />
          </label>
          <label>Vender kg (de inventario, 0 = guardar):
            <input value={acts[cur.id]?.sell ?? ''} onChange={e => setA(cur.id, { sell: e.target.value })} inputMode="decimal" aria-label={`Vender kg ${cur.id}`} placeholder="vacío = auto" style={{ fontSize: 16, minHeight: 44, width: 110, marginLeft: 6 }} />
          </label>
          <label>Canal:
            <select value={acts[cur.id]?.channel || 'base'} onChange={e => setA(cur.id, { channel: e.target.value })} aria-label={`Canal ${cur.id}`} style={{ fontSize: 16, minHeight: 44, marginLeft: 6 }}>
              <option value="base">base</option><option value="cooperativa">cooperativa</option><option value="mercado">mercado</option>
            </select>
          </label>
          {[['harvest', 'Cosechar a inventario (precio juego al vender)'], ['prune', 'Poda (coste abstracto juego)'], ['scout', 'Vigilancia (no diagnostica)'], ['fert', 'Abono abstracto (sin dosis real)']].map(([k, label]) => (
            <label key={k} style={{ fontSize: 16 }}>
              <input type="checkbox" checked={(acts[cur.id] as any)?.[k] || false} onChange={e => setA(cur.id, { [k]: e.target.checked } as any)} style={{ width: 24, height: 24 }} /> {label}
            </label>
          ))}
          <label>Fertilizante juego (id):
            <input value={acts[cur.id]?.fertId || ''} onChange={e => setA(cur.id, { fertId: e.target.value })} aria-label={`Fertilizante ${cur.id}`} placeholder="NPK15_juego" style={{ fontSize: 16, minHeight: 44, width: 140, marginLeft: 6 }} />
          </label>
          <label>Fertilizante kg:
            <input value={acts[cur.id]?.fertKg || ''} onChange={e => setA(cur.id, { fertKg: e.target.value })} inputMode="decimal" aria-label={`Fertilizante kg ${cur.id}`} style={{ fontSize: 16, minHeight: 44, width: 90, marginLeft: 6 }} />
          </label>
          <label>Fitosanitario (se bloquea):
            <input value={acts[cur.id]?.spray || ''} onChange={e => setA(cur.id, { spray: e.target.value })} aria-label={`Fitosanitario ${cur.id}`} placeholder="bloqueado" style={{ fontSize: 16, minHeight: 44, width: 140, marginLeft: 6 }} />
          </label>
        </div>
      </section>
      {msg && <p role="status" style={{ background: '#e2e3e5', padding: 8 }}>{msg}</p>}
      <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
        <button onClick={newGame} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Nueva finca</button>
        <button onClick={() => advance(false)} disabled={!gameId || !online} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Avanzar 1 día</button>
        <button onClick={() => advance(true)} disabled={!gameId || !online} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Avanzar semana</button>
        <button onClick={advanceWeather} disabled={!gameId || !online} style={{ flex: 1, minHeight: 52, fontSize: 17 }}>Clima real Motril</button>
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
        <button onClick={saveAreas} disabled={!gameId} style={{ flex: 1, minHeight: 48 }}>Guardar finca</button>
        <button onClick={restart} disabled={!gameId} style={{ flex: 1, minHeight: 48 }}>Reiniciar</button>
        <button onClick={loadForecast} disabled={!gameId} style={{ flex: 1, minHeight: 48 }}>Previsión juego</button>
        <button onClick={saveVersion} disabled={!gameId || !online} style={{ flex: 1, minHeight: 48 }}>Guardar versión</button>
      </div>
      {info && <h2 style={{ fontSize: 18 }}>Caja: {info.cash_eur} € · Agua: {info.reservoir_m3} m³ · Deuda: {info.debt_eur ?? 0} € · Día: {info.day}</h2>}
      {info?.forecast && <p style={{ fontSize: 14 }}>Previsión: {JSON.stringify(info.forecast)} (orientativa)</p>}
      {forecast && <p style={{ fontSize: 14 }}>Previsión juego: {JSON.stringify(forecast.forecast)} · {forecast.nota}</p>}
      {versions.length > 0 && <p style={{ fontSize: 14 }}>Versiones: {versions.map((v: any) => `v${v.v} ${v.day}`).join(', ')} (ensayo)</p>}
      <section aria-label="Historial">
        <h2 style={{ fontSize: 18 }}>Historial (efectos y costes)</h2>
        {hist.length === 0 ? <p style={{ fontSize: 14 }}>Avanza días para ver qué pasó y cuánto costó. Incertidumbre: valores de juego, no calibrados.</p> :
          <ol>{hist.slice(-8).reverse().map((h: any, i: number) => (
            <li key={i} style={{ fontSize: 14 }}><b>{h.day}</b>: {(h.events || []).map((e: any) =>
              e.type === 'riego' ? `riego ${e.parcel} ${e.mm}mm (${e.m3}m³, ${e.coste_eur}€)` :
              e.type === 'labor' ? `labor ${e.parcel}: ${(e.tareas || []).join(',')} (${e.coste_eur}€)` :
              e.type === 'cosecha' ? `cosecha ${e.parcel}: ${e.kg}kg (lote)` :
              e.type === 'venta' ? `venta ${e.parcel}: ${e.kg}kg ${e.canal} → ${e.ingreso_eur}€ (escenario)` :
              e.type === 'vigilancia' ? `vigilancia ${e.parcel} (información general)` :
              e.type === 'tratamiento_bloqueado' ? `tratamiento bloqueado ${e.parcel} (requiere MAPA+técnico)` :
              `${e.type} ${e.parcel || ''}`).join(' · ')}{h.water_ledger?.length ? ` · agua: ${h.water_ledger.length} movimientos` : ''}</li>))}</ol>}
      </section>
      <section aria-label="Sistema">
        <h2 style={{ fontSize: 18 }}>Sistema y ensayo</h2>
        <button onClick={loadSys} style={{ minHeight: 48, fontSize: 16 }}>Ver privacidad, profesional y monitorización</button>
        {sys && <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>{JSON.stringify(sys, null, 2).slice(0, 2000)}</pre>}
      </section>
      {info?.prov && <details><summary style={{ fontSize: 14 }}>Procedencia e incertidumbre</summary><pre style={{ fontSize: 12 }}>{JSON.stringify(info.prov, null, 2)}</pre></details>}
    </main>
  )
}
