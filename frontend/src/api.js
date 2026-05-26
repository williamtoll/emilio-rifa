import { clearToken, getToken } from './auth'

const API = '/api'

function onUnauthorized() {
  clearToken()
  window.location.reload()
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${API}${path}`, { ...options, headers })

  if (res.status === 401 && !path.startsWith('/auth/login')) {
    onUnauthorized()
    throw new Error('Sesión expirada. Inicia sesión de nuevo.')
  }

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

export const authApi = {
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request('/auth/me'),
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
  fetchImage: async (id) => {
    const token = getToken()
    const res = await fetch(`${API}/tickets/${id}/image`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (res.status === 401) {
      onUnauthorized()
      throw new Error('Sesión expirada')
    }
    if (!res.ok) throw new Error('No se pudo cargar la imagen del ticket')
    const blob = await res.blob()
    return URL.createObjectURL(blob)
  },
}
