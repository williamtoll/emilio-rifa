from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from app.models import Ticket
from app.services.ticket_urls import get_short_ticket_url
from app.utils.currency import format_guaranies

WIDTH = 420
HEIGHT = 640
PURPLE = (124, 58, 237)
PURPLE_DARK = (91, 33, 182)
WHITE = (255, 255, 255)
BG = (250, 250, 252)
TEXT = (31, 41, 55)
MUTED = (107, 114, 128)
GREEN = (22, 163, 74)
YELLOW = (202, 138, 4)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_qr_payload(ticket: Ticket) -> str:
    return get_short_ticket_url(ticket)


def _font_line_height(font) -> int:
    return getattr(font, "size", 14) + 4


def _draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font, fill, max_width: int):
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    line_height = _font_line_height(font)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def generate_ticket_image(ticket: Ticket) -> bytes:
    raffle = ticket.raffle
    price = float(raffle.ticket_price) if raffle.ticket_price else 0
    paid = ticket.is_paid
    status_text = "PAGADO" if paid else "PENDIENTE"
    status_color = GREEN if paid else YELLOW

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (WIDTH, 88)], fill=PURPLE)
    draw.rectangle([(0, 88), (WIDTH, 92)], fill=PURPLE_DARK)

    font_title = _load_font(26, bold=True)
    font_brand = _load_font(14)
    font_number = _load_font(52, bold=True)
    font_label = _load_font(12)
    font_value = _load_font(16, bold=True)
    font_status = _load_font(13, bold=True)

    draw.text((WIDTH // 2, 28), "La Rifa", font=font_title, fill=WHITE, anchor="mm")
    draw.text((WIDTH // 2, 58), "TICKET DE SORTEO", font=font_brand, fill=(220, 210, 255), anchor="mm")

    draw.rounded_rectangle([(24, 108), (WIDTH - 24, 200)], radius=12, fill=WHITE, outline=PURPLE, width=2)
    draw.text((WIDTH // 2, 148), f"#{ticket.ticket_number}", font=font_number, fill=PURPLE, anchor="mm")

    y = 220
    fields = [
        ("Sorteo", raffle.name),
        ("Participante", ticket.buyer_name),
        ("Precio", format_guaranies(price)),
    ]
    for label, value in fields:
        draw.text((36, y), label.upper(), font=font_label, fill=MUTED)
        y = _draw_wrapped_text(draw, value, (36, y + 16), font_value, TEXT, WIDTH - 72) + 12

    badge_y = y + 4
    badge_w = 120
    badge_h = 28
    badge_x = (WIDTH - badge_w) // 2
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=14,
        fill=status_color,
    )
    draw.text(
        (WIDTH // 2, badge_y + badge_h // 2),
        status_text,
        font=font_status,
        fill=WHITE,
        anchor="mm",
    )

    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(build_qr_payload(ticket))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = 140
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    qr_x = (WIDTH - qr_size) // 2
    qr_y = HEIGHT - qr_size - 56
    draw.rounded_rectangle(
        [(qr_x - 8, qr_y - 8), (qr_x + qr_size + 8, qr_y + qr_size + 8)],
        radius=10,
        fill=WHITE,
        outline=PURPLE,
        width=2,
    )
    img.paste(qr_img, (qr_x, qr_y))

    draw.text((WIDTH // 2, HEIGHT - 18), "La Rifa", font=font_label, fill=MUTED, anchor="mm")

    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
