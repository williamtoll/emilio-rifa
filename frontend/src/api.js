const API = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg || d).join(', ')
      : detail || 'Error en la solicitud'
    throw new Error(message)
  }
  if (res.status === 204) return null
  return res.json()
}

export const rafflesApi = {
  list: () => request('/raffles'),
  get: (id) => request(`/raffles/${id}`),
  create: (data) => request('/raffles', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/raffles/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => request(`/raffles/${id}`, { method: 'DELETE' }),
}

export const ticketsApi = {
  list: (raffleId) => request(`/tickets${raffleId ? `?raffle_id=${raffleId}` : ''}`),
  create: (data) => request('/tickets', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  markPaid: (id) => request(`/tickets/${id}/mark-paid`, { method: 'POST' }),
  markUnpaid: (id) => request(`/tickets/${id}/mark-unpaid`, { method: 'POST' }),
  sendEmail: (id, message) =>
    request(`/tickets/${id}/send-email`, {
      method: 'POST',
      body: JSON.stringify({ message: message || null }),
    }),
  whatsappLink: (id, message) => {
    const params = message ? `?message=${encodeURIComponent(message)}` : ''
    return request(`/tickets/${id}/whatsapp-link${params}`)
  },
  imageUrl: (id) => `${API}/tickets/${id}/image`,
}
