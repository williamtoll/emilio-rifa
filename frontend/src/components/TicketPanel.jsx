import { useState } from 'react'
import TicketCard from './TicketCard'
import { formatGuaranies } from '../utils/currency'
import {
  formatParaguayPhoneInput,
  isValidParaguayPhone,
  normalizeParaguayPhone,
} from '../utils/phone'
import './TicketPanel.css'

export default function TicketPanel({
  raffle,
  tickets,
  onCreateTicket,
  onTogglePaid,
  onSendEmail,
  onWhatsApp,
  onError,
}) {
  const [showForm, setShowForm] = useState(false)
  const [buyerName, setBuyerName] = useState('')
  const [buyerPhone, setBuyerPhone] = useState('')
  const [buyerEmail, setBuyerEmail] = useState('')
  const [saving, setSaving] = useState(false)
  const [phoneError, setPhoneError] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)

  const handlePhoneChange = (e) => {
    setPhoneError(null)
    setBuyerPhone(formatParaguayPhoneInput(e.target.value))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (buyerPhone && !isValidParaguayPhone(buyerPhone)) {
      setPhoneError('Ingresá un móvil válido: 09XXXXXXXX (10 dígitos)')
      return
    }
    setSaving(true)
    try {
      await onCreateTicket({
        buyer_name: buyerName,
        buyer_phone: normalizeParaguayPhone(buyerPhone),
        buyer_email: buyerEmail || null,
      })
      setBuyerName('')
      setBuyerPhone('')
      setBuyerEmail('')
      setShowForm(false)
    } catch (err) {
      onError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const runAction = async (key, fn) => {
    setActionLoading(key)
    try {
      await fn()
    } catch (err) {
      onError(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  if (!raffle) {
    return (
      <main className="ticket-panel empty">
        <p>Selecciona o crea un sorteo para comenzar.</p>
      </main>
    )
  }

  const unpaid = tickets.filter((t) => !t.is_paid).length
  const paid = tickets.filter((t) => t.is_paid).length

  return (
    <main className="ticket-panel">
      <div className="panel-header">
        <div>
          <h2>{raffle.name}</h2>
          {raffle.description && <p className="panel-desc">{raffle.description}</p>}
          <div className="panel-meta">
            <span>Precio: {formatGuaranies(raffle.ticket_price)}</span>
            <span>{tickets.length} tickets</span>
            <span className="paid-count">{paid} pagados</span>
            <span className="unpaid-count">{unpaid} pendientes</span>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Generar ticket
        </button>
      </div>

      <div className="ticket-grid">
        {tickets.length === 0 ? (
          <div className="no-tickets">
            <p>No hay tickets en este sorteo.</p>
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              Generar el primero
            </button>
          </div>
        ) : (
          tickets.map((ticket) => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
              loading={actionLoading}
              onTogglePaid={() => runAction(`paid-${ticket.id}`, () => onTogglePaid(ticket))}
              onSendEmail={() => runAction(`email-${ticket.id}`, () => onSendEmail(ticket.id))}
              onWhatsApp={() => runAction(`wa-${ticket.id}`, () => onWhatsApp(ticket.id))}
            />
          ))
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nuevo ticket — {raffle.name}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombre del participante *</label>
                <input
                  value={buyerName}
                  onChange={(e) => setBuyerName(e.target.value)}
                  placeholder="Nombre completo"
                  required
                />
              </div>
              <div className="form-group">
                <label>Teléfono móvil (Paraguay)</label>
                <input
                  type="tel"
                  inputMode="numeric"
                  value={buyerPhone}
                  onChange={handlePhoneChange}
                  placeholder="0961732207"
                  maxLength={10}
                  pattern="09[0-9]{8}"
                  title="Formato: 09XXXXXXXX"
                />
                {phoneError && <p className="field-error">{phoneError}</p>}
                <p className="field-hint">Formato: 09 + 8 dígitos (ej. 0961732207)</p>
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
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Generando...' : 'Generar ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  )
}
