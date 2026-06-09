import { useRef, useState } from 'react'
import { prizesApi } from '../api'
import './PrizesManager.css'

export default function PrizesManager({ raffle, onPrizesChange, onError }) {
  const [showForm, setShowForm] = useState(false)
  const [editingPrize, setEditingPrize] = useState(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [uploadingId, setUploadingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const fileInputRef = useRef(null)
  const [pendingImagePrizeId, setPendingImagePrizeId] = useState(null)

  const prizes = raffle.prizes || []

  const openCreate = () => {
    setEditingPrize(null)
    setName('')
    setDescription('')
    setShowForm(true)
  }

  const openEdit = (prize) => {
    setEditingPrize(prize)
    setName(prize.name)
    setDescription(prize.description || '')
    setShowForm(true)
  }

  const closeForm = () => {
    setShowForm(false)
    setEditingPrize(null)
    setName('')
    setDescription('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { name, description: description || null, order: editingPrize?.order ?? prizes.length }
      let updated
      if (editingPrize) {
        updated = await prizesApi.update(raffle.id, editingPrize.id, payload)
        onPrizesChange(prizes.map((p) => (p.id === updated.id ? updated : p)))
      } else {
        updated = await prizesApi.create(raffle.id, payload)
        onPrizesChange([...prizes, updated])
      }
      closeForm()
    } catch (err) {
      onError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (prize) => {
    if (!window.confirm(`¿Eliminar el premio "${prize.name}"?`)) return
    setDeletingId(prize.id)
    try {
      await prizesApi.delete(raffle.id, prize.id)
      onPrizesChange(prizes.filter((p) => p.id !== prize.id))
    } catch (err) {
      onError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  const triggerImageUpload = (prizeId) => {
    setPendingImagePrizeId(prizeId)
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !pendingImagePrizeId) return
    e.target.value = ''
    setUploadingId(pendingImagePrizeId)
    try {
      const updated = await prizesApi.uploadImage(raffle.id, pendingImagePrizeId, file)
      onPrizesChange(prizes.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err) {
      onError(err.message)
    } finally {
      setUploadingId(null)
      setPendingImagePrizeId(null)
    }
  }

  const handleDeleteImage = async (prize) => {
    setUploadingId(prize.id)
    try {
      const updated = await prizesApi.deleteImage(raffle.id, prize.id)
      onPrizesChange(prizes.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err) {
      onError(err.message)
    } finally {
      setUploadingId(null)
    }
  }

  return (
    <div className="prizes-manager">
      <div className="prizes-header">
        <h3>Premios</h3>
        <button className="btn btn-sm btn-outline" onClick={openCreate}>
          + Agregar premio
        </button>
      </div>

      {prizes.length === 0 ? (
        <p className="prizes-empty">No hay premios definidos para este sorteo.</p>
      ) : (
        <ul className="prizes-list">
          {prizes.map((prize) => (
            <li key={prize.id} className="prize-item">
              <div className="prize-image-slot">
                {prize.image_url ? (
                  <img src={prize.image_url} alt={prize.name} className="prize-thumb" />
                ) : (
                  <div className="prize-thumb-placeholder">🎁</div>
                )}
              </div>
              <div className="prize-info">
                <span className="prize-name">{prize.name}</span>
                {prize.description && <span className="prize-desc">{prize.description}</span>}
              </div>
              <div className="prize-actions">
                <button
                  className="btn btn-xs btn-outline"
                  onClick={() => triggerImageUpload(prize.id)}
                  disabled={uploadingId === prize.id}
                  title={prize.image_url ? 'Cambiar imagen' : 'Subir imagen'}
                >
                  {uploadingId === prize.id ? '...' : prize.image_url ? '🖼 Cambiar' : '🖼 Imagen'}
                </button>
                {prize.image_url && (
                  <button
                    className="btn btn-xs btn-ghost"
                    onClick={() => handleDeleteImage(prize)}
                    disabled={uploadingId === prize.id}
                    title="Quitar imagen"
                  >
                    ✕
                  </button>
                )}
                <button
                  className="btn btn-xs btn-outline"
                  onClick={() => openEdit(prize)}
                  title="Editar"
                >
                  Editar
                </button>
                <button
                  className="btn btn-xs btn-danger"
                  onClick={() => handleDelete(prize)}
                  disabled={deletingId === prize.id}
                  title="Eliminar"
                >
                  {deletingId === prize.id ? '...' : 'Borrar'}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      {showForm && (
        <div className="modal-overlay" onClick={closeForm}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingPrize ? 'Editar premio' : 'Nuevo premio'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombre del premio *</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej: 1° Premio - Smart TV 55&quot;"
                  required
                />
              </div>
              <div className="form-group">
                <label>Descripción (opcional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Detalles del premio..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={closeForm}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Guardando...' : editingPrize ? 'Guardar cambios' : 'Agregar premio'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
