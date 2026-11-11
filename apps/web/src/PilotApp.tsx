import React, { useState } from 'react'
import AxarquiaFarm from './AxarquiaFarm'
import SoilCrossSection, { type SoilResult } from './SoilCrossSection'

type Municipality = { name: string; admin1?: string; admin2?: string; latitude: number; longitude: number }
type Point = { fecha: string; agua_estimada_mm: number }
type Result = SoilResult & { escenarios: { habitual: Point[]; alternativa: Point[] }; meteorologia: { fuente: string; consultado_en: string; dias: { fecha: string; precip_mm: number; et0_mm: number }[] }; supuestos: string[]; aviso: string }
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
  const [soil, setSoil] = useState('desconocido')
  const [soilCapacity, setSoilCapacity] = useState('')
  const [soilInitial, setSoilInitial] = useState('')
  const [trees, setTrees] = useState('')
  const [variety, setVariety] = useState('')
  const [treeAge, setTreeAge] = useState('')
  const [flow, setFlow] = useState('')
  const [duration, setDuration] = useState('')
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
        body: JSON.stringify({ latitude: location.latitude, longitude: location.longitude, crop, area_ha: Number(area), usual_mm: Number(usual), alternative_mm: Number(alternative), soil_texture: soil, soil_capacity_mm: soilCapacity === '' ? null : Number(soilCapacity), soil_initial_mm: soilInitial === '' ? null : Number(soilInitial) }) })
      if (!response.ok) {
        const data = await response.json().catch(() => null)
        throw new Error(typeof data?.detail === 'string' ? data.detail : 'No se pudo realizar la simulación. Compruebe los datos.')
      }
      setResult(await response.json())
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo realizar la simulación.') }
    finally { setBusy(false) }
  }

  async function convertIrrigation() {
    if (!flow || !duration) { setMessage('Indique el caudal total y la duración del riego.'); return }
    setBusy(true); setMessage(''); setResult(null)
    try {
      const response = await fetch(`${API}/pilot/convertir-riego`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ area_ha: Number(area), flow_m3_hour: Number(flow), duration_hours: Number(duration) }) })
      if (!response.ok) throw new Error('No se pudo convertir: compruebe superficie, caudal y duración.')
      const data = await response.json()
      setUsual(String(Number(data.mm_por_riego.toFixed(3))))
      setMessage('Conversión aplicada al riego habitual. En la simulación se aplicará cada día.')
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo convertir el riego.') }
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
          <label>Tipo de suelo (opcional)<select style={input} value={soil} onChange={e => setSoil(e.target.value)}><option value="desconocido">No lo sé</option><option value="arenoso">Arenoso</option><option value="franco">Franco</option><option value="arcilloso">Arcilloso</option><option value="otro">Otro</option></select></label>
          <p>El tipo selecciona una capacidad ficticia de juego, no validada. No describe por sí solo el suelo real.</p>
          <label>Capacidad de almacenamiento de agua en la zona de raíces (mm, opcional)<input style={input} type="number" min="1" max="500" step="any" value={soilCapacity} onChange={e => setSoilCapacity(e.target.value)} /></label>
          <label>Agua inicial en la zona de raíces (mm, opcional)<input style={input} type="number" min="0" max="500" step="any" value={soilInitial} onChange={e => setSoilInitial(e.target.value)} /></label>
          <p>Indique valores locales solo si conoce su significado y unidades. Sin capacidad se usa un supuesto de juego; sin agua inicial, se supone el 50 % de la capacidad. Ningún valor se verifica automáticamente.</p>
          <label>Número aproximado de árboles (opcional)<input style={input} type="number" min="1" max="100000" step="1" value={trees} onChange={e => setTrees(e.target.value)} /></label>
          <label>Variedad (opcional)<input style={input} maxLength={80} value={variety} onChange={e => setVariety(e.target.value)} /></label>
          <label>Edad aproximada de los árboles, en años (opcional)<input style={input} type="number" min="0" max="200" step="1" value={treeAge} onChange={e => setTreeAge(e.target.value)} /></label>
          <p>Árboles, variedad y edad son solo contexto: todavía no modifican el cálculo. Los datos no se guardan.</p>
          <details><summary>Calcular el riego a partir de caudal y duración</summary>
            <p>Indique el caudal total de la parcela, no el de un solo gotero. Se necesita la superficie para obtener mm por riego.</p>
            <label>Caudal total (m³/h)<input style={input} type="number" min="0" step="any" value={flow} onChange={e => setFlow(e.target.value)} /></label>
            <label>Duración de cada riego (horas)<input style={input} type="number" min="0" step="any" value={duration} onChange={e => setDuration(e.target.value)} /></label>
            <button type="button" disabled={busy} onClick={() => void convertIrrigation()}>Usar como riego habitual diario</button>
          </details>
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
        <SoilCrossSection result={result} />
        <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', textAlign: 'left' }}><thead><tr><th>Fecha</th><th>Riego habitual</th><th>Riego alternativo</th></tr></thead>
          <tbody>{result.escenarios.habitual.map((p, i) => <tr key={p.fecha}><th scope="row">{p.fecha}</th><td>{p.agua_estimada_mm} mm</td><td>{result.escenarios.alternativa[i]?.agua_estimada_mm} mm</td></tr>)}</tbody></table></div>
        <details><summary>¿Por qué veo esto?</summary><p>{result.meteorologia.fuente}; consulta: {result.meteorologia.consultado_en}. La previsión es modelizada, no observada.</p>
          <ul>{result.supuestos.map(s => <li key={s}>{s}</li>)}</ul>
          <p>Riego diario: {usual} mm y {alternative} mm. Superficie: {area} ha. Cultivo: {crop}.</p>
          <p>Datos de contexto, no utilizados en el cálculo: árboles {trees || 'no indicado'}; variedad {variety || 'no indicada'}; edad {treeAge ? `${treeAge} años` : 'no indicada'}.</p>
          <ul>{result.meteorologia.dias.map(d => <li key={d.fecha}>{d.fecha}: lluvia prevista {d.precip_mm} mm; ET0 prevista {d.et0_mm} mm</li>)}</ul>
        </details></section>}
    </div>
  </main>
}
