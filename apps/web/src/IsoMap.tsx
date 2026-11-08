import React, { useEffect, useRef } from 'react'

export type IsoParcel = { id: string; crop: string; soil: number; health: number }

/** Mapa isométrico táctil Canvas 2D — cero dependencias.
 * Tres cultivos distinguibles sin color: aguacate=círculos, mango=triángulos, chirimoyo=cuadrados. */
export default function IsoMap({ parcels, selected, onSelect }: { parcels: IsoParcel[]; selected: string | null; onSelect: (id: string) => void }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const boxes = useRef<{ id: string; x: number; y: number; w: number; h: number }[]>([])
  const order = useRef<string[]>(parcels.map(p => p.id))

  useEffect(() => { order.current = parcels.map(p => p.id) }, [parcels])

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const W = cv.clientWidth || 360
    const H = 310
    cv.width = W * dpr
    cv.height = H * dpr
    const ctx = cv.getContext('2d')
    if (!ctx) return
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, W, H)

    const colors: Record<string, string> = { aguacate: '#2e7d32', mango: '#ef6c00', chirimoyo: '#558b2f' }
    const tw = Math.min(150, (W - 32) / 2.2)
    const th = tw / 2.4
    boxes.current = []
    parcels.slice(0, 3).forEach((p, i) => {
      const cx = W / 2 + (i - 1) * (tw * 0.72)
      const cy = 120 + (i % 2) * 44
      const sel = selected === p.id
      ctx.beginPath()
      ctx.moveTo(cx, cy - th / 2); ctx.lineTo(cx + tw / 2, cy); ctx.lineTo(cx, cy + th / 2); ctx.lineTo(cx - tw / 2, cy)
      ctx.closePath()
      ctx.fillStyle = sel ? '#ffd54f' : (colors[p.crop] || '#33691e')
      ctx.fill()
      ctx.lineWidth = sel ? 4 : 2
      ctx.strokeStyle = sel ? '#1a237e' : '#10270f'
      ctx.stroke()
      // árboles distinguibles por forma (juego)
      let seed = p.id.charCodeAt(1) * 7919 + 13
      const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff
      for (let t = 0; t < 8; t++) {
        const ox = (rnd() - 0.5) * tw * 0.55
        const oy = (rnd() - 0.5) * th * 0.55
        const x = cx + ox, y = cy + oy
        ctx.fillStyle = 'rgba(255,255,255,0.9)'
        if (p.crop === 'aguacate') { ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 7); ctx.fill() }
        else if (p.crop === 'mango') { ctx.beginPath(); ctx.moveTo(x, y - 5); ctx.lineTo(x + 5, y + 4); ctx.lineTo(x - 5, y + 4); ctx.closePath(); ctx.fill() }
        else { ctx.fillRect(x - 4, y - 4, 8, 8) }
      }
      ctx.fillStyle = '#000'
      ctx.font = 'bold 15px system-ui'
      ctx.textAlign = 'center'
      const glyph = p.crop === 'aguacate' ? '●' : p.crop === 'mango' ? '▲' : '■'
      ctx.fillText(`${p.id} ${glyph} ${p.crop}`, cx, cy + th / 2 + 20)
      boxes.current.push({ id: p.id, x: cx - tw / 2 - 8, y: cy - th / 2 - 22, w: tw + 16, h: th + 44 })
    })
  }, [parcels, selected])

  function at(px: number, py: number) {
    return boxes.current.find(b => px >= b.x && px <= b.x + b.w && py >= b.y && py <= b.y + b.h)
  }
  function pick(e: React.MouseEvent | React.TouchEvent) {
    const cv = ref.current
    if (!cv) return
    const r = cv.getBoundingClientRect()
    const t = 'touches' in e && (e as React.TouchEvent).touches[0] ? (e as React.TouchEvent).touches[0] as unknown as { clientX: number; clientY: number } : null
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
        aria-label="Mapa isométrico de parcelas. Usa flechas izquierda y derecha para cambiar de parcela."
        style={{ width: '100%', height: 310, touchAction: 'manipulation', borderRadius: 12, background: '#e8f5e9' }} />
      <p style={{ fontSize: 13 }} aria-hidden={false}>Leyenda: ● aguacate · ▲ mango · ■ chirimoyo (formas distintas además del color).</p>
    </div>
  )
}
