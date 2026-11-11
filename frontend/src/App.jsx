import { useEffect, useState } from 'react'
import { api } from './api.js'
import Home from './Home.jsx'
import Results from './Results.jsx'
import { Seal } from './Seal.jsx'

function useHashId() {
  const read = () => (window.location.hash.match(/^#\/doc\/([a-f0-9]+)/) || [])[1] || null
  const [id, setId] = useState(read)
  useEffect(() => {
    const on = () => setId(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return id
}

export default function App() {
  const docId = useHashId()
  const [analysis, setAnalysis] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { api.health().then(setHealth).catch(() => setHealth({ ok: false })) }, [])

  useEffect(() => {
    if (!docId) { setAnalysis(null); return }
    if (analysis?.id === docId) return
    api.get(docId).then(setAnalysis).catch((e) => { setError(e.message); window.location.hash = '' })
  }, [docId]) // eslint-disable-line react-hooks/exhaustive-deps

  const open = (a) => { setError(''); setAnalysis(a); window.location.hash = `#/doc/${a.id}` }
  const home = () => { setAnalysis(null); window.location.hash = '' }

  return (
    <div className="app">
      <header className="topbar">
        <a href="#" className="brand" onClick={(e) => { e.preventDefault(); home() }}>
          <Seal size={30} />
          <span>TermGuard</span>
        </a>
        <p className="topbar-note">Information, not legal advice</p>
      </header>
      {docId && analysis
        ? <Results analysis={analysis} onHome={home} />
        : docId
          ? <main className="loading-page"><p>Opening the analysis…</p></main>
          : <Home onResult={open} health={health} initialError={error} />}
    </div>
  )
}
