import { useState } from 'react'
import { useTicketImage } from '../hooks/useTicketImage'
import { displayParaguayPhone } from '../utils/phone'
import { shareTicketImage } from '../utils/shareTicket'
import TicketImageModal from './TicketImageModal'
import './TicketCard.css'

export default function TicketCard({
  ticket,
  loading,
  onTogglePaid,
  onSendEmail,
  onWhatsApp,
  onNotice,
  onError,
}) {
  const [showImage, setShowImage] = useState(false)
  const [sharing, setSharing] = useState(false)
  const { imageUrl, loading: imageLoading } = useTicketImage(ticket.id)
  const isEmailLoading = loading === `email-${ticket.id}`
  const isWaLoading = loading === `wa-${ticket.id}`
  const isPaidLoading = loading === `paid-${ticket.id}`

  const handleShare = async () => {
    if (!imageUrl) {
      setShowImage(true)
      return
    }
    setSharing(true)
    try {
      const result = await shareTicketImage(
        imageUrl,
        ticket.ticket_number,
        ticket.raffle_name,
      )
      if (result === 'downloaded') {
        onNotice?.('Imagen descargada')
      } else {
        onNotice?.('Ticket compartido')
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        onError?.(err.message || 'No se pudo compartir')
      }
    } finally {
      setSharing(false)
    }
  }

  return (
    <>
      <article className={`ticket-card ${ticket.is_paid ? 'paid' : 'unpaid'}`}>
        <button
          type="button"
          className="ticket-thumb"
          onClick={() => setShowImage(true)}
          title="Ver imagen del ticket"
        >
          {imageLoading && <span className="ticket-thumb-loading">...</span>}
          {imageUrl && <img src={imageUrl} alt="" />}
        </button>
        <div className="ticket-number">#{ticket.ticket_number}</div>
        <div className="ticket-body">
          <h3>{ticket.buyer_name}</h3>
          <div className="ticket-contact">
            {ticket.buyer_phone && <span>📱 {displayParaguayPhone(ticket.buyer_phone)}</span>}
            {ticket.buyer_email && <span>✉️ {ticket.buyer_email}</span>}
          </div>
          <span className={`badge ${ticket.is_paid ? 'badge-paid' : 'badge-unpaid'}`}>
            {ticket.is_paid ? 'Pagado' : 'Pendiente'}
          </span>
        </div>
        <div className="ticket-actions">
          <button type="button" className="btn btn-sm btn-secondary" onClick={() => setShowImage(true)}>
            Ver ticket
          </button>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={handleShare}
            disabled={sharing || imageLoading}
          >
            {sharing ? '...' : 'Compartir'}
          </button>
          <button
            className={`btn btn-sm ${ticket.is_paid ? 'btn-warning' : 'btn-success'}`}
            onClick={onTogglePaid}
            disabled={isPaidLoading}
          >
            {isPaidLoading ? '...' : ticket.is_paid ? 'Marcar pendiente' : 'Marcar pagado'}
          </button>
          {ticket.buyer_phone && (
            <button className="btn btn-sm btn-whatsapp" onClick={onWhatsApp} disabled={isWaLoading}>
              {isWaLoading ? '...' : 'WhatsApp'}
            </button>
          )}
          {ticket.buyer_email && (
            <button className="btn btn-sm btn-secondary" onClick={onSendEmail} disabled={isEmailLoading}>
              {isEmailLoading ? '...' : 'Correo'}
            </button>
          )}
        </div>
      </article>
      {showImage && (
        <TicketImageModal
          ticket={ticket}
          onClose={() => setShowImage(false)}
          onNotice={onNotice}
          onError={onError}
        />
      )}
    </>
  )
}
