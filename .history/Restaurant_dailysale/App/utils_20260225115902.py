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