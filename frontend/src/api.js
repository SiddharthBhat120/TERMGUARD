async function request(path, options = {}) {
  const res = await fetch(path, options)
  if (!res.ok) {
    let detail = `The server answered ${res.status}.`
    try {
      const body = await res.json()
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch { /* not JSON */ }
    throw new Error(detail)
  }
  return res.headers.get('content-type')?.includes('application/json') ? res.json() : res
}

export const api = {
  health: () => request('/api/health'),
  samples: () => request('/api/samples'),
  analyzeSample: (name) => request(`/api/samples/${encodeURIComponent(name)}`, { method: 'POST' }),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/api/documents', { method: 'POST', body: form })
  },
  get: (id) => request(`/api/documents/${id}`),
  remove: (id) => request(`/api/documents/${id}`, { method: 'DELETE' }),
  checklist: (type) => request(`/api/checklist/${type}`),
  fileUrl: (id) => `/api/documents/${id}/file`,
  reportUrl: (id) => `/api/documents/${id}/report.pdf`,
}
