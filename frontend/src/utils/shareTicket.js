export async function shareTicketImage(imageUrl, ticketNumber, raffleName) {
  const response = await fetch(imageUrl)
  const blob = await response.blob()
  const file = new File([blob], `ticket-${ticketNumber}.png`, { type: 'image/png' })
  const title = `Ticket #${ticketNumber} - La Rifa`
  const text = raffleName
    ? `Ticket #${ticketNumber} — ${raffleName}`
    : `Ticket #${ticketNumber}`

  if (navigator.share && navigator.canShare?.({ files: [file] })) {
    await navigator.share({ title, text, files: [file] })
    return 'shared'
  }

  const link = document.createElement('a')
  link.href = imageUrl
  link.download = `ticket-${ticketNumber}.png`
  link.click()
  return 'downloaded'
}

export function canShareImage() {
  return typeof navigator !== 'undefined' && typeof navigator.share === 'function'
}
