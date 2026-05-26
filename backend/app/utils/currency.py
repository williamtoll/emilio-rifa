def format_guaranies(amount: float | int) -> str:
    """Formatea un monto en guaraníes paraguayos (sin decimales)."""
    value = int(round(float(amount)))
    formatted = f"{value:,}".replace(",", ".")
    return f"Gs. {formatted}"
