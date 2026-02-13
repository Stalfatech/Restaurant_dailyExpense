import re
from google.cloud import vision


def extract_amount_from_text(text):
    """
    Extract ONLY Grand Total / Total Amount.
    Ignore phone numbers and random highest numbers.
    """

    # Normalize text
    text = text.replace(",", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        lower_line = line.lower()

        # Detect only grand total related lines
        if any(keyword in lower_line for keyword in [
            "grand total",
            "total amount",
            "amount due",
            "net total"
        ]):

            # Remove ₹ $ or other symbols
            clean_line = re.sub(r'[^\d\. ]', '', line)

            # Find decimal numbers only (ignore phone numbers)
            match = re.search(r'\d+\.\d{2}', clean_line)
            if match:
                return float(match.group())

            # Check next line if amount is below label
            if i + 1 < len(lines):
                next_line = re.sub(r'[^\d\. ]', '', lines[i + 1])
                match = re.search(r'\d+\.\d{2}', next_line)
                if match:
                    return float(match.group())

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
        print("FULL OCR TEXT:\n", full_text)  # Debug
        return extract_amount_from_text(full_text)

    return None
