import { useState } from 'react'

type Point = { fecha: string; agua_estimada_mm: number }
export type SoilResult = {
  escenarios: { habitual: Point[]; alternativa: Point[] }
  suelo: { texture: string; capacity_mm: number; initial_mm: number; capacity_source: string; initial_source: string }
  meteorologia: { dias: { fecha: string; precip_mm: number; et0_mm: number }[] }
}

export default function SoilCrossSection({ result }: { result: SoilResult }) {
  const [scenario, setScenario] = useState<'habitual' | 'alternativa'>('habitual')
  const [day, setDay] = useState(0)
  const points = result.escenarios[scenario]
  const point = points[day]
  const weather = result.meteorologia.dias.find(d => d.fecha === point?.fecha)
  if (!point) return null

  return <section aria-labelledby="soil-heading" style={{ background: '#fff', padding: 20, margin: '24px 0', borderRadius: 12 }}>
    <h3 id="soil-heading">Un vistazo bajo el suelo</h3>
    <p>Las raíces absorben agua del suelo; la lluvia y el riego aportan agua a la zona de raíces. Es una explicación simplificada, no una representación de la parcela.</p>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
      <label>Escenario <select value={scenario} onChange={e => setScenario(e.target.value as 'habitual' | 'alternativa')}><option value="habitual">Riego habitual</option><option value="alternativa">Riego alternativo</option></select></label>
      <label>Día <select value={day} onChange={e => setDay(Number(e.target.value))}>{points.map((p, i) => <option key={p.fecha} value={i}>{p.fecha}</option>)}</select></label>
    </div>
    <svg viewBox="0 0 600 350" role="img" aria-labelledby="soil-figure-title soil-figure-desc" style={{ width: '100%', height: 'auto', marginTop: 16 }}>
      <title id="soil-figure-title">Corte didáctico del suelo y las raíces</title>
      <desc id="soil-figure-desc">Un árbol, raíces y flechas esquemáticas ilustran lluvia, riego y absorción de agua. No representan profundidades ni mediciones reales.</desc>
      <rect width="600" height="350" rx="16" fill="#e5f3f1" />
      <path d="M0 145 Q130 135 260 145 T600 145 V350 H0Z" fill="#8d684c" />
      <path d="M0 155 Q160 145 300 155 T600 155" fill="none" stroke="#557947" strokeWidth="9" />
      <path d="M295 148 L290 78 L310 78 L305 148" fill="#765039" />
      <circle cx="300" cy="66" r="48" fill="#487b54" /><circle cx="263" cy="77" r="30" fill="#608e61" /><circle cx="337" cy="77" r="30" fill="#608e61" />
      <g fill="none" stroke="#e4c9a0" strokeLinecap="round"><path d="M300 146 C300 190 285 225 282 285 M298 168 C265 180 251 213 214 236 M295 194 C267 202 260 251 238 270 M305 169 C342 180 354 218 392 237 M305 201 C331 216 338 254 362 278" strokeWidth="5" /><path d="M250 209 l-23 -6 m24 7 l-6 26 m98 -28 l21 -5 m-18 11 l6 25 M281 251 l-20 18 m26 -54 l18 15" strokeWidth="2.5" /></g>
      <g fill="none" stroke="#296d9d" strokeWidth="5" strokeLinecap="round"><path d="M90 72 v48 m-9 -10 l9 10 l9 -10 M145 72 v48 m-9 -10 l9 10 l9 -10 M487 72 v48 m-9 -10 l9 10 l9 -10" /></g>
      <g fill="none" stroke="#eaf6eb" strokeWidth="4" strokeLinecap="round"><path d="M216 290 Q237 273 252 250 m-2 13 l2 -13 l-13 3 M385 290 Q367 272 350 250 m13 3 l-13 -3 l2 13" /></g>
      <g fontFamily="system-ui, sans-serif" fontSize="17" fontWeight="600"><text x="75" y="56" fill="#245a7a">Lluvia</text><text x="466" y="56" fill="#245a7a">Riego</text><text x="195" y="320" fill="#fff">Absorción por las raíces</text></g>
    </svg>
    <p><strong>{point.fecha} · {scenario === 'habitual' ? 'Riego habitual' : 'Riego alternativo'}:</strong> agua total estimada en la zona de raíces: <strong>{point.agua_estimada_mm} mm</strong> de {result.suelo.capacity_mm} mm de capacidad.</p>
    {weather && <p>Lluvia prevista ese día: {weather.precip_mm} mm.</p>}
    <p>Tipo de suelo: {result.suelo.texture === 'desconocido' ? 'no conocido' : result.suelo.texture}. Capacidad: {result.suelo.capacity_source}. Agua inicial: {result.suelo.initial_mm} mm ({result.suelo.initial_source}).</p>
    <p><strong>Ilustración esquemática:</strong> la forma y profundidad de las raíces y la distribución del agua por profundidad no son mediciones ni resultados del modelo. Las flechas explican procesos y no indican cantidades calculadas. Simulación experimental, no una recomendación profesional.</p>
  </section>
}
