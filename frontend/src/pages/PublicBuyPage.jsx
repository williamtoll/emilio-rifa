import { useCallback, useEffect, useMemo, useState } from 'react'
import { publicApi } from '../api'
import { formatGuaranies } from '../utils/currency'
import {
  formatParaguayPhoneInput,
  isValidParaguayPhone,
  normalizeParaguayPhone,
} from '../utils/phone'
import './PublicBuyPage.css'

function padNum(n) {
  return String(n).padStart(4, '0')
}

export default function PublicBuyPage({ raffleId: initialRaffleId }) {
  const [raffles, setRaffles] = useState([])
  const [raffle, setRaffle] = useState(null)
  const [taken, setTaken] = useState(new Set())
  const [maxTickets, setMaxTickets] = useState(100)
  const [selectedId, setSelectedId] = useState(initialRaffleId ? Number(initialRaffleId) : null)
  const [selectedNumber, setSelectedNumber] = useState(null)
  const [search, setSearch] = useState('')
  const [showAvailableOnly, setShowAvailableOnly] = useState(false)
  const [buyerName, setBuyerName] = useState('')
  const [buyerPhone, setBuyerPhone] = useState('')
  const [buyerEmail, setBuyerEmail] = useState('')
  const [phoneError, setPhoneError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [confirmation, setConfirmation] = useState(null)

  const loadRaffleList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await publicApi.listRaffles()
      setRaffles(data)
      if (data.length === 1 && !initialRaffleId) {
        setSelectedId(data[0].id)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [initialRaffleId])

  const loadRaffleDetail = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    setConfirmation(null)
    setSelectedNumber(null)
    try {
      const [detail, availability] = await Promise.all([
        publicApi.getRaffle(id),
        publicApi.getAvailability(id),
      ])
      setRaffle(detail)
      setTaken(new Set(availability.taken))
      setMaxTickets(availability.max_tickets)
    } catch (e) {
      setError(e.message)
      setRaffle(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedId) {
      loadRaffleDetail(selectedId)
      window.history.replaceState(null, '', `/comprar/${selectedId}`)
    } else {
      loadRaffleList()
      window.history.replaceState(null, '', '/comprar')
    }
  }, [selectedId, loadRaffleDetail, loadRaffleList])

  const numbers = useMemo(() => {
    const list = []
    for (let i = 1; i <= maxTickets; i++) {
      const num = padNum(i)
      const isTaken = taken.has(num)
      if (showAvailableOnly && isTaken) continue
      if (search.trim()) {
        const q = search.trim()
        if (!num.includes(q) && !String(i).includes(q)) continue
      }
      list.push({ num, isTaken })
    }
    return list
  }, [maxTickets, taken, showAvailableOnly, search])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedNumber) {
      setError('Elegí un número de ticket')
      return
    }
    if (buyerPhone && !isValidParaguayPhone(buyerPhone)) {
      setPhoneError('Ingresá un móvil válido: 09XXXXXXXX')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const result = await publicApi.reserveTicket(selectedId, {
        ticket_number: selectedNumber,
        buyer_name: buyerName,
        buyer_phone: normalizeParaguayPhone(buyerPhone),
        buyer_email: buyerEmail || null,
      })
      setConfirmation(result)
      setTaken((prev) => new Set([...prev, selectedNumber]))
      setSelectedNumber(null)
    } catch (e) {
      setError(e.message)
      await loadRaffleDetail(selectedId)
    } finally {
      setSubmitting(false)
    }
  }

  if (confirmation) {
    return (
      <div className="buy-page">
        <div className="buy-card buy-success">
          <div className="buy-success-icon">✅</div>
          <h1>¡Número reservado!</h1>
          <p className="buy-success-raffle">{confirmation.raffle_name}</p>
          <div className="buy-success-number">#{confirmation.ticket_number}</div>
          <p className="buy-success-name">{confirmation.buyer_name}</p>
          <p className="buy-success-price">{formatGuaranies(confirmation.ticket_price)}</p>
          <p className="buy-success-msg">{confirmation.message}</p>
          <div className="buy-success-actions">
            {confirmation.public_id && (
              <a
                href={`/comprobante/${confirmation.public_id}`}
                className="btn btn-primary"
              >
                Enviar comprobante de pago
              </a>
            )}
            <button type="button" className="btn btn-secondary" onClick={() => setConfirmation(null)}>
              Elegir otro número
            </button>
            {raffles.length > 1 && (
              <button type="button" className="btn btn-secondary" onClick={() => { setSelectedId(null); setConfirmation(null) }}>
                Ver otros sorteos
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!selectedId) {
    return (
      <div className="buy-page">
        <header className="buy-header">
          <span className="buy-logo">🎟️</span>
          <div>
            <h1>La Rifa</h1>
            <p>Elegí tu número de ticket</p>
          </div>
        </header>

        {loading && (
          <div className="buy-center">
            <div className="spinner" />
          </div>
        )}

        {error && !loading && <div className="buy-error">{error}</div>}

        {!loading && !error && raffles.length === 0 && (
          <div className="buy-empty">No hay sorteos disponibles en este momento.</div>
        )}

        <div className="buy-raffle-list">
          {raffles.map((r) => (
            <button key={r.id} type="button" className="buy-raffle-card" onClick={() => setSelectedId(r.id)}>
              {r.image_url && <img src={r.image_url} alt="" className="buy-raffle-card-img" />}
              <div className="buy-raffle-card-body">
                <h2>{r.name}</h2>
                {r.description && <p>{r.description}</p>}
                <div className="buy-raffle-card-meta">
                  <span>{formatGuaranies(r.ticket_price)}</span>
                  <span>{r.tickets_available} disponibles</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="buy-page">
      <header className="buy-header">
        <button type="button" className="buy-back" onClick={() => setSelectedId(null)}>← Sorteos</button>
        <div className="buy-header-title">
          <h1>{raffle?.name || 'Cargando...'}</h1>
          {raffle && <p>{formatGuaranies(raffle.ticket_price)} por ticket</p>}
        </div>
      </header>

      {loading && (
        <div className="buy-center">
          <div className="spinner" />
        </div>
      )}

      {error && <div className="buy-error">{error}</div>}

      {!loading && raffle && (
        <div className="buy-content">
          {raffle.image_url && (
            <img src={raffle.image_url} alt={raffle.name} className="buy-raffle-banner" />
          )}

          {raffle.description && <p className="buy-desc">{raffle.description}</p>}

          {raffle.prizes?.length > 0 && (
            <div className="buy-prizes">
              <h3>Premios</h3>
              <ul>
                {raffle.prizes.map((p) => (
                  <li key={p.id}>
                    {p.image_url && <img src={p.image_url} alt="" />}
                    <span>{p.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="buy-picker">
            <div className="buy-picker-toolbar">
              <input
                type="search"
                placeholder="Buscar número..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="buy-search"
              />
              <label className="buy-filter">
                <input
                  type="checkbox"
                  checked={showAvailableOnly}
                  onChange={(e) => setShowAvailableOnly(e.target.checked)}
                />
                Solo disponibles
              </label>
            </div>

            <p className="buy-picker-hint">
              {taken.size} vendidos · {maxTickets - taken.size} disponibles de {maxTickets}
            </p>

            <div className="buy-number-grid">
              {numbers.map(({ num, isTaken }) => (
                <button
                  key={num}
                  type="button"
                  disabled={isTaken}
                  className={`buy-number ${isTaken ? 'buy-number--taken' : ''} ${selectedNumber === num ? 'buy-number--selected' : ''}`}
                  onClick={() => setSelectedNumber(num)}
                >
                  {num}
                </button>
              ))}
            </div>

            {numbers.length === 0 && (
              <p className="buy-no-results">No hay números que coincidan con tu búsqueda.</p>
            )}
          </div>

          <form className="buy-form" onSubmit={handleSubmit}>
            <h3>Tus datos</h3>
            {selectedNumber ? (
              <p className="buy-selected-label">
                Número elegido: <strong>#{selectedNumber}</strong>
              </p>
            ) : (
              <p className="buy-selected-label buy-selected-label--empty">Seleccioná un número arriba</p>
            )}

            <div className="form-group">
              <label>Nombre completo *</label>
              <input
                value={buyerName}
                onChange={(e) => setBuyerName(e.target.value)}
                placeholder="Tu nombre"
                required
              />
            </div>
            <div className="form-group">
              <label>Teléfono móvil (Paraguay)</label>
              <input
                type="tel"
                inputMode="numeric"
                value={buyerPhone}
                onChange={(e) => { setPhoneError(null); setBuyerPhone(formatParaguayPhoneInput(e.target.value)) }}
                placeholder="0961732207"
                maxLength={10}
              />
              {phoneError && <p className="field-error">{phoneError}</p>}
            </div>
            <div className="form-group">
              <label>Correo electrónico</label>
              <input
                type="email"
                value={buyerEmail}
                onChange={(e) => setBuyerEmail(e.target.value)}
                placeholder="correo@ejemplo.com"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary buy-submit"
              disabled={submitting || !selectedNumber}
            >
              {submitting ? 'Reservando...' : `Reservar ticket ${selectedNumber ? `#${selectedNumber}` : ''}`}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
