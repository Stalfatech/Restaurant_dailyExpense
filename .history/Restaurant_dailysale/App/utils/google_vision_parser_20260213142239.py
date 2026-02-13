import re
from google.cloud import vision


def extract_amount_from_text(text):
    """
    Extract highest monetary value from text.
    """
    matches = re.findall(r'\d+(?:\.\d{1,2})?', text)

    if matches:
        numbers = [float(m) for m in matches]
        return max(numbers)

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
