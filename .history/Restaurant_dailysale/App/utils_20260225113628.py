# utils.py
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    return result