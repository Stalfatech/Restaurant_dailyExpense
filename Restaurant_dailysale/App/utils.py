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


# ================= EMAIL (MAIN) =================
from django.core.mail import EmailMessage, get_connection
from .models import CommunicationSettings

def send_email_report(client_email, subject, body, pdf_file=None):
    """
    Sends report to:
    1. Client email (if provided)
    2. Admin email (from active Communication Settings)
    """

    # Get active email config
    try:
        config = CommunicationSettings.objects.filter(is_active=True).first()
    except CommunicationSettings.DoesNotExist:
        config = None

    if not config:
        raise Exception("No active Communication Settings found")

    # Validate all required email fields
    required_fields = ['email_host', 'email_port', 'email_host_user', 'email_host_password']
    missing = [f for f in required_fields if not getattr(config, f)]
    if missing:
        raise Exception(f"Email settings incomplete: missing {', '.join(missing)}")

    # Setup SMTP connection
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=config.email_host,
        port=config.email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=True,
        use_ssl=False,
        timeout=30,
    )

    # ===== Recipients =====
    recipients = []
    if client_email:
        recipients.append(client_email)

    if config.email_host_user not in recipients:
        recipients.append(config.email_host_user)

    if not recipients:
        raise Exception("No recipient email provided")

    # ===== Send Email =====
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
from urllib.parse import quote
from django.shortcuts import redirect


def send_whatsapp(number, message):
    if not number:
        return None

    url = f"https://wa.me/{number}?text={quote(message)}"
    return redirect(url)


def send_whatsapp_report(client_number, message):
    """
    Opens WhatsApp for:
    1. Client number (if provided)
    2. Otherwise admin number
    """
    config = CommunicationSettings.objects.first()
    admin_number = config.whatsapp_number if config else None

    # Send to client first
    if client_number:
        return send_whatsapp(client_number, message)

    # Otherwise admin
    if admin_number:
        return send_whatsapp(admin_number, message)

    return None



import os
from django.conf import settings
from datetime import datetime


def save_pdf_and_get_link(request, pdf_file):
    # Create reports folder
    folder_path = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(folder_path, exist_ok=True)

    # Unique file name
    file_name = f"delivery_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    file_path = os.path.join(folder_path, file_name)

    # Save file
    with open(file_path, "wb") as f:
        f.write(pdf_file.getvalue())

    # Return full URL
    file_url = settings.MEDIA_URL + "reports/" + file_name
    return request.build_absolute_uri(file_url)