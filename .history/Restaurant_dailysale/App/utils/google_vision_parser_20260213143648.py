import re
from google.cloud import vision


def extract_amount_from_text(text):

    # Normalize text
    text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Join lines for better detection
    full_text = " ".join(lines).lower()

    # 🔹 1️⃣ Strict Grand Total detection
    patterns = [
        r'grand\s*total[^0-9]*([\d]+(?:\.\d{1,2})?)',
        r'total\s*amount[^0-9]*([\d]+(?:\.\d{1,2})?)',
        r'amount\s*due[^0-9]*([\d]+(?:\.\d{1,2})?)',
        r'net\s*total[^0-9]*([\d]+(?:\.\d{1,2})?)',
        r'\btotal[^0-9]*([\d]+(?:\.\d{1,2})?)'
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # 🔴 STRICT MODE: Do NOT fallback
    return None


def extract_amount_from_invoice(file_path):
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

    return None
