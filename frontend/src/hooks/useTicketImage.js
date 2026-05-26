import { useEffect, useState } from 'react'
import { ticketsApi } from '../api'

export function useTicketImage(ticketId, enabled = true) {
  const [imageUrl, setImageUrl] = useState(null)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!enabled) {
      setImageUrl(null)
      setLoading(false)
      setError(null)
      return
    }

    let objectUrl = null
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        objectUrl = await ticketsApi.fetchImage(ticketId)
        if (!cancelled) setImageUrl(objectUrl)
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [ticketId, enabled])

  return { imageUrl, loading, error }
}
