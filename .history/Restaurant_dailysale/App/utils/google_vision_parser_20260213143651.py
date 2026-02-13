import re
from google.cloud import vision


def extract_amount_from_text(text):
    
    text = text.replace(",", "")  # remove commas
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        lower_line = line.lower()

        if "grand total" in lower_line:

            # Extract any number after "grand total"
            match = re.search(r'grand\s*total[^0-9]*([\d]+(?:\.\d{1,2})?)',
                              lower_line)

            if match:
                return float(match.group(1))

            # If amount is on next line
            if i + 1 < len(lines):
                match = re.search(r'([\d]+(?:\.\d{1,2})?)', lines[i + 1])
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
