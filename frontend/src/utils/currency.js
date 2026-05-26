export function formatGuaranies(amount) {
  const value = Math.round(parseFloat(amount) || 0)
  const formatted = value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `Gs. ${formatted}`
}
