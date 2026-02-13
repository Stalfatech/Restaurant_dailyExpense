import re
from google.cloud import vision

def extract_amount_line_from_text(text):
    """
    Return the full line containing the amount, prioritizing:
    1. Grand Total
    2. Total
    3. Amount Due
    4. Net Total
    Fallback: line with highest number
    """
    lines = text.split('\n')
    keywords = ["grand total", "total", "amount due", "net total"]

    # Look for keyword matches first
    for line in lines:
        lower_line = line.lower()
        for keyword in keywords:
            if keyword in lower_line:
                return line.strip()  # return full line

    # Fallback: line containing the largest number
    number_lines = []
    for line in lines:
        numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', line)
        if numbers:
            largest = max([float(n.replace(',', '')) for n in numbers])
            number_lines.append((largest, line.strip()))
    if number_lines:
        return max(number_lines, key=lambda x: x[0])[1]

    return None

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

def extract_numeric_from_text(line_text):
    """
    Extract the first valid float number from a text line
    """
    import re
    if not line_text:
        return None
    numbers = re.findall(r'\d+(?:[.,]\d{1,2})?', line_text)
    if numbers:
        # remove commas and convert to float
        return float(numbers[0].replace(',', ''))
    return None
