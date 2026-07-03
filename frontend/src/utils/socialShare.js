export function getRaffleBuyUrl(raffleId) {
  return `${window.location.origin}/comprar/${raffleId}`
}

export function buildRaffleBuyShareText(raffleName, url, { priceLabel, availableLabel } = {}) {
  const lines = [`🎟️ ${raffleName}`]
  if (priceLabel) lines.push(`💰 ${priceLabel}`)
  if (availableLabel) lines.push(`🎫 ${availableLabel}`)
  lines.push('', 'Elegí tu número y reservá acá:', url)
  return lines.join('\n')
}

export function buildTicketShareText(ticketNumber, raffleName, url) {
  const title = raffleName ? `Ticket #${ticketNumber} — ${raffleName}` : `Ticket #${ticketNumber}`
  return `🎟️ ${title}\n\n👉 Ver ticket:\n${url}`
}

export function openFacebookShare(url) {
  const shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`
  window.open(shareUrl, 'facebook-share', 'width=580,height=480,noopener,noreferrer')
}

async function downloadImage(imageUrl, filename) {
  const response = await fetch(imageUrl)
  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}

export async function shareToInstagram({ url, text, imageUrl, imageFilename }) {
  const message = text || url
  if (imageUrl) {
    await downloadImage(imageUrl, imageFilename || 'sorteo.jpg')
    await navigator.clipboard.writeText(message)
    return 'image'
  }
  const fullText = message.includes(url) ? message : `${message}\n${url}`
  await navigator.clipboard.writeText(fullText)
  return 'link'
}
