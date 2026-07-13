import { useCallback, useEffect, useRef, useState } from 'react'
import { publicApi } from '../api'
import { formatGuaranies } from '../utils/currency'
import './PublicPaymentPage.css'

function formatDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString('es-PY', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export default function PublicPaymentPage({ publicId }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [preview, setPreview] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const fileRef = useRef(null)

  const loadStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await publicApi.getPaymentStatus(publicId)
      setStatus(data)
    } catch (e) {
      setError(e.message || 'No se pudo cargar el ticket')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }, [publicId])

  useEffect(() => {
    loadStatus()
  }, [loadStatus])

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview)
    }
  }, [preview])

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (preview) URL.revokeObjectURL(preview)
    setSelectedFile(file || null)
    setPreview(file?.type.startsWith('image/') ? URL.createObjectURL(file) : null)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const file = selectedFile || fileRef.current?.files?.[0]
    if (!file) {
      setError('Seleccioná una imagen del comprobante')
      return
    }
    setUploading(true)
    setError(null)
    try {
      const data = await publicApi.uploadPaymentProof(publicId, file)
      setStatus(data)
      if (preview) URL.revokeObjectURL(preview)
      setPreview(null)
      setSelectedFile(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) {
      setError(err.message || 'No se pudo subir el comprobante')
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div className="payment-page">
        <div className="payment-card payment-center">
          <div className="spinner" />
          <p>Cargando...</p>
        </div>
      </div>
    )
  }

  if (error && !status) {
    return (
      <div className="payment-page">
        <div className="payment-card payment-center">
          <span className="payment-logo">🎟️</span>
          <h1>La Rifa</h1>
          <p className="payment-error">{error}</p>
        </div>
      </div>
    )
  }

  const proofIsPdf = status.payment_proof_url?.toLowerCase().endsWith('.pdf')
  const ticketNumbers = status.ticket_numbers?.length > 0
    ? status.ticket_numbers
    : [status.ticket_number]
  const isMulti = ticketNumbers.length > 1
  const totalPrice = status.total_price ?? status.ticket_price

  return (
    <div className="payment-page">
      <header className="payment-header">
        <span className="payment-logo">🎟️</span>
        <div>
          <h1>Comprobante de pago</h1>
          <p>{status.raffle_name}</p>
        </div>
      </header>

      <div className="payment-card">
        <div className="payment-ticket-info">
          {isMulti ? (
            <div className="payment-ticket-numbers">
              {ticketNumbers.map((num) => (
                <span key={num} className="payment-ticket-number">#{num}</span>
              ))}
            </div>
          ) : (
            <span className="payment-ticket-number">#{status.ticket_number}</span>
          )}
          <span className="payment-ticket-name">{status.buyer_name}</span>
          <span className="payment-ticket-price">
            {isMulti
              ? `${ticketNumbers.length} tickets · Total ${formatGuaranies(totalPrice)}`
              : formatGuaranies(totalPrice)}
          </span>
        </div>

        {status.is_paid ? (
          <div className="payment-done">
            <div className="payment-done-icon">✅</div>
            <h2>Pago confirmado</h2>
            <p>
              {isMulti
                ? 'Tus tickets ya fueron marcados como pagados. Recibirás tus tickets digitales cuando el organizador los envíe.'
                : 'Tu ticket ya fue marcado como pagado. Recibirás tu ticket digital cuando el organizador lo envíe.'}
            </p>
          </div>
        ) : status.has_payment_proof ? (
          <div className="payment-sent">
            <div className="payment-sent-icon">📎</div>
            <h2>Comprobante enviado</h2>
            <p>
              Recibimos tu comprobante
              {status.payment_proof_uploaded_at && (
                <> el {formatDate(status.payment_proof_uploaded_at)}</>
              )}
              . Te confirmaremos el pago a la brevedad.
            </p>
            {status.payment_proof_url && (
              <div className="payment-proof-preview">
                {proofIsPdf ? (
                  <a
                    href={status.payment_proof_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="payment-proof-pdf"
                  >
                    Ver comprobante PDF
                  </a>
                ) : (
                  <img src={status.payment_proof_url} alt="Comprobante de pago" />
                )}
              </div>
            )}
            <p className="payment-replace-hint">¿Enviaste el archivo incorrecto? Podés subir otro:</p>
          </div>
        ) : (
          <div className="payment-instructions">
            <p>
              Realizá la transferencia por <strong>{formatGuaranies(totalPrice)}</strong>
              {isMulti && <> ({ticketNumbers.length} tickets)</>} y
              subí una foto o captura del comprobante para confirmar tu reserva.
            </p>
          </div>
        )}

        {!status.is_paid && (
          <form className="payment-form" onSubmit={handleSubmit}>
            {error && <div className="payment-form-error">{error}</div>}

            <label className="payment-file-label">
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif,application/pdf"
                onChange={handleFileChange}
                disabled={uploading}
              />
              <span className="payment-file-btn">
                {selectedFile ? 'Cambiar archivo' : 'Elegir imagen'}
              </span>
              <span className="payment-file-hint">JPG, PNG, WEBP o PDF · máx. 5 MB</span>
            </label>

            {selectedFile && !preview && (
              <p className="payment-file-selected">{selectedFile.name}</p>
            )}

            {preview && (
              <div className="payment-local-preview">
                <img src={preview} alt="Vista previa" />
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary payment-submit"
              disabled={uploading || !selectedFile}
            >
              {uploading ? 'Enviando...' : status.has_payment_proof ? 'Reemplazar comprobante' : 'Enviar comprobante'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
