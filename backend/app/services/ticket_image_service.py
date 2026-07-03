from io import BytesIO
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from app.models import Ticket
from app.services.ticket_urls import get_short_ticket_url
from app.utils.currency import format_guaranies

WIDTH = 420
RAFFLES_UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "raffles"
RAFFLE_IMG_MAX_W = 372
RAFFLE_IMG_MAX_H = 100
PURPLE = (124, 58, 237)
PURPLE_DARK = (91, 33, 182)
WHITE = (255, 255, 255)
BG = (250, 250, 252)
TEXT = (31, 41, 55)
MUTED = (107, 114, 128)
GREEN = (22, 163, 74)
YELLOW = (202, 138, 4)
PRIZE_GOLD = (161, 110, 0)


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


def _count_wrapped_lines(text: str, font, max_width: int) -> int:
    words = text.split()
    if not words:
        return 1
    lines = 1
    current = ""
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for word in words:
        test = f"{current} {word}".strip()
        bbox = dummy.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            lines += 1
            current = word
    return lines


def _estimate_fields_height(fields: list[tuple[str, str]], font_label, font_value, max_width: int) -> int:
    total = 0
    for _, value in fields:
        total += 16
        lines = _count_wrapped_lines(value, font_value, max_width)
        total += lines * _font_line_height(font_value) + 12
    return total


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


def _load_raffle_image(raffle) -> Image.Image | None:
    if not raffle.image_filename:
        return None
    path = RAFFLES_UPLOADS_DIR / raffle.image_filename
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGB")
    except OSError:
        return None


def _fit_image(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    ratio = min(max_w / img.width, max_h / img.height, 1.0)
    if ratio >= 1.0:
        return img
    new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def generate_ticket_image(ticket: Ticket) -> bytes:
    raffle = ticket.raffle
    price = float(raffle.ticket_price) if raffle.ticket_price else 0
    paid = ticket.is_paid
    status_text = "PAGADO" if paid else "PENDIENTE"
    status_color = GREEN if paid else YELLOW

    prizes = sorted(raffle.prizes, key=lambda p: p.order) if getattr(raffle, "prizes", None) else []

    font_title = _load_font(26, bold=True)
    font_brand = _load_font(14)
    font_number = _load_font(52, bold=True)
    font_label = _load_font(12)
    font_value = _load_font(16, bold=True)
    font_status = _load_font(13, bold=True)
    font_prize_label = _load_font(11, bold=True)
    font_prize_name = _load_font(14)
    font_desc = _load_font(14)

    fields = [("Sorteo", raffle.name)]
    if raffle.description and raffle.description.strip():
        fields.append(("Descripción", raffle.description.strip()))
    fields.extend([
        ("Participante", ticket.buyer_name),
        ("Precio", format_guaranies(price)),
    ])

    fields_height = _estimate_fields_height(fields, font_label, font_value, WIDTH - 72)

    raffle_img = _load_raffle_image(raffle)
    if raffle_img:
        raffle_img = _fit_image(raffle_img, RAFFLE_IMG_MAX_W, RAFFLE_IMG_MAX_H)
    raffle_img_section = (raffle_img.height + 20) if raffle_img else 0

    prizes_section_height = 0
    if prizes:
        for prize in prizes:
            lines = _count_wrapped_lines(prize.name, font_prize_name, WIDTH - 92)
            prizes_section_height += max(22, lines * _font_line_height(font_prize_name))
        prizes_section_height += 12 + 18 + 4 + 8

    QR_SIZE = 140
    QR_BOTTOM_PADDING = 56
    FOOTER_H = 30
    HEADER_AND_NUMBER = 92 + 16 + 92 + 20
    BADGE_H = 40
    FIXED_ABOVE_QR = HEADER_AND_NUMBER + raffle_img_section + fields_height + BADGE_H
    HEIGHT = max(640, FIXED_ABOVE_QR + prizes_section_height + QR_SIZE + QR_BOTTOM_PADDING + FOOTER_H)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (WIDTH, 88)], fill=PURPLE)
    draw.rectangle([(0, 88), (WIDTH, 92)], fill=PURPLE_DARK)

    draw.text((WIDTH // 2, 28), "La Rifa", font=font_title, fill=WHITE, anchor="mm")
    draw.text((WIDTH // 2, 58), "TICKET DE SORTEO", font=font_brand, fill=(220, 210, 255), anchor="mm")

    draw.rounded_rectangle([(24, 108), (WIDTH - 24, 200)], radius=12, fill=WHITE, outline=PURPLE, width=2)
    draw.text((WIDTH // 2, 148), f"#{ticket.ticket_number}", font=font_number, fill=PURPLE, anchor="mm")

    y = 212
    if raffle_img:
        img_x = (WIDTH - raffle_img.width) // 2
        draw.rounded_rectangle(
            [(img_x - 4, y - 4), (img_x + raffle_img.width + 4, y + raffle_img.height + 4)],
            radius=8,
            fill=WHITE,
            outline=PURPLE,
            width=1,
        )
        img.paste(raffle_img, (img_x, y))
        y += raffle_img.height + 16

    for label, value in fields:
        draw.text((36, y), label.upper(), font=font_label, fill=MUTED)
        value_font = font_desc if label == "Descripción" else font_value
        value_color = MUTED if label == "Descripción" else TEXT
        y = _draw_wrapped_text(draw, value, (36, y + 16), value_font, value_color, WIDTH - 72) + 12

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

    y = badge_y + badge_h + 12

    if prizes:
        draw.line([(36, y + 6), (WIDTH - 36, y + 6)], fill=(220, 215, 240), width=1)
        y += 12
        draw.text((36, y), "PREMIOS", font=font_prize_label, fill=PRIZE_GOLD)
        y += 18 + 4
        for i, prize in enumerate(prizes):
            bullet = f"{i + 1}."
            draw.text((36, y), bullet, font=font_prize_name, fill=PRIZE_GOLD)
            y = _draw_wrapped_text(draw, prize.name, (56, y), font_prize_name, TEXT, WIDTH - 92) + 6
        y += 8

    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(build_qr_payload(ticket))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)

    qr_x = (WIDTH - QR_SIZE) // 2
    qr_y = HEIGHT - QR_SIZE - QR_BOTTOM_PADDING
    draw.rounded_rectangle(
        [(qr_x - 8, qr_y - 8), (qr_x + QR_SIZE + 8, qr_y + QR_SIZE + 8)],
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
