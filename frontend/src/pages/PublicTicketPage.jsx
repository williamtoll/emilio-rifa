import { useEffect, useState } from 'react'
import { publicApi } from '../api'
import { formatGuaranies } from '../utils/currency'
import './PublicTicketPage.css'

export default function PublicTicketPage({ publicId }) {
  const [ticket, setTicket] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let objectUrl = null
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await publicApi.getTicket(publicId)
        if (cancelled) return
        setTicket(data)
        objectUrl = await publicApi.fetchImage(publicId)
        if (!cancelled) setImageUrl(objectUrl)
      } catch (e) {
        if (!cancelled) setError(e.message || 'Ticket no encontrado')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [publicId])

  if (loading) {
    return (
      <div className="public-ticket-page">
        <div className="public-ticket-card">
          <div className="spinner" />
          <p>Cargando ticket...</p>
        </div>
      </div>
    )
  }

  if (error || !ticket) {
    return (
      <div className="public-ticket-page">
        <div className="public-ticket-card">
          <span className="public-logo">🎟️</span>
          <h1>La Rifa</h1>
          <p className="public-error">{error || 'Ticket no disponible'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="public-ticket-page">
      <div className="public-ticket-card">
        <header className="public-header">
          <span className="public-logo">🎟️</span>
          <div>
            <h1>La Rifa</h1>
            <p>{ticket.raffle_name}</p>
          </div>
        </header>

        {imageUrl && (
          <div className="public-ticket-image">
            <img src={imageUrl} alt={`Ticket ${ticket.ticket_number}`} />
          </div>
        )}

        <div className="public-ticket-info">
          <p className="public-ticket-number">#{ticket.ticket_number}</p>
          <p>
            <strong>Participante:</strong> {ticket.buyer_name}
          </p>
          <p>
            <strong>Precio:</strong> {formatGuaranies(ticket.ticket_price)}
          </p>
          <span className="badge badge-paid">Pagado</span>
        </div>

        {ticket.prizes && ticket.prizes.length > 0 && (
          <div className="public-prizes">
            <h2 className="public-prizes-title">🏆 Premios</h2>
            <ul className="public-prizes-list">
              {ticket.prizes.map((prize, idx) => (
                <li key={prize.id} className="public-prize-item">
                  {prize.image_url && (
                    <img
                      src={prize.image_url}
                      alt={prize.name}
                      className="public-prize-img"
                    />
                  )}
                  <div className="public-prize-info">
                    <span className="public-prize-pos">{idx + 1}°</span>
                    <div>
                      <p className="public-prize-name">{prize.name}</p>
                      {prize.description && (
                        <p className="public-prize-desc">{prize.description}</p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
