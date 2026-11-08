import React, { useEffect, useRef } from 'react'

export type IsoParcel = { id: string; crop: string; variety: string; edad: number; soil: number; health: number }

/** Mapa isométrico táctil Canvas 2D — cero dependencias. Diamantes 2.5D, tap ≥44px. */
export default function IsoMap({ parcels, selected, onSelect }: { parcels: IsoParcel[]; selected: string | null; onSelect: (id: string) => void }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const boxes = useRef<{ id: string; x: number; y: number; w: number; h: number }[]>([])

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const W = cv.clientWidth || 360
    const H = 300
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
      // diamante isométrico
      ctx.beginPath()
      ctx.moveTo(cx, cy - th / 2); ctx.lineTo(cx + tw / 2, cy); ctx.lineTo(cx, cy + th / 2); ctx.lineTo(cx - tw / 2, cy)
      ctx.closePath()
      ctx.fillStyle = sel ? '#ffd54f' : (colors[p.crop] || '#33691e')
      ctx.fill()
      ctx.lineWidth = sel ? 4 : 2
      ctx.strokeStyle = sel ? '#1a237e' : '#10270f'
      ctx.stroke()
      // arbolitos deterministas (juego)
      ctx.fillStyle = 'rgba(255,255,255,0.85)'
      let seed = p.id.charCodeAt(1) * 7919
      const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff
      for (let t = 0; t < 8; t++) {
        const ox = (rnd() - 0.5) * tw * 0.55
        const oy = (rnd() - 0.5) * th * 0.55
        ctx.beginPath(); ctx.arc(cx + ox, cy + oy, 4, 0, 7); ctx.fill()
      }
      ctx.fillStyle = '#000'
      ctx.font = 'bold 15px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(`${p.id} · ${p.crop}`, cx, cy + th / 2 + 20)
      // área táctil ampliada ≥44px
      boxes.current.push({ id: p.id, x: cx - tw / 2 - 8, y: cy - th / 2 - 22, w: tw + 16, h: th + 44 })
    })
  }, [parcels, selected])

  function pick(e: React.MouseEvent | React.TouchEvent) {
    const cv = ref.current
    if (!cv) return
    const r = cv.getBoundingClientRect()
    const t = 'touches' in e ? (e as React.TouchEvent).touches[0] : null
    const px = t ? t.clientX - r.left : (e as React.MouseEvent).clientX - r.left
    const py = t ? t.clientY - r.top : (e as React.MouseEvent).clientY - r.top
    const hit = boxes.current.find(b => px >= b.x && px <= b.x + b.w && py >= b.y && py <= b.y + b.h)
    if (hit) onSelect(hit.id)
  }

  return <canvas ref={ref} onClick={pick} onTouchStart={pick} aria-label="Mapa isométrico de parcelas"
    style={{ width: '100%', height: 300, touchAction: 'manipulation', borderRadius: 12, background: '#e8f5e9' }} />
}
