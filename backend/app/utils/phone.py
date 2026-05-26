import re

PY_MOBILE_REGEX = re.compile(r"^09\d{8}$")


def digits_only(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def normalize_paraguay_phone(value: str | None) -> str | None:
    """Guarda/valida formato local: 0961732207 (10 dígitos)."""
    if not value:
        return None
    digits = digits_only(value)
    if not digits:
        return None
    if PY_MOBILE_REGEX.match(digits):
        return digits
    raise ValueError("Teléfono inválido. Use formato paraguayo: 09XXXXXXXX (10 dígitos)")


def to_whatsapp_phone(value: str) -> str:
    """Convierte 0961732207 → 595961732207 para wa.me."""
    digits = digits_only(value)
    if digits.startswith("595") and len(digits) == 12:
        return digits
    if PY_MOBILE_REGEX.match(digits):
        return f"595{digits[1:]}"
    if len(digits) == 9 and digits.startswith("9"):
        return f"595{digits}"
    raise ValueError("Teléfono inválido para Paraguay")
