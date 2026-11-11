import { useEffect, useRef, useState } from 'react'
import * as pdfjs from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

// Renders every page of the PDF and draws highlight boxes from the backend's
// coordinates (PDF points, top-left origin, same as CSS).
export default function PdfViewer({ url, highlights, activeId, scrollSignal, onSelect }) {
  const wrap = useRef(null)
  const [doc, setDoc] = useState(null)
  const [width, setWidth] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const task = pdfjs.getDocument({ url })
    task.promise.then((d) => { if (!cancelled) setDoc(d) }).catch((e) => { console.error('pdf.js', e); setError('The PDF could not be displayed.') })
    return () => { cancelled = true; task.destroy() }
  }, [url])

  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!activeId || !wrap.current) return
    const el = wrap.current.querySelector(`[data-hl="${activeId}"]`)
    el?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' })
  }, [activeId, scrollSignal, doc, width])

  return (
    <div className="pdf" ref={wrap}>
      {error && <p className="pdf-error">{error}</p>}
      {!doc && !error && <p className="pdf-loading">Loading pages…</p>}
      {doc && width > 0 && Array.from({ length: doc.numPages }, (_, i) => (
        <Page key={i} doc={doc} index={i} width={width} highlights={highlights} activeId={activeId} onSelect={onSelect} />
      ))}
    </div>
  )
}

function Page({ doc, index, width, highlights, activeId, onSelect }) {
  const canvas = useRef(null)
  const [size, setSize] = useState(null)

  useEffect(() => {
    let task
    let cancelled = false
    doc.getPage(index + 1).then((page) => {
      if (cancelled) return
      const base = page.getViewport({ scale: 1 })
      const scale = width / base.width
      const viewport = page.getViewport({ scale })
      const ratio = window.devicePixelRatio || 1
      const c = canvas.current
      c.width = Math.floor(viewport.width * ratio)
      c.height = Math.floor(viewport.height * ratio)
      c.style.width = `${viewport.width}px`
      c.style.height = `${viewport.height}px`
      const ctx = c.getContext('2d')
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      setSize({ scale, w: viewport.width, h: viewport.height })
      task = page.render({ canvas: c, canvasContext: ctx, viewport })
      task.promise.catch(() => {})
    })
    return () => { cancelled = true; task?.cancel() }
  }, [doc, index, width])

  return (
    <div className="pdf-page" style={size ? { width: size.w, height: size.h } : { width, aspectRatio: '1 / 1.414' }}>
      <canvas ref={canvas} aria-label={`Page ${index + 1}`} />
      {size && highlights.flatMap((h) => h.rects
        .map((r, k) => ({ r, k }))
        .filter(({ r }) => r.page === index)
        .map(({ r, k }) => (
          <button
            key={`${h.id}-${k}`}
            data-hl={k === h.rects.findIndex((x) => x.page === index) ? h.id : undefined}
            className={`hl hl-${h.risk} ${activeId === h.id ? 'is-active' : ''}`}
            style={{
              left: r.x0 * size.scale - 2, top: r.y0 * size.scale - 1,
              width: (r.x1 - r.x0) * size.scale + 4, height: (r.y1 - r.y0) * size.scale + 2,
            }}
            onClick={() => onSelect(h.id)}
            aria-label={h.label}
            title={h.label}
          />
        )))}
      <span className="page-no">{index + 1}</span>
    </div>
  )
}
