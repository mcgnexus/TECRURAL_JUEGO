import React, { useEffect, useRef } from 'react'

export type FarmParcel = { id: string; crop: string; soil: number; health: number }

/**
 * Finca genérica de la Axarquía en 2.5D — Canvas 2D, cero dependencias, sin imágenes externas.
 * Vista fija inclinada: cielo, sierras al fondo, 3 bancales con muros de piedra,
 * depósito con nivel de agua, caseta, camino y vegetación mediterránea.
 * Todo lo visual es orientativo del estado simulado (no medición ni diagnóstico).
 */
export default function AxarquiaFarm({ parcels, selected, onSelect, reservoirM3 }:
  { parcels: FarmParcel[]; selected: string | null; onSelect: (id: string) => void; reservoirM3?: number }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const boxes = useRef<{ id: string; x: number; y: number; w: number; h: number }[]>([])
  const order = useRef<string[]>(parcels.map(p => p.id))

  useEffect(() => { order.current = parcels.map(p => p.id) }, [parcels])

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const W = cv.clientWidth || 360
    const H = 400
    cv.width = W * dpr
    cv.height = H * dpr
    const ctx = cv.getContext('2d')
    if (!ctx) return
    ctx.scale(dpr, dpr)

    const clamp01 = (v: number) => Math.max(0, Math.min(1, v || 0))
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t
    const mix = (c1: number[], c2: number[], t: number) =>
      `rgb(${Math.round(lerp(c1[0], c2[0], t))},${Math.round(lerp(c1[1], c2[1], t))},${Math.round(lerp(c1[2], c2[2], t))})`

    // --- Cielo ---
    const sky = ctx.createLinearGradient(0, 0, 0, 110)
    sky.addColorStop(0, '#bfe0f2'); sky.addColorStop(1, '#f3e9d2')
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, 110)
    // Sol suave
    ctx.fillStyle = 'rgba(255,244,200,0.9)'
    ctx.beginPath(); ctx.arc(W - 52, 30, 16, 0, 7); ctx.fill()

    // --- Sierras al fondo (Tejeda/Almijara, genéricas) ---
    ctx.fillStyle = '#9db3c4'
    ctx.beginPath(); ctx.moveTo(0, 108)
    ctx.lineTo(W * 0.12, 62); ctx.lineTo(W * 0.26, 96); ctx.lineTo(W * 0.4, 58)
    ctx.lineTo(W * 0.55, 98); ctx.lineTo(W * 0.7, 70); ctx.lineTo(W * 0.85, 100)
    ctx.lineTo(W, 78); ctx.lineTo(W, 112); ctx.lineTo(0, 112); ctx.closePath(); ctx.fill()
    ctx.fillStyle = '#c8d6e2'
    ctx.beginPath(); ctx.moveTo(W * 0.36, 68); ctx.lineTo(W * 0.4, 58); ctx.lineTo(W * 0.44, 68); ctx.closePath(); ctx.fill()
    // Mar al fondo a la derecha (franja)
    ctx.fillStyle = '#a9cde8'; ctx.fillRect(W * 0.72, 104, W * 0.28, 7)

    // --- Ladera base ---
    const base = ctx.createLinearGradient(0, 108, 0, H)
    base.addColorStop(0, '#b9a06b'); base.addColorStop(1, '#8a6f45')
    ctx.fillStyle = base; ctx.fillRect(0, 110, W, H - 110)

    // Bancales: de arriba (fondo, pequeño) a abajo (frente, grande)
    const shown = parcels.slice(0, 3)
    const terraces = [
      { y: 128, h: 76, inset: 0.20 },
      { y: 210, h: 84, inset: 0.10 },
      { y: 300, h: 88, inset: 0.02 },
    ]
    boxes.current = []
    shown.forEach((p, i) => {
      const t = terraces[i]
      const x0 = W * t.inset + 8, x1 = W * (1 - t.inset) - 8
      const y0 = t.y, y1 = Math.min(t.y + t.h, H - 8)
      const skew = 22 // desplazamiento 2.5D
      const sel = selected === p.id

      // Suelo: color según humedad estimada (claro=seco, oscuro=húmedo)
      const wet = clamp01(p.soil / 60)
      const soil = mix([201, 168, 122], [106, 80, 52], wet)
      ctx.beginPath()
      ctx.moveTo(x0 + skew, y0); ctx.lineTo(x1 + skew, y0)
      ctx.lineTo(x1 - skew, y1); ctx.lineTo(x0 - skew, y1)
      ctx.closePath()
      ctx.fillStyle = soil; ctx.fill()
      // Surcos
      ctx.strokeStyle = 'rgba(60,40,20,0.18)'; ctx.lineWidth = 1
      for (let s = 1; s <= 3; s++) {
        const yy = y0 + ((y1 - y0) * s) / 4
        ctx.beginPath(); ctx.moveTo(x0 + skew * 0.4, yy); ctx.lineTo(x1 - skew * 0.4, yy); ctx.stroke()
      }
      // Muro de piedra del bancal (borde inferior)
      ctx.fillStyle = '#8d8577'
      ctx.beginPath()
      ctx.moveTo(x0 - skew, y1); ctx.lineTo(x1 - skew, y1)
      ctx.lineTo(x1 - skew, y1 + 8); ctx.lineTo(x0 - skew, y1 + 8)
      ctx.closePath(); ctx.fill()
      ctx.fillStyle = 'rgba(0,0,0,0.15)'
      for (let bx = x0 - skew + 4; bx < x1 - skew; bx += 14) ctx.fillRect(bx, y1 + 2, 2, 5)

      // Selección
      if (sel) {
        ctx.strokeStyle = '#ffd54f'; ctx.lineWidth = 4
        ctx.beginPath()
        ctx.moveTo(x0 + skew, y0); ctx.lineTo(x1 + skew, y0)
        ctx.lineTo(x1 - skew, y1); ctx.lineTo(x0 - skew, y1)
        ctx.closePath(); ctx.stroke()
      } else {
        ctx.strokeStyle = 'rgba(30,40,20,0.5)'; ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(x0 + skew, y0); ctx.lineTo(x1 + skew, y0)
        ctx.lineTo(x1 - skew, y1); ctx.lineTo(x0 - skew, y1)
        ctx.closePath(); ctx.stroke()
      }

      // Árboles 2.5D: forma y tamaño por cultivo, vigor por sanidad (juego)
      const health = clamp01(p.health)
      const perRow = i === 2 ? 6 : 5
      const rows = 2
      let seed = (p.id.charCodeAt(1) || 80) * 7919 + 13
      const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff
      const canopyBase = p.crop === 'mango' ? 13 : p.crop === 'chirimoyo' ? 10 : 12
      for (let r = 0; r < rows; r++) {
        for (let k = 0; k < perRow; k++) {
          const fx = (k + 0.5 + (r % 2) * 0.4) / (perRow + 0.4)
          const fy = (r + 0.6) / (rows + 0.5)
          const jx = (rnd() - 0.5) * 10, jy = (rnd() - 0.5) * 6
          const x = lerp(x0, x1, fx) + jx
          const y = lerp(y0 + 14, y1 - 10, fy) + jy
          const s = lerp(0.55, 1.1, health) * (i === 0 ? 0.8 : 1)
          const cr = canopyBase * s
          // Sombra
          ctx.fillStyle = 'rgba(0,0,0,0.18)'
          ctx.beginPath(); ctx.ellipse(x + 3, y + 5, cr * 0.9, cr * 0.35, 0, 0, 7); ctx.fill()
          // Tronco
          ctx.fillStyle = '#6b4a2c'
          ctx.fillRect(x - 1.5, y, 3, 8 * s)
          // Copa: verde sano -> amarillento estresado (juego, no diagnóstico)
          const canopy = p.crop === 'mango'
            ? mix([168, 163, 90], [46, 110, 40], health)
            : p.crop === 'chirimoyo'
              ? mix([178, 170, 100], [70, 130, 55], health)
              : mix([170, 162, 92], [44, 105, 48], health)
          ctx.fillStyle = canopy
          if (p.crop === 'mango') {
            ctx.beginPath(); ctx.ellipse(x, y - 5 * s, cr, cr * 0.72, 0, 0, 7); ctx.fill()
            ctx.fillStyle = 'rgba(255,255,255,0.25)'
            ctx.beginPath(); ctx.ellipse(x - cr * 0.3, y - 8 * s, cr * 0.35, cr * 0.22, -0.4, 0, 7); ctx.fill()
          } else if (p.crop === 'chirimoyo') {
            ctx.beginPath(); ctx.arc(x, y - 4 * s, cr * 0.8, 0, 7); ctx.fill()
            ctx.beginPath(); ctx.arc(x - cr * 0.3, y - 7 * s, cr * 0.45, 0, 7); ctx.fill()
          } else {
            ctx.beginPath(); ctx.arc(x, y - 5 * s, cr * 0.85, 0, 7); ctx.fill()
            ctx.beginPath(); ctx.arc(x + cr * 0.35, y - 3 * s, cr * 0.55, 0, 7); ctx.fill()
          }
          // Fruta orientativa (puntos) solo si vigor alto
          if (health > 0.55) {
            ctx.fillStyle = p.crop === 'mango' ? '#e8912d' : p.crop === 'chirimoyo' ? '#b9c46a' : '#3d5a27'
            for (let f = 0; f < 3; f++) {
              ctx.beginPath()
              ctx.arc(x + (rnd() - 0.5) * cr, y - 5 * s + (rnd() - 0.5) * cr * 0.7, 1.8, 0, 7)
              ctx.fill()
            }
          }
        }
      }

      // Etiqueta de parcela
      const glyph = p.crop === 'aguacate' ? '●' : p.crop === 'mango' ? '▲' : '■'
      ctx.fillStyle = 'rgba(255,255,255,0.92)'
      const label = `${p.id} ${glyph} ${p.crop}`
      ctx.font = 'bold 13px system-ui'
      const tw = ctx.measureText(label).width + 14
      const lx = lerp(x0, x1, 0.5) - tw / 2
      ctx.fillRect(lx, y0 + 4, tw, 19)
      ctx.fillStyle = '#1b2a1b'; ctx.textAlign = 'left'
      ctx.fillText(label, lx + 7, y0 + 18)

      boxes.current.push({ id: p.id, x: x0 - skew - 6, y: y0 - 4, w: (x1 - x0) + skew * 2 + 12, h: (y1 - y0) + 16 })
    })

    // --- Camino ---
    ctx.strokeStyle = '#e6d9bd'; ctx.lineWidth = 10; ctx.lineCap = 'round'
    ctx.beginPath(); ctx.moveTo(W * 0.06, H - 6); ctx.quadraticCurveTo(W * 0.4, H - 60, W * 0.62, 210); ctx.stroke()
    ctx.strokeStyle = 'rgba(120,95,60,0.35)'; ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(W * 0.06, H - 6); ctx.quadraticCurveTo(W * 0.4, H - 60, W * 0.62, 210); ctx.stroke()

    // --- Depósito con nivel (refleja reservoir_m3 de juego) ---
    const cap = 200
    const lvl = clamp01((reservoirM3 ?? 80) / cap)
    const dx = W - 86, dy = H - 108, dw = 62, dh = 56
    ctx.fillStyle = 'rgba(0,0,0,0.2)'
    ctx.beginPath(); ctx.ellipse(dx + dw / 2, dy + dh + 6, dw / 2, 7, 0, 0, 7); ctx.fill()
    ctx.fillStyle = '#f5f5f2'; ctx.fillRect(dx, dy, dw, dh)
    ctx.strokeStyle = '#5d6b73'; ctx.lineWidth = 2; ctx.strokeRect(dx, dy, dw, dh)
    ctx.fillStyle = '#2d9cdb'
    const wh = (dh - 8) * lvl
    ctx.fillRect(dx + 4, dy + dh - 4 - wh, dw - 8, wh)
    ctx.fillStyle = '#123'; ctx.font = '11px system-ui'; ctx.textAlign = 'center'
    ctx.fillText('Depósito', dx + dw / 2, dy - 6)
    ctx.fillStyle = '#fff'; ctx.font = 'bold 11px system-ui'
    ctx.fillText(`${Math.round(lvl * 100)}%`, dx + dw / 2, dy + dh / 2 + 4)

    // --- Caseta de aperos ---
    const hx = 14, hy = H - 66
    ctx.fillStyle = '#f0e6d2'; ctx.fillRect(hx, hy + 12, 52, 30)
    ctx.fillStyle = '#b5542d'
    ctx.beginPath(); ctx.moveTo(hx - 4, hy + 12); ctx.lineTo(hx + 26, hy - 4); ctx.lineTo(hx + 56, hy + 12); ctx.closePath(); ctx.fill()
    ctx.fillStyle = '#4a3a28'; ctx.fillRect(hx + 20, hy + 24, 12, 18)

    // --- Vegetación mediterránea (chumberas, retama, ciprés) ---
    ctx.fillStyle = '#5d7d3a'
    const bushes: [number, number][] = [[W * 0.12, 200], [W * 0.88, 200], [W * 0.1, 292], [W * 0.9, 292]]
    bushes.forEach(([bx, by]) => {
      ctx.beginPath(); ctx.ellipse(bx, by, 10, 6, 0, 0, 7); ctx.fill()
      ctx.beginPath(); ctx.ellipse(bx + 7, by - 3, 7, 5, 0.3, 0, 7); ctx.fill()
    })
    ctx.fillStyle = '#2f5d33'
    ctx.beginPath(); ctx.ellipse(W * 0.06, 150, 6, 16, 0, 0, 7); ctx.fill()
    ctx.beginPath(); ctx.ellipse(W * 0.94, 150, 6, 16, 0, 0, 7); ctx.fill()
  }, [parcels, selected, reservoirM3])

  function at(px: number, py: number) {
    return boxes.current.find(b => px >= b.x && px <= b.x + b.w && py >= b.y && py <= b.y + b.h)
  }
  function pick(e: React.MouseEvent | React.TouchEvent) {
    const cv = ref.current
    if (!cv) return
    const r = cv.getBoundingClientRect()
    const t = 'touches' in e && (e as React.TouchEvent).touches[0]
      ? (e as React.TouchEvent).touches[0] as unknown as { clientX: number; clientY: number } : null
    const px = t ? t.clientX - r.left : (e as React.MouseEvent).clientX - r.left
    const py = t ? t.clientY - r.top : (e as React.MouseEvent).clientY - r.top
    const hit = at(px, py)
    if (hit) onSelect(hit.id)
  }
  function keys(e: React.KeyboardEvent) {
    const ids = order.current
    const i = ids.indexOf(selected || ids[0])
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault()
      onSelect(ids[(i + (e.key === 'ArrowRight' ? 1 : -1) + ids.length) % ids.length])
    }
  }

  return (
    <div>
      <canvas ref={ref} onClick={pick} onTouchStart={pick} onKeyDown={keys} tabIndex={0} role="img"
        aria-label="Finca genérica de la Axarquía en bancales. Usa flechas izquierda y derecha para cambiar de parcela."
        style={{ width: '100%', height: 400, touchAction: 'manipulation', borderRadius: 12, background: '#e8f5e9' }} />
      <p style={{ fontSize: 13 }}>Leyenda: ● aguacate · ▲ mango · ■ chirimoyo (formas distintas además del color). Suelo oscuro = humedad estimada alta; copa amarillenta = vigor bajo en el juego. Aspecto orientativo, no medido ni diagnóstico.</p>
    </div>
  )
}
