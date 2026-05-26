import { useState } from 'react'
import { useTicketImage } from '../hooks/useTicketImage'
import { canShareImage, shareTicketImage } from '../utils/shareTicket'
import './TicketImageModal.css'

export default function TicketImageModal({ ticket, onClose, onNotice, onError }) {
  const isPaid = ticket.is_paid
  const { imageUrl, loading, error } = useTicketImage(ticket.id, isPaid)
  const [sharing, setSharing] = useState(false)

  const handleDownload = () => {
    if (!isPaid || !imageUrl) return
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `ticket-${ticket.ticket_number}.png`
    link.click()
  }

  const handleShare = async () => {
    if (!isPaid || !imageUrl) return
    setSharing(true)
    try {
      const result = await shareTicketImage(
        imageUrl,
        ticket.ticket_number,
        ticket.raffle_name,
      )
      if (result === 'downloaded') {
        onNotice?.('Imagen descargada (tu navegador no admite compartir archivos)')
      } else {
        onNotice?.('Ticket compartido')
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        onError?.(err.message || 'No se pudo compartir la imagen')
      }
    } finally {
      setSharing(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="ticket-image-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-image-modal-header">
          <h2>Ticket #{ticket.ticket_number}</h2>
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
            Cerrar
          </button>
        </div>

        {!isPaid ? (
          <p className="ticket-image-unpaid">
            Este ticket está pendiente de pago. Marcá como pagado para compartir o descargar la imagen.
          </p>
        ) : (
          <>
            {ticket.public_url && (
              <div className="ticket-public-link">
                <input type="text" readOnly value={ticket.public_url} />
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => {
                    navigator.clipboard.writeText(ticket.public_url)
                    onNotice?.('Enlace copiado')
                  }}
                >
                  Copiar
                </button>
              </div>
            )}
            <div className="ticket-image-preview">
              {loading && <p className="ticket-image-status">Cargando imagen...</p>}
              {error && <p className="ticket-image-status error">{error}</p>}
              {imageUrl && <img src={imageUrl} alt={`Ticket ${ticket.ticket_number}`} />}
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleShare}
                disabled={!imageUrl || sharing}
              >
                {sharing ? 'Compartiendo...' : canShareImage() ? 'Compartir imagen' : 'Compartir / Descargar'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleDownload}
                disabled={!imageUrl}
              >
                Descargar PNG
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
