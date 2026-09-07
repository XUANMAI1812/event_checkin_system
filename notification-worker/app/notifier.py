import smtplib
from email.message import EmailMessage

from .config import settings


def send_ticket_email(
    to_email: str, full_name: str, ticket_id: str, qr_code_path: str
) -> None:
    """mail test smtp fake test local, doi that sau"""
    msg = EmailMessage()
    msg["Subject"] = "Ve tham du su kien cua ban"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"Chao {full_name},\n\n"
        f"Ve cua ban (ticket_id: {ticket_id}) da san sang. "
        f"Anh QR dinh kem, xuat trinh khi check-in."
    )

    with open(qr_code_path, "rb") as f:
        qr_bytes = f.read()
    msg.add_attachment(
        qr_bytes, maintype="image", subtype="png", filename=f"{ticket_id}.png"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.send_message(msg)
