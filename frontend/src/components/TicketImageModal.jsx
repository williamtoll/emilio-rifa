import { ticketsApi } from '../api'
import './TicketImageModal.css'

export default function TicketImageModal({ ticket, onClose }) {
  const imageUrl = ticketsApi.imageUrl(ticket.id)
  const downloadUrl = `${imageUrl}?t=${Date.now()}`

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = downloadUrl
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
          <img src={imageUrl} alt={`Ticket ${ticket.ticket_number}`} />
        </div>
        <p className="ticket-image-hint">El código QR contiene los datos del ticket para verificación.</p>
        <div className="modal-actions">
          <a href={downloadUrl} download={`ticket-${ticket.ticket_number}.png`} className="btn btn-primary">
            Descargar imagen
          </a>
          <button type="button" className="btn btn-secondary" onClick={handleDownload}>
            Guardar PNG
          </button>
        </div>
      </div>
    </div>
  )
}
