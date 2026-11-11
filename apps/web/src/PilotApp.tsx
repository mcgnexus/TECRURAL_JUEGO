import React, { useState } from 'react'
import AxarquiaFarm from './AxarquiaFarm'

type Municipality = { name: string; admin1?: string; admin2?: string; latitude: number; longitude: number }
type Point = { fecha: string; agua_estimada_mm: number }
type Result = { escenarios: { habitual: Point[]; alternativa: Point[] }; meteorologia: { fuente: string; consultado_en: string; dias: { fecha: string; precip_mm: number; et0_mm: number }[] }; supuestos: string[]; aviso: string }
const API = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

export default function PilotApp() {
  const [example, setExample] = useState<boolean | null>(null)
  const [query, setQuery] = useState('')
  const [locations, setLocations] = useState<Municipality[]>([])
  const [location, setLocation] = useState<Municipality | null>(null)
  const [crop, setCrop] = useState('aguacate')
  const [area, setArea] = useState('1')
  const [usual, setUsual] = useState('4')
  const [alternative, setAlternative] = useState('2')
  const [result, setResult] = useState<Result | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function search(name = query, useFirst = false) {
    setBusy(true); setMessage(''); setResult(null); setLocation(null); setLocations([])
    try {
      const response = await fetch(`${API}/pilot/municipios?q=${encodeURIComponent(name)}`)
      if (!response.ok) throw new Error('No se pudo consultar el municipio.')
      const data = await response.json()
      setLocations(data.municipios)
      if (useFirst) {
        const motril = data.municipios.find((m: Municipality) => m.name.toLowerCase() === 'motril' && m.admin1 === 'Andalucía')
        if (motril) setLocation(motril)
        else setMessage('No se encontró Motril; busque un municipio de referencia.')
      } else if (!data.municipios.length) setMessage('No se encontraron localidades. Pruebe otro nombre.')
    } catch { setMessage('El buscador de municipios no está disponible. Inténtelo de nuevo.') }
    finally { setBusy(false) }
  }

  async function compare(e: React.FormEvent) {
    e.preventDefault()
    if (!location) { setMessage('Busque y seleccione un municipio.'); return }
    setBusy(true); setMessage(''); setResult(null)
    try {
      const response = await fetch(`${API}/pilot/comparar`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: location.latitude, longitude: location.longitude, crop, area_ha: Number(area), usual_mm: Number(usual), alternative_mm: Number(alternative) }) })
      if (!response.ok) throw new Error('La previsión no está disponible o está incompleta. No se ha realizado la simulación.')
      setResult(await response.json())
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo realizar la simulación.') }
    finally { setBusy(false) }
  }

  const input = { display: 'block', fontSize: 16, padding: 10, width: '100%', boxSizing: 'border-box' as const, marginTop: 5 }
  return <main style={{ fontFamily: 'system-ui, sans-serif', color: '#173c37', background: '#f3f8f5', minHeight: '100vh', padding: '24px 16px' }}>
    <div style={{ maxWidth: 720, margin: 'auto' }}>
      <header><strong>TecRural</strong><h1 style={{ fontFamily: 'Georgia, serif', fontSize: 'clamp(32px, 7vw, 50px)' }}>Tu finca, unos días por delante</h1>
        <p>Explora cómo podrían influir el tiempo previsto y el riego en el agua estimada del suelo.</p>
        <p><strong>Simulación experimental:</strong> no es una medición ni una recomendación profesional.</p></header>
      {example === null ? <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button style={{ padding: 14 }} onClick={() => { setExample(true); setQuery('Motril'); void search('Motril', true) }}>Probar con una finca de ejemplo</button>
        <button style={{ padding: 14 }} onClick={() => setExample(false)}>Crear mi parcela</button>
      </div> : <>
        {example && <><p><strong>Finca ficticia:</strong> el ejemplo usa Motril como referencia meteorológica, no el microclima de una parcela.</p>
          <AxarquiaFarm parcels={[{ id: 'P1', crop: 'aguacate', soil: 40, health: 0.9 }]} selected="P1" onSelect={() => {}} /></>}
        <form onSubmit={compare} onChange={() => setResult(null)} style={{ display: 'grid', gap: 15, background: 'white', padding: 20 }}>
          <h2>Datos para explorar</h2>
          <label>Municipio o zona aproximada<input style={input} value={query} onChange={e => { setQuery(e.target.value); setLocation(null); setLocations([]) }} minLength={2} /></label>
          <button type="button" disabled={busy || query.trim().length < 2} onClick={() => void search()}>Buscar municipio</button>
          {locations.length > 0 && <label>Seleccione una localidad<select style={input} value={location ? String(locations.indexOf(location)) : ''} onChange={e => setLocation(e.target.value === '' ? null : locations[Number(e.target.value)])}>
            <option value="">Seleccione una localidad</option>{locations.map((m, i) => <option key={`${m.latitude}-${m.longitude}-${i}`} value={i}>{m.name}, {m.admin2 || m.admin1 || 'España'}</option>)}
          </select></label>}
          {location && <p>Referencia: {location.name}, {location.admin2 || location.admin1}. No representa necesariamente el microclima de la finca.</p>}
          <label>Cultivo<select style={input} value={crop} onChange={e => setCrop(e.target.value)}><option value="aguacate">Aguacate</option><option value="mango">Mango</option><option value="chirimoyo">Chirimoyo</option></select></label>
          <label>Superficie aproximada (hectáreas)<input style={input} type="number" min="0.1" max="10" step="0.1" required value={area} onChange={e => setArea(e.target.value)} /></label>
          <label>Riego habitual de juego (mm al día)<input style={input} type="number" min="0" max="100" step="0.1" required value={usual} onChange={e => setUsual(e.target.value)} /></label>
          <label>Riego alternativo de juego (mm al día)<input style={input} type="number" min="0" max="100" step="0.1" required value={alternative} onChange={e => setAlternative(e.target.value)} /></label>
          <p>Se comparan las mismas cantidades cada día. No convertimos duración a volumen sin conocer el caudal.</p>
          <button disabled={busy || !location} type="submit" style={{ padding: 14, background: '#205b4e', color: 'white', fontSize: 16 }}>Comparar opciones</button>
        </form>
        <button type="button" onClick={() => { setExample(null); setResult(null); setLocation(null); setLocations([]) }}>Volver al inicio</button>
      </>}
      {message && <p role="alert">{message}</p>}
      {busy && <p role="status">Consultando datos…</p>}
      {result && <section><h2>Cómo cambia el agua estimada</h2><p>{result.aviso}</p>
        <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', textAlign: 'left' }}><thead><tr><th>Fecha</th><th>Riego habitual</th><th>Riego alternativo</th></tr></thead>
          <tbody>{result.escenarios.habitual.map((p, i) => <tr key={p.fecha}><th scope="row">{p.fecha}</th><td>{p.agua_estimada_mm} mm</td><td>{result.escenarios.alternativa[i]?.agua_estimada_mm} mm</td></tr>)}</tbody></table></div>
        <details><summary>¿Por qué veo esto?</summary><p>{result.meteorologia.fuente}; consulta: {result.meteorologia.consultado_en}. La previsión es modelizada, no observada.</p>
          <ul>{result.supuestos.map(s => <li key={s}>{s}</li>)}</ul>
          <p>Riego diario: {usual} mm y {alternative} mm. Superficie: {area} ha. Cultivo: {crop}.</p>
          <ul>{result.meteorologia.dias.map(d => <li key={d.fecha}>{d.fecha}: lluvia prevista {d.precip_mm} mm; ET0 prevista {d.et0_mm} mm</li>)}</ul>
        </details></section>}
    </div>
  </main>
}
