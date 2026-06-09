import { useCallback, useEffect, useState } from 'react'
import { rafflesApi, ticketsApi } from './api'
import { useAuth } from './contexts/AuthContext'
import LoginPage from './components/LoginPage'
import RaffleSidebar from './components/RaffleSidebar'
import TicketPanel from './components/TicketPanel'
import DrawView from './components/DrawView'
import './App.css'

export default function App() {
  const { user, loading: authLoading, logout, isAuthenticated } = useAuth()
  const [raffles, setRaffles] = useState([])
  const [selectedRaffleId, setSelectedRaffleId] = useState(null)
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [view, setView] = useState('tickets')

  const showNotice = (msg) => {
    setNotice(msg)
    setTimeout(() => setNotice(null), 4000)
  }

  const loadRaffles = useCallback(async () => {
    try {
      const data = await rafflesApi.list()
      setRaffles(data)
      if (data.length && !selectedRaffleId) {
        setSelectedRaffleId(data[0].id)
      }
    } catch (e) {
      setError(e.message)
    }
  }, [selectedRaffleId])

  const loadTickets = useCallback(async (raffleId) => {
    if (!raffleId) {
      setTickets([])
      return
    }
    try {
      const data = await ticketsApi.list(raffleId)
      setTickets(data)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) return
    async function init() {
      setLoading(true)
      await loadRaffles()
      setLoading(false)
    }
    init()
  }, [isAuthenticated, loadRaffles])

  useEffect(() => {
    if (selectedRaffleId && isAuthenticated) {
      loadTickets(selectedRaffleId)
    }
  }, [selectedRaffleId, loadTickets, isAuthenticated])

  const selectedRaffle = raffles.find((r) => r.id === selectedRaffleId)

  const handleCreateRaffle = async (data) => {
    const created = await rafflesApi.create(data)
    await loadRaffles()
    setSelectedRaffleId(created.id)
    showNotice(`Sorteo "${created.name}" creado`)
  }

  const handleCreateTicket = async (data) => {
    const created = await ticketsApi.create({ ...data, raffle_id: selectedRaffleId })
    await loadTickets(selectedRaffleId)
    await loadRaffles()
    showNotice(`Ticket #${created.ticket_number} generado`)
    return created
  }

  const handleTogglePaid = async (ticket) => {
    if (ticket.is_paid) {
      await ticketsApi.markUnpaid(ticket.id)
    } else {
      await ticketsApi.markPaid(ticket.id)
    }
    await loadTickets(selectedRaffleId)
    await loadRaffles()
  }

  const handleSendEmail = async (ticketId) => {
    await ticketsApi.sendEmail(ticketId)
    showNotice('Correo enviado correctamente')
  }

  const handleWhatsApp = async (ticketId) => {
    const { url } = await ticketsApi.whatsappLink(ticketId)
    window.open(url, '_blank')
  }

  const handlePrizesChange = (updatedPrizes) => {
    setRaffles((prev) =>
      prev.map((r) => (r.id === selectedRaffleId ? { ...r, prizes: updatedPrizes } : r))
    )
  }

  if (authLoading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Cargando...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner" />
        <p>Cargando sorteos...</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🎟️</span>
          <div>
            <h1>La Rifa</h1>
            <p>Gestión de tickets y sorteos</p>
          </div>
        </div>
        <nav className="app-nav">
          <button
            className={`app-nav-btn ${view === 'tickets' ? 'app-nav-btn--active' : ''}`}
            onClick={() => setView('tickets')}
          >
            🎟️ Tickets
          </button>
          <button
            className={`app-nav-btn ${view === 'draw' ? 'app-nav-btn--active' : ''}`}
            onClick={() => setView('draw')}
          >
            🎰 Sortear
          </button>
        </nav>
        <div className="header-user">
          <span className="header-username">{user?.username}</span>
          <button type="button" className="btn btn-secondary btn-sm" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner app-banner">
          {error}
          <button className="btn btn-sm btn-secondary" onClick={() => setError(null)}>Cerrar</button>
        </div>
      )}
      {notice && <div className="success-banner app-banner">{notice}</div>}

      {view === 'draw' ? (
        <DrawView
          initialRaffleId={selectedRaffleId}
          raffles={raffles}
          onBack={() => setView('tickets')}
        />
      ) : (
        <div className="app-layout">
          <RaffleSidebar
            raffles={raffles}
            selectedId={selectedRaffleId}
            onSelect={setSelectedRaffleId}
            onCreate={handleCreateRaffle}
            onError={setError}
          />
          <TicketPanel
            raffle={selectedRaffle}
            tickets={tickets}
            onCreateTicket={handleCreateTicket}
            onTogglePaid={handleTogglePaid}
            onSendEmail={handleSendEmail}
            onWhatsApp={handleWhatsApp}
            onError={setError}
            onNotice={showNotice}
            onPrizesChange={handlePrizesChange}
          />
        </div>
      )}
    </div>
  )
}
