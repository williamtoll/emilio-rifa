import { useState } from 'react'
import { useTicketImage } from '../hooks/useTicketImage'
import { displayParaguayPhone } from '../utils/phone'
import { shareTicketImage } from '../utils/shareTicket'
import { buildTicketShareText } from '../utils/socialShare'
import SocialShareButtons from './SocialShareButtons'
import TicketImageModal from './TicketImageModal'
import PaymentProofModal from './PaymentProofModal'
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
  const [showProof, setShowProof] = useState(false)
  const [sharing, setSharing] = useState(false)
  const isPaid = ticket.is_paid
  const { imageUrl, loading: imageLoading } = useTicketImage(ticket.id, isPaid)
  const isEmailLoading = loading === `email-${ticket.id}`
  const isWaLoading = loading === `wa-${ticket.id}`
  const isPaidLoading = loading === `paid-${ticket.id}`
  const ticketUrl = ticket.short_url || ticket.public_url
  const shareText = ticketUrl
    ? buildTicketShareText(ticket.ticket_number, ticket.raffle_name, ticketUrl)
    : null

  const handleShare = async () => {
    if (!isPaid) {
      onError?.('El ticket debe estar pagado para compartir la imagen')
      return
    }
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
      <article className={`ticket-card ${isPaid ? 'paid' : 'unpaid'}`}>
        <button
          type="button"
          className="ticket-thumb"
          onClick={() => setShowImage(true)}
          title={isPaid ? 'Ver imagen del ticket' : 'Ver detalle del ticket'}
        >
          {isPaid && imageLoading && <span className="ticket-thumb-loading">...</span>}
          {isPaid && imageUrl && <img src={imageUrl} alt="" />}
          {!isPaid && <span className="ticket-thumb-pending">Pendiente</span>}
        </button>
        <div className="ticket-number">#{ticket.ticket_number}</div>
        <div className="ticket-body">
          <h3>{ticket.buyer_name}</h3>
          <div className="ticket-contact">
            {ticket.buyer_phone && <span>📱 {displayParaguayPhone(ticket.buyer_phone)}</span>}
            {ticket.buyer_email && <span>✉️ {ticket.buyer_email}</span>}
          </div>
          <div className="ticket-badges">
            <span className={`badge ${isPaid ? 'badge-paid' : 'badge-unpaid'}`}>
              {isPaid ? 'Pagado' : 'Pendiente'}
            </span>
            {!isPaid && ticket.has_payment_proof && (
              <span className="badge badge-proof">Comprobante enviado</span>
            )}
          </div>
        </div>
        <div className="ticket-actions">
          {!isPaid && ticket.has_payment_proof && (
            <button type="button" className="btn btn-sm btn-secondary" onClick={() => setShowProof(true)}>
              Ver comprobante
            </button>
          )}
          <button type="button" className="btn btn-sm btn-secondary" onClick={() => setShowImage(true)}>
            Ver ticket
          </button>
          {isPaid && (
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={handleShare}
              disabled={sharing || imageLoading}
            >
              {sharing ? '...' : 'Compartir'}
            </button>
          )}
          <button
            className={`btn btn-sm ${isPaid ? 'btn-warning' : 'btn-success'}`}
            onClick={onTogglePaid}
            disabled={isPaidLoading}
          >
            {isPaidLoading ? '...' : isPaid ? 'Marcar pendiente' : 'Marcar pagado'}
          </button>
          {isPaid && ticket.buyer_phone && (
            <button className="btn btn-sm btn-whatsapp" onClick={onWhatsApp} disabled={isWaLoading}>
              {isWaLoading ? '...' : 'WhatsApp'}
            </button>
          )}
          {isPaid && ticketUrl && (
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => {
                navigator.clipboard.writeText(ticketUrl)
                onNotice?.('Enlace copiado')
              }}
            >
              Copiar link
            </button>
          )}
          {isPaid && ticketUrl && shareText && (
            <SocialShareButtons
              url={ticketUrl}
              text={shareText}
              imageUrl={imageUrl}
              imageFilename={`ticket-${ticket.ticket_number}.png`}
              onNotice={onNotice}
              onError={onError}
            />
          )}
          {ticket.buyer_email && (
            <button className="btn btn-sm btn-secondary" onClick={onSendEmail} disabled={isEmailLoading}>
              {isEmailLoading ? '...' : 'Correo'}
            </button>
          )}
        </div>
      </article>
      {showProof && (
        <PaymentProofModal ticket={ticket} onClose={() => setShowProof(false)} />
      )}
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
