import { useEffect, useState } from 'react'
import { ticketsApi } from '../api'
import './PaymentProofModal.css'

export default function PaymentProofModal({ ticket, onClose }) {
  const [proofUrl, setProofUrl] = useState(null)
  const [isPdf, setIsPdf] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let objectUrl = null
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const { url, isPdf: pdf } = await ticketsApi.fetchPaymentProof(ticket.id)
        if (cancelled) return
        objectUrl = url
        setProofUrl(url)
        setIsPdf(pdf)
      } catch (e) {
        if (!cancelled) setError(e.message || 'No se pudo cargar el comprobante')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [ticket.id])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="payment-proof-modal" onClick={(e) => e.stopPropagation()}>
        <div className="payment-proof-modal-header">
          <h2>Comprobante · #{ticket.ticket_number}</h2>
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
            Cerrar
          </button>
        </div>
        <p className="payment-proof-modal-buyer">{ticket.buyer_name}</p>
        <div className="payment-proof-modal-preview">
          {loading && <p className="payment-proof-status">Cargando...</p>}
          {error && <p className="payment-proof-status error">{error}</p>}
          {proofUrl && !isPdf && <img src={proofUrl} alt={`Comprobante ${ticket.ticket_number}`} />}
          {proofUrl && isPdf && (
            <iframe src={proofUrl} title="Comprobante PDF" className="payment-proof-pdf-frame" />
          )}
        </div>
        {proofUrl && (
          <div className="modal-actions">
            <a href={proofUrl} download={`comprobante-${ticket.ticket_number}`} className="btn btn-secondary">
              Descargar
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
