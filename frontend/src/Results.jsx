import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api.js'
import PdfViewer from './PdfViewer.jsx'

const RISK_LABEL = { high: 'High', medium: 'Medium', low: 'Low' }
const LANGS = [['en', 'English'], ['hi', 'हिंदी'], ['kn', 'ಕನ್ನಡ']]

function verdict(a) {
  const n = a.findings.length
  if (a.counts.high > 0) return { tone: 'high', text: `${n} clause${n === 1 ? '' : 's'} to question` }
  if (n > 0) return { tone: 'medium', text: `${n} point${n === 1 ? '' : 's'} to check` }
  return { tone: 'low', text: 'Nothing flagged' }
}

export default function Results({ analysis: a, onHome }) {
  const [active, setActive] = useState(null)
  const [signal, setSignal] = useState(0)
  const [tab, setTab] = useState('findings')
  const [lang, setLang] = useState('en')
  const [filter, setFilter] = useState('all')
  const [lawyer, setLawyer] = useState([])
  const [deleting, setDeleting] = useState(false)
  const list = useRef(null)
  const v = verdict(a)

  useEffect(() => { api.checklist(a.doc_type).then((c) => setLawyer(c.lawyer)).catch(() => {}) }, [a.doc_type])

  const highlights = useMemo(() => [
    ...a.findings.map((f) => ({ id: f.id, risk: f.risk, rects: f.rects, label: `${RISK_LABEL[f.risk]} risk: ${f.name}` })),
    ...a.facts.map((f) => ({ id: `fact-${f.key}`, risk: 'fact', rects: f.rects, label: `${f.label}: ${f.value}` })),
  ], [a])

  const shown = a.findings.filter((f) => filter === 'all' || f.risk === filter)
  const minutesLeft = Math.max(0, Math.round((a.expires_at * 1000 - Date.now()) / 60000))

  const selectFromPdf = (id) => {
    setActive(id)
    if (id.startsWith('fact-')) return
    setTab('findings'); setFilter('all')
    requestAnimationFrame(() => list.current?.querySelector(`[data-finding="${id}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }))
  }
  const selectFromList = (id) => { setActive(id); setSignal((s) => s + 1) }

  async function remove() {
    if (!window.confirm('Delete this document and its analysis from the server now?')) return
    setDeleting(true)
    try { await api.remove(a.id) } finally { onHome() }
  }

  return (
    <main className="results">
      <section className="summary">
        <div className="summary-head">
          <div>
            <p className="doc-kind">{a.doc_type_label}</p>
            <h1 className="doc-name">{a.filename}</h1>
            <p className="doc-meta">
              {a.clauses.length} clauses read and {a.engine === 'llm' ? 'checked by AI, with every quote verified' : 'checked against the written checklist'}.
              {a.ocr_used ? ' Scanned pages were read with OCR.' : ''}
            </p>
          </div>
          <div className={`verdict verdict-${v.tone}`} role="status">{v.text}</div>
        </div>

        <div className="ledger">
          <div className="ledger-facts">
            {a.facts.length === 0 && <p className="muted">No amounts or periods were found in a form TermGuard can quote.</p>}
            {a.facts.map((f) => (
              <button key={f.key} className={`fact ${active === `fact-${f.key}` ? 'is-active' : ''}`}
                onClick={() => selectFromList(`fact-${f.key}`)} title={f.quote}>
                <span className="fact-label">{f.label}</span>
                <span className="fact-value">{f.value}</span>
              </button>
            ))}
          </div>
          <div className="counts" aria-label="Findings by risk">
            {['high', 'medium', 'low'].map((r) => (
              <button key={r} className={`count count-${r} ${filter === r ? 'is-on' : ''}`}
                onClick={() => { setTab('findings'); setFilter(filter === r ? 'all' : r) }}>
                <strong>{a.counts[r]}</strong> {RISK_LABEL[r].toLowerCase()}
              </button>
            ))}
            <button className={`count count-missing ${tab === 'missing' ? 'is-on' : ''}`} onClick={() => setTab('missing')}>
              <strong>{a.missing.length}</strong> not mentioned
            </button>
          </div>
        </div>

        <div className="actions">
          <div className="lang" role="group" aria-label="Explanation language">
            {LANGS.map(([code, label]) => (
              <button key={code} className={lang === code ? 'is-on' : ''} onClick={() => setLang(code)} lang={code}>{label}</button>
            ))}
          </div>
          <a className="btn btn-ghost" href={api.reportUrl(a.id)}>Export report (PDF)</a>
          <button className="btn btn-ghost" onClick={onHome}>Check another document</button>
          <button className="btn btn-danger" onClick={remove} disabled={deleting}>{deleting ? 'Deleting…' : 'Delete now'}</button>
        </div>
      </section>

      <div className="panes">
        <PdfViewer url={api.fileUrl(a.id)} highlights={highlights} activeId={active} scrollSignal={signal} onSelect={selectFromPdf} />

        <aside className="panel">
          <div className="tabs" role="tablist">
            {[['findings', `Clauses to question (${a.findings.length})`], ['missing', `Not mentioned (${a.missing.length})`], ['lawyer', 'When to see a lawyer']].map(([id, label]) => (
              <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'is-on' : ''} onClick={() => setTab(id)}>{label}</button>
            ))}
          </div>

          <div className="panel-body" ref={list}>
            {tab === 'findings' && (
              <>
                {filter !== 'all' && <p className="filter-note">Showing {filter} risk only. <button className="link" onClick={() => setFilter('all')}>Show all</button></p>}
                {shown.length === 0 && <p className="empty">Nothing from the checklist was flagged. Still read every clause before you sign.</p>}
                {shown.map((f) => (
                  <Finding key={f.id} f={f} lang={lang} active={active === f.id} onClick={() => selectFromList(f.id)} />
                ))}
              </>
            )}
            {tab === 'missing' && (
              <>
                <p className="panel-intro">A fair {a.doc_type === 'rental' ? 'agreement' : 'offer letter'} usually covers these. Yours does not mention them, so ask before you sign.</p>
                {a.missing.length === 0 && <p className="empty">Everything on the expected list is mentioned somewhere.</p>}
                {a.missing.map((m) => (
                  <article key={m.id} className="missing">
                    <h3>{m.name}</h3>
                    <p>{m.why}</p>
                    <p className="ask"><span>Ask</span> {m.question}</p>
                  </article>
                ))}
              </>
            )}
            {tab === 'lawyer' && (
              <>
                <p className="panel-intro">TermGuard helps you ask better questions. Talk to a lawyer, or your state's rent or labour authority, if:</p>
                <ul className="lawyer-list">{lawyer.map((l) => <li key={l}>{l}</li>)}</ul>
                <p className="disclaimer">{a.disclaimer}</p>
              </>
            )}
          </div>

          <p className="privacy">
            {a.redactions} personal detail{a.redactions === 1 ? ' was' : 's were'} hidden before analysis.
            This file deletes itself in {minutesLeft} min.
            {a.dropped_unverified > 0 ? ` ${a.dropped_unverified} finding${a.dropped_unverified === 1 ? '' : 's'} without a matching quote ${a.dropped_unverified === 1 ? 'was' : 'were'} removed.` : ''}
          </p>
        </aside>
      </div>
    </main>
  )
}

function Finding({ f, lang, active, onClick }) {
  const text = (lang === 'hi' && f.explanation_hi) || (lang === 'kn' && f.explanation_kn) || f.explanation
  return (
    <article data-finding={f.id} className={`finding finding-${f.risk} ${active ? 'is-active' : ''}`}>
      <button className="finding-main" onClick={onClick} aria-pressed={active}>
        <span className="finding-top">
          <span className={`risk risk-${f.risk}`}>{RISK_LABEL[f.risk]}</span>
          <span className="finding-clause">{f.clause_title}</span>
        </span>
        <span className="finding-name">{f.name}</span>
        <q className="quote">{f.quote}</q>
      </button>
      <p className="explain" lang={lang}>{text}</p>
      <p className="ask"><span>Ask</span> {f.question}</p>
      <details>
        <summary>Why it matters</summary>
        <p>{f.why}</p>
      </details>
    </article>
  )
}
