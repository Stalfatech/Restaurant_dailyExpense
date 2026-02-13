import re
from google.cloud import vision

import re

def extract_amount_from_text(text):
    """
    Extract numeric value of the amount from text.
    Priority keywords: Grand Total, Total, Amount Due, Net Total
    Fallback: largest number in text
    Returns float as string.
    """
    lines = text.split('\n')
    keywords = ["grand total", "total", "amount due", "net total"]

    # Search for keyword matches first
    for line in lines:
        lower_line = line.lower()
        for keyword in keywords:
            if keyword in lower_line:
                # Extract numeric value from line
                numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', line)
                if numbers:
                    # Take the largest number in case multiple
                    amount = max([float(n.replace(',', '')) for n in numbers])
                    return f"{amount:.2f}"

    # Fallback: largest number in entire text
    all_numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', text)
    if all_numbers:
        amount = max([float(n.replace(',', '')) for n in all_numbers])
        return f"{amount:.2f}"

    return ""


def extract_amount_from_invoice(file_path):
    """
    Uses Google Vision OCR to extract the line containing the total amount.
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
        return extract_amount_line_from_text(full_text)

    return None
