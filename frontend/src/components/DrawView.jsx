import { useCallback, useEffect, useRef, useState } from 'react'
import { drawsApi, rafflesApi } from '../api'
import './DrawView.css'

// ─── helpers ─────────────────────────────────────────────────────────────────
function rndNum() {
  return String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')
}
function delay(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

// ─── Phases ───────────────────────────────────────────────────────────────────
const P = { LOADING: 'loading', INTRO: 'intro', DRAWING: 'drawing', DONE: 'done' }
const DS = { IDLE: 'idle', SPINNING: 'spinning', REVEALED: 'revealed' }

// ─── DrawView ─────────────────────────────────────────────────────────────────
export default function DrawView({ initialRaffleId, raffles, onBack }) {
  const [selectedId, setSelectedId] = useState(initialRaffleId || raffles[0]?.id || null)
  const [raffle, setRaffle] = useState(null)
  const [sortedPrizes, setSortedPrizes] = useState([])   // desc by order
  const [results, setResults] = useState({})             // prizeId → DrawResult
  const [phase, setPhase] = useState(P.LOADING)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [drawState, setDrawState] = useState(DS.IDLE)
  const [spinNum, setSpinNum] = useState('????')
  const [error, setError] = useState(null)
  const [resetting, setResetting] = useState(false)
  const spinRef = useRef(null)

  // ── Load raffle + existing results ──────────────────────────────────────────
  const load = useCallback(async (id) => {
    if (!id) return
    setPhase(P.LOADING)
    setError(null)
    try {
      const [r, res] = await Promise.all([rafflesApi.get(id), drawsApi.list(id)])
      const prizes = [...(r.prizes || [])].sort((a, b) => b.order - a.order)
      const resMap = Object.fromEntries(res.map((x) => [x.prize_id, x]))
      const nextIdx = prizes.findIndex((p) => !resMap[p.id])

      setRaffle(r)
      setSortedPrizes(prizes)
      setResults(resMap)

      if (prizes.length === 0) {
        setPhase(P.INTRO)
      } else if (nextIdx === -1) {
        // All drawn already
        setCurrentIdx(prizes.length - 1)
        setDrawState(DS.REVEALED)
        setPhase(P.DONE)
      } else if (Object.keys(resMap).length > 0 && nextIdx > 0) {
        // Partially drawn — resume
        setCurrentIdx(nextIdx)
        setDrawState(DS.IDLE)
        setPhase(P.DRAWING)
      } else {
        setCurrentIdx(0)
        setDrawState(DS.IDLE)
        setPhase(P.INTRO)
      }
    } catch (e) {
      setError(e.message)
      setPhase(P.INTRO)
    }
  }, [])

  useEffect(() => { load(selectedId) }, [selectedId, load])

  // ── Draw ────────────────────────────────────────────────────────────────────
  const handleDraw = async () => {
    const prize = sortedPrizes[currentIdx]
    setDrawState(DS.SPINNING)
    setSpinNum(rndNum())

    // fast spin
    spinRef.current = setInterval(() => setSpinNum(rndNum()), 65)
    const t0 = Date.now()

    let result
    try {
      result = await drawsApi.draw(selectedId, prize.id)
    } catch (e) {
      clearInterval(spinRef.current)
      setDrawState(DS.IDLE)
      setError(e.message)
      return
    }

    // spin at least 3 seconds total
    const wait = Math.max(0, 3000 - (Date.now() - t0))
    await delay(wait)
    clearInterval(spinRef.current)

    // slowdown
    for (const ms of [130, 200, 300, 420, 560]) {
      setSpinNum(rndNum())
      await delay(ms)
    }

    setSpinNum(result.ticket_number)
    setResults((prev) => ({ ...prev, [prize.id]: result }))
    setDrawState(DS.REVEALED)
  }

  const handleNext = () => {
    if (currentIdx + 1 >= sortedPrizes.length) {
      setPhase(P.DONE)
    } else {
      setCurrentIdx((i) => i + 1)
      setDrawState(DS.IDLE)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('¿Reiniciar todos los resultados del sorteo?')) return
    setResetting(true)
    try {
      await drawsApi.resetAll(selectedId)
      setResults({})
      setCurrentIdx(0)
      setDrawState(DS.IDLE)
      setPhase(P.INTRO)
    } catch (e) {
      setError(e.message)
    } finally {
      setResetting(false)
    }
  }

  const handleUndoCurrent = async () => {
    const prize = sortedPrizes[currentIdx]
    try {
      await drawsApi.undoPrize(selectedId, prize.id)
      setResults((prev) => { const n = { ...prev }; delete n[prize.id]; return n })
      setDrawState(DS.IDLE)
    } catch (e) {
      setError(e.message)
    }
  }

  // ── Derived ─────────────────────────────────────────────────────────────────
  const currentPrize = sortedPrizes[currentIdx]
  const currentResult = currentPrize ? results[currentPrize.id] : null
  const drawnCount = Object.keys(results).length
  const totalPrizes = sortedPrizes.length

  // prizes that were drawn before the current one (to show as mini recap)
  const prevWinners = sortedPrizes
    .slice(0, currentIdx)
    .map((p) => results[p.id])
    .filter(Boolean)
    .reverse()

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="dv-root">
      {/* ── top bar ── */}
      <div className="dv-topbar">
        <button className="dv-back" onClick={onBack}>← Volver</button>
        <div className="dv-topbar-center">
          <select
            className="dv-select"
            value={selectedId || ''}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {raffles.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        {drawnCount > 0 && phase !== P.DONE && (
          <button className="dv-reset" onClick={handleReset} disabled={resetting}>
            {resetting ? '...' : 'Reiniciar'}
          </button>
        )}
        {(drawnCount === 0 || phase === P.DONE) && <div className="dv-spacer" />}
      </div>

      {error && (
        <div className="dv-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* ── LOADING ── */}
      {phase === P.LOADING && (
        <div className="dv-center">
          <div className="spinner" />
        </div>
      )}

      {/* ── INTRO ── */}
      {phase === P.INTRO && raffle && (
        <div className="dv-center">
          <div className="dv-intro-card">
            <div className="dv-intro-logo">🎟️</div>
            <h1 className="dv-intro-title">{raffle.name}</h1>
            <p className="dv-intro-sub">
              {raffle.paid_count} tickets participantes · {totalPrizes} premios
            </p>

            {totalPrizes === 0 ? (
              <p className="dv-intro-warn">
                Este sorteo no tiene premios. Agregalos desde la gestión de tickets.
              </p>
            ) : (
              <>
                <div className="dv-intro-prizes">
                  <p className="dv-intro-prizes-label">Se sortearán en este orden:</p>
                  <ol className="dv-intro-list">
                    {sortedPrizes.map((p, i) => (
                      <li key={p.id} className="dv-intro-item">
                        <span className="dv-intro-pos">{i + 1}°</span>
                        {p.image_url && (
                          <img src={p.image_url} alt={p.name} className="dv-intro-img" />
                        )}
                        <span className="dv-intro-name">{p.name}</span>
                      </li>
                    ))}
                  </ol>
                </div>
                <button className="dv-btn-start" onClick={() => setPhase(P.DRAWING)}>
                  Comenzar Sorteo
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── DRAWING ── */}
      {phase === P.DRAWING && currentPrize && (
        <div className="dv-stage">
          {/* Progress dots */}
          <div className="dv-progress">
            {sortedPrizes.map((p, i) => {
              const won = !!results[p.id]
              const isCurrent = i === currentIdx
              return (
                <div
                  key={p.id}
                  className={`dv-dot ${isCurrent ? 'dv-dot--current' : won ? 'dv-dot--done' : ''}`}
                />
              )
            })}
          </div>

          {/* Main prize card */}
          <div className="dv-prize-stage">
            <div className="dv-prize-order">
              Premio {currentIdx + 1} de {totalPrizes}
            </div>

            {currentPrize.image_url && drawState !== DS.SPINNING && (
              <div className={`dv-prize-img-wrap ${drawState === DS.REVEALED ? 'dv-prize-img-wrap--revealed' : ''}`}>
                <img src={currentPrize.image_url} alt={currentPrize.name} className="dv-prize-img" />
              </div>
            )}

            <h2 className="dv-prize-name">{currentPrize.name}</h2>
            {currentPrize.description && drawState !== DS.SPINNING && (
              <p className="dv-prize-desc">{currentPrize.description}</p>
            )}

            {/* ── IDLE ── */}
            {drawState === DS.IDLE && (
              <div className="dv-idle">
                <div className="dv-ticket-placeholder">?</div>
                <button className="dv-btn-draw" onClick={handleDraw}>
                  🎰 SORTEAR
                </button>
              </div>
            )}

            {/* ── SPINNING ── */}
            {drawState === DS.SPINNING && (
              <div className="dv-spinning">
                <div className="dv-spin-num">{spinNum}</div>
                <div className="dv-spin-label">Sorteando…</div>
              </div>
            )}

            {/* ── REVEALED ── */}
            {drawState === DS.REVEALED && currentResult && (
              <div className="dv-revealed">
                <div className="dv-winner-label">🏆 GANADOR</div>
                <div className="dv-winner-num">#{currentResult.ticket_number}</div>
                <div className="dv-winner-name">{currentResult.buyer_name}</div>
                {currentResult.buyer_phone && (
                  <div className="dv-winner-phone">{currentResult.buyer_phone}</div>
                )}
                <div className="dv-revealed-actions">
                  <button className="dv-btn-undo" onClick={handleUndoCurrent}>
                    Repetir sorteo
                  </button>
                  {currentIdx + 1 < totalPrizes ? (
                    <button className="dv-btn-next" onClick={handleNext}>
                      Siguiente Premio →
                    </button>
                  ) : (
                    <button className="dv-btn-next" onClick={() => setPhase(P.DONE)}>
                      Ver Resultados →
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Previous winners (mini list at the bottom for transparency) */}
          {prevWinners.length > 0 && drawState !== DS.SPINNING && (
            <div className="dv-prev">
              <div className="dv-prev-title">Premios anteriores</div>
              <div className="dv-prev-list">
                {prevWinners.map((w) => (
                  <div key={w.id} className="dv-prev-item">
                    <span className="dv-prev-prize">{w.prize_name}</span>
                    <span className="dv-prev-sep">→</span>
                    <span className="dv-prev-ticket">#{w.ticket_number}</span>
                    <span className="dv-prev-buyer">{w.buyer_name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── DONE ── */}
      {phase === P.DONE && (
        <div className="dv-done">
          <div className="dv-done-header">
            <div className="dv-done-icon">🎉</div>
            <h1 className="dv-done-title">¡Sorteo Completado!</h1>
            <p className="dv-done-sub">{raffle?.name}</p>
          </div>

          <div className="dv-done-results">
            {sortedPrizes.map((p, i) => {
              const w = results[p.id]
              return (
                <div key={p.id} className="dv-done-row">
                  <div className="dv-done-row-prize">
                    {p.image_url && (
                      <img src={p.image_url} alt={p.name} className="dv-done-prize-img" />
                    )}
                    <div>
                      <div className="dv-done-pos">{i + 1}° Premio</div>
                      <div className="dv-done-prize-name">{p.name}</div>
                    </div>
                  </div>
                  <div className="dv-done-row-winner">
                    {w ? (
                      <>
                        <span className="dv-done-ticket">#{w.ticket_number}</span>
                        <span className="dv-done-buyer">{w.buyer_name}</span>
                        {w.buyer_phone && (
                          <span className="dv-done-phone">{w.buyer_phone}</span>
                        )}
                      </>
                    ) : (
                      <span className="dv-done-missing">— no sorteado —</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="dv-done-actions">
            <button className="dv-btn-reset" onClick={handleReset} disabled={resetting}>
              {resetting ? '...' : '↺ Nuevo sorteo'}
            </button>
            <button className="dv-btn-back-done" onClick={onBack}>
              Volver a tickets
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
