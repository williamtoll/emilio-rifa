import { useState } from 'react'
import './RaffleSidebar.css'

export default function RaffleSidebar({ raffles, selectedId, onSelect, onCreate, onError }) {
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [ticketPrice, setTicketPrice] = useState('50000')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onCreate({
        name,
        description: description || null,
        ticket_price: parseFloat(ticketPrice) || 0,
        is_active: true,
      })
      setName('')
      setDescription('')
      setTicketPrice('50000')
      setShowForm(false)
    } catch (err) {
      onError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <aside className="raffle-sidebar">
      <div className="sidebar-header">
        <h2>Sorteos</h2>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
          + Nuevo
        </button>
      </div>

      <ul className="raffle-list">
        {raffles.length === 0 && (
          <li className="raffle-empty">No hay sorteos. Crea el primero.</li>
        )}
        {raffles.map((r) => (
          <li key={r.id}>
            <button
              className={`raffle-item ${selectedId === r.id ? 'active' : ''}`}
              onClick={() => onSelect(r.id)}
            >
              <span className="raffle-name">{r.name}</span>
              <span className="raffle-stats">
                {r.ticket_count} tickets · {r.paid_count} pagados
              </span>
              {!r.is_active && <span className="badge badge-inactive">Inactivo</span>}
            </button>
          </li>
        ))}
      </ul>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Nuevo sorteo</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombre del sorteo</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej: Día de la madre"
                  required
                />
              </div>
              <div className="form-group">
                <label>Descripción (opcional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Premios, fecha del sorteo..."
                />
              </div>
              <div className="form-group">
                <label>Precio por ticket (Gs.)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={ticketPrice}
                  onChange={(e) => setTicketPrice(e.target.value)}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Guardando...' : 'Crear sorteo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  )
}
