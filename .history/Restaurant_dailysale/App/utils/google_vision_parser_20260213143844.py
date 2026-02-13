import re
from google.cloud import vision


def extract_amount_from_text(text):
    
    text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        lower_line = line.lower()

        if "grand total" in lower_line:

            # Only detect numbers that look like money (with decimal)
            match = re.search(r'([\d]+\.\d{2})', line)
            if match:
                return float(match.group(1))

            # Check next line only
            if i + 1 < len(lines):
                match = re.search(r'([\d]+\.\d{2})', lines[i + 1])
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
