import re
from google.cloud import vision


def extract_invoice_fields(text):

    data = {}

    # Remove commas for numeric parsing
    clean_text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    lower_text = clean_text.lower()

    # Invoice Number
    inv_match = re.search(r'invoice\s*no[:\s]*([A-Za-z0-9-]+)', lower_text)
    if inv_match:
        data["invoice_number"] = inv_match.group(1)

    # Invoice Date
    date_match = re.search(r'invoice\s*date[:\s]*([0-9A-Za-z-]+)', lower_text)
    if date_match:
        data["invoice_date"] = date_match.group(1)

    # Phone
    phone_match = re.search(r'phone[:\s]*([0-9\s]+)', lower_text)
    if phone_match:
        data["phone"] = phone_match.group(1).strip()

    # Subtotal
    subtotal_match = re.search(r'sub\s*total[^0-9]*([0-9]+\.[0-9]{2})', clean_text, re.IGNORECASE)
    if subtotal_match:
        data["subtotal"] = subtotal_match.group(1)

    # Tax
    tax_match = re.search(r'tax[^0-9]*([0-9]+\.[0-9]{2})', clean_text, re.IGNORECASE)
    if tax_match:
        data["tax"] = tax_match.group(1)

    # Grand Total
    grand_match = re.search(r'grand\s*total[^0-9]*([0-9]+\.[0-9]{2})', clean_text, re.IGNORECASE)
    if grand_match:
        data["grand_total"] = grand_match.group(1)

    return data


def extract_invoice_data(file_path):
    client = vision.ImageAnnotatorClient()

    with open(file_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    texts = response.text_annotations

    if texts:
        full_text = texts[0].description
        return extract_invoice_fields(full_text)

    return {}
