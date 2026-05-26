/** Teléfono móvil Paraguay: 10 dígitos, formato 09XXXXXXXX */

const PY_MOBILE_REGEX = /^09\d{8}$/

export function digitsOnly(value) {
  return (value || '').replace(/\D/g, '')
}

/** Limita y formatea mientras el usuario escribe (solo dígitos, máx. 10). */
export function formatParaguayPhoneInput(value) {
  let digits = digitsOnly(value).slice(0, 10)
  if (digits.length > 0 && digits[0] !== '0') {
    digits = `0${digits}`.slice(0, 10)
  }
  if (digits.length > 1 && digits[1] !== '9') {
    digits = '09' + digits.slice(2)
  }
  if (digits.length === 1 && digits !== '0') {
    digits = '0'
  }
  return digits
}

export function isValidParaguayPhone(value) {
  if (!value) return true
  return PY_MOBILE_REGEX.test(digitsOnly(value))
}

/** Normaliza para guardar en BD: 0961732207 */
export function normalizeParaguayPhone(value) {
  const digits = digitsOnly(value)
  if (!digits) return null
  if (PY_MOBILE_REGEX.test(digits)) return digits
  return null
}

/** Muestra con espacios: 0961 732 207 */
export function displayParaguayPhone(value) {
  const digits = digitsOnly(value)
  if (!digits) return ''
  if (digits.length <= 4) return digits
  if (digits.length <= 7) return `${digits.slice(0, 4)} ${digits.slice(4)}`
  return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 10)}`
}
