import re
from google.cloud import vision


def extract_amount_from_text(text):
    
    # Normalize
    text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        lower_line = line.lower()

        if "grand total" in lower_line:

            # 🔹 Search in same line (with optional currency symbol)
            match = re.search(r'₹?\$?\s*([\d]+\.\d{2})', line)
            if match:
                return float(match.group(1))

            # 🔹 Search in next 2 lines (OCR may break layout)
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j]
                    match = re.search(r'₹?\$?\s*([\d]+\.\d{2})', next_line)
                    if match:
                        return float(match.group(1))

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
