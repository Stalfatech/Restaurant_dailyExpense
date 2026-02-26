from django.core.mail import EmailMessage, get_connection
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from urllib.parse import quote
from django.shortcuts import redirect
from .models import CommunicationSettings


# ================= PDF =================
def generate_pdf(template, context):
    html = get_template(template).render(context)
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    return result


# ================= EMAIL =================
def send_email(to_email, subject, body, pdf_file=None):
    config = CommunicationSettings.objects.first()

    if not config or not config.email_host_user:
        raise Exception("Email settings not configured")

    # Gmail Standard Configuration
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=config.email_host or 'smtp.gmail.com',
        port=config.email_port or 587,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=True,      # REQUIRED for Gmail (port 587)
        use_ssl=False,
        timeout=30,
    )

    # Send to client + admin copy
    recipients = [to_email]
    if config.email_host_user not in recipients:
        recipients.append(config.email_host_user)

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=config.email_host_user,
        to=recipients,
        connection=connection
    )

    if pdf_file:
        email.attach("Report.pdf", pdf_file.getvalue(), "application/pdf")

    email.send(fail_silently=False)


# ================= WHATSAPP =================
def send_whatsapp(number, message):
    if not number:
        return None
    url = f"https://wa.me/{number}?text={quote(message)}"
    return redirect(url)


def send_whatsapp_report(client_number, message):
    config = CommunicationSettings.objects.first()
    admin_number = config.whatsapp_number if config else None

    # Priority: client
    if client_number:
        return send_whatsapp(client_number, message)

    # Otherwise admin
    if admin_number:
        return send_whatsapp(admin_number, message)