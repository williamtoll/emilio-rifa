import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings
from app.models import Ticket
from app.services.ticket_message import build_ticket_message
from app.services.ticket_image_service import generate_ticket_image
from app.utils.currency import format_guaranies


def _html_ticket(ticket: Ticket, message: str) -> str:
    raffle = ticket.raffle
    price = float(raffle.ticket_price) if raffle.ticket_price else 0
    paid = "Pagado" if ticket.is_paid else "Pendiente de pago"
    paid_color = "#16a34a" if ticket.is_paid else "#ca8a04"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
      <div style="border: 2px solid #7c3aed; border-radius: 12px; padding: 24px; text-align: center;">
        <h1 style="color: #7c3aed; margin: 0;">🎟️ Ticket de Sorteo</h1>
        <p style="color: #666; font-size: 14px;">{raffle.name}</p>
        <div style="background: #f3f4f6; border-radius: 8px; padding: 16px; margin: 20px 0;">
          <p style="font-size: 32px; font-weight: bold; color: #1f2937; margin: 0;">#{ticket.ticket_number}</p>
        </div>
        <table style="width: 100%; text-align: left; font-size: 14px;">
          <tr><td style="padding: 6px 0; color: #666;">Participante</td><td style="padding: 6px 0;"><strong>{ticket.buyer_name}</strong></td></tr>
          <tr><td style="padding: 6px 0; color: #666;">Precio</td><td style="padding: 6px 0;"><strong>{format_guaranies(price)}</strong></td></tr>
          <tr><td style="padding: 6px 0; color: #666;">Estado</td><td style="padding: 6px 0; color: {paid_color};"><strong>{paid}</strong></td></tr>
        </table>
        <p style="color: #666; font-size: 13px; margin-top: 20px;">{message.replace(chr(10), '<br>')}</p>
      </div>
    </body>
    </html>
    """


async def send_ticket_email(ticket: Ticket, custom_message: str | None = None) -> None:
    if not ticket.buyer_email:
        raise ValueError("El ticket no tiene correo electrónico registrado")
    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("Configura SMTP_USER y SMTP_PASSWORD en las variables de entorno")

    message_text = build_ticket_message(ticket, custom_message)
    raffle = ticket.raffle

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Ticket #{ticket.ticket_number} - {raffle.name}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = ticket.buyer_email

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(message_text, "plain", "utf-8"))
    body.attach(MIMEText(_html_ticket(ticket, message_text), "html", "utf-8"))
    msg.attach(body)

    image_bytes = generate_ticket_image(ticket)
    attachment = MIMEImage(image_bytes, _subtype="png")
    attachment.add_header("Content-Disposition", "attachment", filename=f"ticket-{ticket.ticket_number}.png")
    msg.attach(attachment)

    context = ssl.create_default_context()
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
        tls_context=context,
    )
