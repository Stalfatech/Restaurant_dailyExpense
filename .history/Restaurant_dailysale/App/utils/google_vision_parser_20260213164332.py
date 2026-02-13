import re
from google.cloud import vision

def extract_amount_from_text(text):
    """
    Extract numeric value from invoice text.
    Priority keywords: Grand Total, Total, Amount Due, Net Total
    Fallback: largest number found
    Returns numeric string like '1234.56'
    """
    lines = text.split('\n')
    keywords = ["grand total", "total", "amount due", "net total"]

    # 1. Look for keyword matches first
    for line in lines:
        lower_line = line.lower()
        for keyword in keywords:
            if keyword in lower_line:
                numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', line)
                if numbers:
                    # Take the largest number if multiple in line
                    amount = max([float(n.replace(',', '')) for n in numbers])
                    return f"{amount:.2f}"

    # 2. Fallback: largest number in entire text
    all_numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', text)
    if all_numbers:
        amount = max([float(n.replace(',', '')) for n in all_numbers])
        return f"{amount:.2f}"

    return ""  # return empty string if nothing found


def extract_amount_from_invoice(file_path):
    """
    Uses Google Vision OCR to extract numeric total amount from invoice.
    """
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
        return extract_amount_from_text(full_text)

    return ""
