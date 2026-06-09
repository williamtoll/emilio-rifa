import { useCallback, useEffect, useRef, useState } from 'react'
import { drawsApi, rafflesApi } from '../api'
import './DrawView.css'

function randomTicketNum() {
  return String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')
}

function PrizeCard({ prize, result, isNext, onDraw, onUndo }) {
  const [spinning, setSpinning] = useState(false)
  const [displayNum, setDisplayNum] = useState('????')
  const intervalRef = useRef(null)

  const handleDraw = async () => {
    setSpinning(true)
    setDisplayNum(randomTicketNum())
    intervalRef.current = setInterval(() => setDisplayNum(randomTicketNum()), 80)

    try {
      const res = await onDraw(prize.id)
      clearInterval(intervalRef.current)
      setDisplayNum(res.ticket_number)
    } catch (err) {
      clearInterval(intervalRef.current)
      setDisplayNum('????')
    } finally {
      setSpinning(false)
    }
  }

  useEffect(() => () => clearInterval(intervalRef.current), [])

  const won = !!result
  const posLabel = `${prize.order + 1}° Premio`

  return (
    <div className={`prize-card ${won ? 'prize-card--won' : ''} ${isNext && !won ? 'prize-card--next' : ''}`}>
      <div className="prize-card-left">
        {prize.image_url ? (
          <img src={prize.image_url} alt={prize.name} className="prize-card-img" />
        ) : (
          <div className="prize-card-img-placeholder">🎁</div>
        )}
        <div className="prize-card-info">
          <span className="prize-card-pos">{posLabel}</span>
          <span className="prize-card-name">{prize.name}</span>
          {prize.description && <span className="prize-card-desc">{prize.description}</span>}
        </div>
      </div>

      <div className="prize-card-right">
        {won ? (
          <div className="prize-winner">
            <div className="prize-winner-num">#{result.ticket_number}</div>
            <div className="prize-winner-name">{result.buyer_name}</div>
            {result.buyer_phone && (
              <div className="prize-winner-phone">{result.buyer_phone}</div>
            )}
            <button
              className="btn btn-sm btn-ghost-danger"
              onClick={() => onUndo(prize.id)}
              title="Deshacer este sorteo"
            >
              Deshacer
            </button>
          </div>
        ) : spinning ? (
          <div className="prize-spinning">
            <div className="spinning-num">{displayNum}</div>
            <div className="spinning-label">Sorteando...</div>
          </div>
        ) : (
          <button
            className={`btn btn-draw ${isNext ? 'btn-draw--active' : ''}`}
            onClick={handleDraw}
            disabled={spinning}
          >
            🎰 Sortear
          </button>
        )}
      </div>
    </div>
  )
}

export default function DrawView({ initialRaffleId, raffles, onBack }) {
  const [selectedId, setSelectedId] = useState(initialRaffleId || (raffles[0]?.id ?? null))
  const [raffle, setRaffle] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [resetting, setResetting] = useState(false)

  const loadRaffle = useCallback(async (id) => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const [r, res] = await Promise.all([rafflesApi.get(id), drawsApi.list(id)])
      setRaffle(r)
      setResults(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRaffle(selectedId)
  }, [selectedId, loadRaffle])

  const handleDraw = async (prizeId) => {
    const res = await drawsApi.draw(selectedId, prizeId)
    setResults((prev) => [...prev, res])
    return res
  }

  const handleUndo = async (prizeId) => {
    await drawsApi.undoPrize(selectedId, prizeId)
    setResults((prev) => prev.filter((r) => r.prize_id !== prizeId))
  }

  const handleReset = async () => {
    if (!window.confirm('¿Reiniciar todos los resultados del sorteo?')) return
    setResetting(true)
    try {
      await drawsApi.resetAll(selectedId)
      setResults([])
    } catch (e) {
      setError(e.message)
    } finally {
      setResetting(false)
    }
  }

  const sortedPrizes = raffle
    ? [...(raffle.prizes || [])].sort((a, b) => b.order - a.order)
    : []

  const resultMap = Object.fromEntries(results.map((r) => [r.prize_id, r]))

  const nextPrizeId = sortedPrizes.find((p) => !resultMap[p.id])?.id ?? null

  const sortedHistory = [...results].sort((a, b) => new Date(b.drawn_at) - new Date(a.drawn_at))

  return (
    <div className="draw-view">
      <div className="draw-topbar">
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          ← Volver
        </button>
        <div className="draw-topbar-center">
          <span className="draw-topbar-title">Realizar Sorteo</span>
          <select
            className="draw-raffle-select"
            value={selectedId || ''}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {raffles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        {results.length > 0 && (
          <button
            className="btn btn-sm btn-ghost-danger"
            onClick={handleReset}
            disabled={resetting}
          >
            {resetting ? 'Reiniciando...' : 'Reiniciar sorteo'}
          </button>
        )}
        {results.length === 0 && <div style={{ width: 110 }} />}
      </div>

      {error && (
        <div className="draw-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {loading ? (
        <div className="draw-loading">
          <div className="spinner" />
          <p>Cargando...</p>
        </div>
      ) : !raffle ? (
        <div className="draw-empty">Seleccioná un sorteo para comenzar.</div>
      ) : sortedPrizes.length === 0 ? (
        <div className="draw-empty">
          <span>🎁</span>
          <p>Este sorteo no tiene premios definidos.</p>
          <p>Volvé a gestión de tickets y agregá los premios primero.</p>
        </div>
      ) : (
        <div className="draw-body">
          <div className="draw-raffle-info">
            <h2>{raffle.name}</h2>
            <div className="draw-raffle-meta">
              <span>{raffle.ticket_count} tickets</span>
              <span className="dot">·</span>
              <span>{raffle.paid_count} pagados</span>
              <span className="dot">·</span>
              <span>{sortedPrizes.length} premios</span>
              <span className="dot">·</span>
              <span className="draw-progress">
                {results.length}/{sortedPrizes.length} sorteados
              </span>
            </div>
            {results.length === sortedPrizes.length && sortedPrizes.length > 0 && (
              <div className="draw-complete-banner">
                🎉 ¡Todos los premios fueron sorteados!
              </div>
            )}
          </div>

          <div className="draw-prizes-section">
            <h3 className="draw-section-title">Premios</h3>
            <div className="draw-prizes-list">
              {sortedPrizes.map((prize) => (
                <PrizeCard
                  key={prize.id}
                  prize={prize}
                  result={resultMap[prize.id] || null}
                  isNext={prize.id === nextPrizeId}
                  onDraw={handleDraw}
                  onUndo={handleUndo}
                />
              ))}
            </div>
          </div>

          {sortedHistory.length > 0 && (
            <div className="draw-history-section">
              <h3 className="draw-section-title">Historial de ganadores</h3>
              <table className="draw-history-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Premio</th>
                    <th>Ticket</th>
                    <th>Ganador</th>
                    <th>Teléfono</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedHistory.map((r, i) => (
                    <tr key={r.id}>
                      <td className="history-idx">{i + 1}</td>
                      <td className="history-prize">{r.prize_name}</td>
                      <td className="history-ticket">#{r.ticket_number}</td>
                      <td className="history-buyer">{r.buyer_name}</td>
                      <td className="history-phone">{r.buyer_phone || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
