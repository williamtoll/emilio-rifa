import { useEffect, useRef, useState } from 'react'
import { rafflesApi } from '../api'
import './RaffleSidebar.css'

function RaffleFormModal({ title, initial, onSubmit, onClose, saving }) {
  const [name, setName] = useState(initial.name)
  const [description, setDescription] = useState(initial.description || '')
  const [ticketPrice, setTicketPrice] = useState(String(initial.ticket_price ?? '50000'))
  const [maxTickets, setMaxTickets] = useState(initial.max_tickets != null ? String(initial.max_tickets) : '')
  const [isActive, setIsActive] = useState(initial.is_active ?? true)
  const [imagePreview, setImagePreview] = useState(initial.image_url || null)
  const [imageFile, setImageFile] = useState(null)
  const [removeImage, setRemoveImage] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    return () => {
      if (imageFile && imagePreview && imagePreview.startsWith('blob:')) {
        URL.revokeObjectURL(imagePreview)
      }
    }
  }, [imageFile, imagePreview])

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    if (imagePreview && imagePreview.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreview)
    }
    setImageFile(file)
    setRemoveImage(false)
    setImagePreview(URL.createObjectURL(file))
  }

  const handleRemoveImage = () => {
    if (imagePreview && imagePreview.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreview)
    }
    setImageFile(null)
    setImagePreview(null)
    setRemoveImage(!!initial.image_url)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(
      {
        name,
        description: description || null,
        ticket_price: parseFloat(ticketPrice) || 0,
        max_tickets: maxTickets ? parseInt(maxTickets, 10) : null,
        is_active: isActive,
      },
      { imageFile, removeImage: removeImage && !imageFile },
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
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
              rows={3}
              placeholder="Fecha del sorteo, detalles, etc."
            />
          </div>
          <div className="form-group">
            <label>Imagen del sorteo (opcional)</label>
            <div className="raffle-image-field">
              {imagePreview ? (
                <img src={imagePreview} alt="Vista previa" className="raffle-image-preview" />
              ) : (
                <div className="raffle-image-placeholder">Sin imagen</div>
              )}
              <div className="raffle-image-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {imagePreview ? 'Cambiar imagen' : 'Subir imagen'}
                </button>
                {imagePreview && (
                  <button type="button" className="btn btn-sm btn-ghost-danger" onClick={handleRemoveImage}>
                    Quitar
                  </button>
                )}
              </div>
            </div>
            <p className="field-hint">Aparece en el ticket. JPG, PNG, WEBP o GIF. Máx. 5 MB.</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              style={{ display: 'none' }}
              onChange={handleFileChange}
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
          <div className="form-group">
            <label>Cantidad de tickets (opcional)</label>
            <input
              type="number"
              min="1"
              max="10000"
              step="1"
              value={maxTickets}
              onChange={(e) => setMaxTickets(e.target.value)}
              placeholder="Ej: 500 (vacío = automático)"
            />
            <p className="field-hint">Define cuántos números puede elegir el cliente en la página de compra.</p>
          </div>
          <div className="form-group form-group-checkbox">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Sorteo activo
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function RaffleSidebar({
  raffles,
  selectedId,
  onSelect,
  onCreate,
  onUpdate,
  onRefresh,
  onError,
  editRaffleId,
  onEditRaffleIdConsumed,
}) {
  const [modal, setModal] = useState(null)
  const [saving, setSaving] = useState(false)

  const closeModal = () => setModal(null)

  useEffect(() => {
    if (editRaffleId == null) return
    const raffle = raffles.find((r) => r.id === editRaffleId)
    if (raffle) setModal({ type: 'edit', raffle })
    onEditRaffleIdConsumed?.()
  }, [editRaffleId, raffles, onEditRaffleIdConsumed])

  const applyImageChanges = async (raffleId, { imageFile, removeImage }) => {
    if (removeImage) {
      await rafflesApi.deleteImage(raffleId)
    } else if (imageFile) {
      await rafflesApi.uploadImage(raffleId, imageFile)
    }
  }

  const handleCreate = async (data, imageOpts) => {
    setSaving(true)
    try {
      const created = await onCreate(data)
      if (imageOpts?.imageFile) {
        await rafflesApi.uploadImage(created.id, imageOpts.imageFile)
        await onRefresh?.()
      }
      closeModal()
    } catch (err) {
      onError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async (data, imageOpts) => {
    if (modal?.type !== 'edit') return
    setSaving(true)
    try {
      await onUpdate(modal.raffle.id, data)
      if (imageOpts?.removeImage || imageOpts?.imageFile) {
        await applyImageChanges(modal.raffle.id, imageOpts)
        await onRefresh?.()
      }
      closeModal()
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
        <button className="btn btn-primary btn-sm" onClick={() => setModal('create')}>
          + Nuevo
        </button>
      </div>

      <ul className="raffle-list">
        {raffles.length === 0 && (
          <li className="raffle-empty">No hay sorteos. Crea el primero.</li>
        )}
        {raffles.map((r) => (
          <li key={r.id} className="raffle-list-item">
            <button
              className={`raffle-item ${selectedId === r.id ? 'active' : ''}`}
              onClick={() => onSelect(r.id)}
            >
              {r.image_url && (
                <img src={r.image_url} alt="" className="raffle-item-thumb" />
              )}
              <span className="raffle-item-body">
                <span className="raffle-name">{r.name}</span>
                <span className="raffle-stats">
                  {r.ticket_count} tickets · {r.paid_count} pagados
                </span>
                <span className="raffle-badges">
                  {!r.is_active && <span className="badge badge-inactive">Inactivo</span>}
                  {r.draw_closed_at && <span className="badge badge-closed">Cerrado</span>}
                </span>
              </span>
            </button>
            <button
              type="button"
              className="raffle-edit-btn"
              title="Editar sorteo"
              onClick={() => setModal({ type: 'edit', raffle: r })}
            >
              ✎
            </button>
          </li>
        ))}
      </ul>

      {modal === 'create' && (
        <RaffleFormModal
          title="Nuevo sorteo"
          initial={{ name: '', description: '', ticket_price: 50000, is_active: true }}
          onSubmit={handleCreate}
          onClose={closeModal}
          saving={saving}
        />
      )}

      {modal?.type === 'edit' && (
        <RaffleFormModal
          key={modal.raffle.id}
          title="Editar sorteo"
          initial={modal.raffle}
          onSubmit={handleUpdate}
          onClose={closeModal}
          saving={saving}
        />
      )}
    </aside>
  )
}
