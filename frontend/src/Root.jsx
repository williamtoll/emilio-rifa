import { AuthProvider } from './contexts/AuthContext'
import App from './App'
import PublicTicketPage from './pages/PublicTicketPage'

const PUBLIC_TICKET_PATTERN = /^\/t\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i

export default function Root() {
  const match = window.location.pathname.match(PUBLIC_TICKET_PATTERN)
  if (match) {
    return <PublicTicketPage publicId={match[1]} />
  }

  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  )
}
