import re
from google.cloud import vision


import re

def extract_amount_from_text(text):

    # Normalize
    text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        lower_line = line.lower()

        if "grand total" in lower_line:

            # Look for proper money format ONLY (must have decimal)
            money_pattern = r'₹?\$?\s*([0-9]{1,9}\.[0-9]{2})'

            # 1️⃣ Check same line
            match = re.search(money_pattern, line)
            if match:
                return float(match.group(1))

            # 2️⃣ Check next 2 lines (OCR safety)
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j]
                    match = re.search(money_pattern, next_line)
                    if match:
                        return float(match.group(1))

    # ❌ NO FALLBACK
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
