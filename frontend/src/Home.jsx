import { useEffect, useRef, useState } from 'react'
import { api } from './api.js'
import { Guilloche, Seal } from './Seal.jsx'

export default function Home({ onResult, health, initialError }) {
  const [samples, setSamples] = useState([])
  const [busy, setBusy] = useState('')
  const [error, setError] = useState(initialError || '')
  const [dragging, setDragging] = useState(false)
  const input = useRef(null)

  useEffect(() => { api.samples().then(setSamples).catch(() => {}) }, [])

  async function run(label, fn) {
    setBusy(label); setError('')
    try { onResult(await fn()) } catch (e) { setError(e.message) } finally { setBusy('') }
  }

  const pick = (file) => {
    if (!file) return
    if (file.type && file.type !== 'application/pdf') { setError('Please choose a PDF file.'); return }
    run(file.name, () => api.upload(file))
  }

  const rental = samples.filter((s) => s.kind === 'Rental agreement')
  const offers = samples.filter((s) => s.kind === 'Offer letter')
  const minutes = health?.retention_minutes ?? 60

  return (
    <main className="home">
      <section className="intro">
        <h1>Know what you are signing.</h1>
        <p className="lede">
          Upload a rental agreement or a job offer letter. TermGuard marks the clauses worth questioning,
          explains each one in plain words, and points to the exact line it comes from.
        </p>
        <ul className="promises">
          <li><strong>Every point is quoted.</strong> If a line is not in your document, it is not shown.</li>
          <li><strong>Gaps are listed.</strong> Things a fair agreement should say, but yours does not.</li>
          <li><strong>Private by default.</strong> Names, phone and ID numbers are hidden before any text leaves the server, and the file deletes itself after {minutes} minutes.</li>
        </ul>
      </section>

      <section
        className={`stamp-sheet ${dragging ? 'is-dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files[0]) }}
      >
        <Guilloche />
        <div className="sheet-body">
          <Seal size={88} className={`sheet-seal ${busy ? 'is-busy' : ''}`} />
          {busy ? (
            <>
              <p className="sheet-title">Reading {busy}</p>
              <p className="sheet-sub">Splitting clauses, checking each one, verifying quotes…</p>
            </>
          ) : (
            <>
              <p className="sheet-title">Drop your PDF here</p>
              <p className="sheet-sub">Scanned copies work too{health && !health.ocr_available ? ' once Tesseract OCR is installed' : ''}.</p>
              <button className="btn btn-ink" onClick={() => input.current?.click()}>Choose a PDF</button>
              <input ref={input} type="file" accept="application/pdf" hidden onChange={(e) => pick(e.target.files[0])} />
            </>
          )}
          {error && <p className="sheet-error" role="alert">{error}</p>}
        </div>
        <Guilloche />
      </section>

      <section className="samples" aria-label="Sample documents">
        <h2>No document handy? Try a sample.</h2>
        <p className="muted">All samples are made up: invented names, addresses and amounts.</p>
        <div className="sample-cols">
          {[['Rental agreements', rental], ['Offer letters', offers]].map(([title, list]) => (
            <div key={title}>
              <h3>{title}</h3>
              <ul>
                {list.map((s) => (
                  <li key={s.name}>
                    <button className="sample" disabled={!!busy} onClick={() => run(s.title, () => api.analyzeSample(s.name))}>
                      {s.title.replace(/^(Rental|Offer) /, '')}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <footer className="home-foot">
        <p>
          TermGuard gives general information, not legal advice. Rules differ from state to state.
          {health?.llm_enabled ? ' Explanations use an AI model; every quote is checked against your file.' : ' Running in offline mode with the written checklist.'}
        </p>
      </footer>
    </main>
  )
}
