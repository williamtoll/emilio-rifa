import { AuthProvider } from './contexts/AuthContext'
import App from './App'
import PublicTicketPage from './pages/PublicTicketPage'
import PublicBuyPage from './pages/PublicBuyPage'
import PublicPaymentPage from './pages/PublicPaymentPage'

const PUBLIC_TICKET_PATTERN = /^\/t\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i
const PUBLIC_BUY_PATTERN = /^\/comprar(?:\/(\d+))?\/?$/
const PUBLIC_PAYMENT_PATTERN = /^\/comprobante\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i

export default function Root() {
  const path = window.location.pathname

  const ticketMatch = path.match(PUBLIC_TICKET_PATTERN)
  if (ticketMatch) {
    return <PublicTicketPage publicId={ticketMatch[1]} />
  }

  const buyMatch = path.match(PUBLIC_BUY_PATTERN)
  if (buyMatch) {
    return <PublicBuyPage raffleId={buyMatch[1]} />
  }

  const paymentMatch = path.match(PUBLIC_PAYMENT_PATTERN)
  if (paymentMatch) {
    return <PublicPaymentPage publicId={paymentMatch[1]} />
  }

  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  )
}
