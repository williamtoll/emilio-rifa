import { useTicketImage } from '../hooks/useTicketImage'
import './TicketImageModal.css'

export default function TicketImageModal({ ticket, onClose }) {
  const { imageUrl, loading, error } = useTicketImage(ticket.id)

  const handleDownload = () => {
    if (!imageUrl) return
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `ticket-${ticket.ticket_number}.png`
    link.click()
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
        <div className="ticket-image-preview">
          {loading && <p className="ticket-image-status">Cargando imagen...</p>}
          {error && <p className="ticket-image-status error">{error}</p>}
          {imageUrl && <img src={imageUrl} alt={`Ticket ${ticket.ticket_number}`} />}
        </div>
        <p className="ticket-image-hint">El código QR contiene los datos del ticket para verificación.</p>
        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={!imageUrl}
          >
            Descargar imagen
          </button>
        </div>
      </div>
    </div>
  )
}
