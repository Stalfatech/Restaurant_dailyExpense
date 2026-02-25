from django.core.mail import EmailMessage, get_connection
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from urllib.parse import quote
from django.shortcuts import redirect
from .models import CommunicationSettings


def generate_pdf(template, context):
    html = get_template(template).render(context)
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    return result


def send_email(to_email, subject, body, pdf):
    config = CommunicationSettings.objects.first()

    connection = get_connection(
        host=config.email_host,
        port=config.email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=config.use_tls,
    )

    email = EmailMessage(
        subject,
        body,
        config.email_host_user,
        [to_email],
        connection=connection
    )

    email.attach("Report.pdf", pdf.getvalue(), "application/pdf")
    email.send()


def send_whatsapp(number, message):
    url = f"https://wa.me/{number}?text={quote(message)}"
    return redirect(url)


from django.core.mail import EmailMessage, get_connection
from urllib.parse import quote
from django.shortcuts import redirect
from .models import CommunicationSettings


def send_email_report(client_email, subject, body, pdf_file=None):
    config = CommunicationSettings.objects.first()
    if not config or not config.email_host_user:
        return

    connection = get_connection(
        host=config.email_host,
        port=config.email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=config.use_tls,
    )

    recipients = [client_email, config.email_host_user]

    email = EmailMessage(
        subject,
        body,
        config.email_host_user,
        recipients,
        connection=connection
    )

    if pdf_file:
        email.attach("Report.pdf", pdf_file.getvalue(), "application/pdf")

    email.send()


def send_whatsapp_report(client_number, message):
    config = CommunicationSettings.objects.first()
    admin_number = config.whatsapp_number if config else None

    # Send to client first
    if client_number:
        return redirect(f"https://wa.me/{client_number}?text={quote(message)}")

    # If no client, send to admin
    if admin_number:
        return redirect(f"https://wa.me/{admin_number}?text={quote(message)}")