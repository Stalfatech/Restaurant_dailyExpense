import re
from google.cloud import vision


def extract_amount_from_text(text):
    """
    Smart detection of invoice total amount.
    Priority:
    1. Grand Total
    2. Total
    3. Amount Due
    4. Net Total
    5. Fallback to highest number
    """

    lines = text.split('\n')

    keywords = [
        "grand total",
        "total",
        "amount due",
        "net total"
    ]

    # 1️⃣ First try keyword-based extraction
    for line in lines:
        lower_line = line.lower()

        for keyword in keywords:
            if keyword in lower_line:
                numbers = re.findall(r'\d+(?:\.\d{1,2})?', line)
                if numbers:
                    return float(numbers[-1])  # Usually last number in line is total

    # 2️⃣ Fallback: highest number in document
    all_numbers = re.findall(r'\d+(?:\.\d{1,2})?', text)

    if all_numbers:
        return max([float(n) for n in all_numbers])

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
