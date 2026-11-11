// The TermGuard mark: a round rubber-stamp seal with a shield.
export function Seal({ size = 40, className = '' }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="29" fill="none" stroke="currentColor" strokeWidth="3" />
      <circle cx="32" cy="32" r="23" fill="none" stroke="currentColor" strokeWidth="1.4" strokeDasharray="2 3" />
      <path d="M32 15l13 5v10c0 9-6 16-13 19-7-3-13-10-13-19V20z" fill="currentColor" />
      <path d="M26 32l4 4 8-9" fill="none" stroke="var(--sheet)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// Guilloche: the fine interlaced line pattern printed on Indian stamp paper and currency.
export function Guilloche() {
  const waves = []
  for (let k = 0; k < 6; k++) {
    let d = ''
    for (let x = 0; x <= 400; x += 4) {
      const y = 12 + 9 * Math.sin((x / 400) * Math.PI * 14 + k * 1.05)
      d += `${x === 0 ? 'M' : 'L'}${x},${y.toFixed(2)} `
    }
    waves.push(<path key={k} d={d} />)
  }
  return (
    <svg className="guilloche" viewBox="0 0 400 24" preserveAspectRatio="none" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="0.6">{waves}</g>
    </svg>
  )
}
