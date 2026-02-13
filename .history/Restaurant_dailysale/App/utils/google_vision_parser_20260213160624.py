import re
from google.cloud import vision

def extract_amount_line_from_text(text):
    """
    Return the line containing the total amount.
    Priority keywords first, fallback to largest number.
    """
    lines = text.split('\n')
    keywords = [
        "grand total", "total", "amount due", "net total",
        "total amount", "balance due", "invoice total"
    ]

    # Search keywords first
    for line in lines:
        lower_line = line.lower()
        for keyword in keywords:
            if keyword in lower_line:
                return line.strip()

    # Fallback: pick the line with largest number
    number_lines = []
    for line in lines:
        numbers = re.findall(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?', line)
        if numbers:
            largest = max([float(n.replace(',', '').replace('$', '')) for n in numbers])
            number_lines.append((largest, line.strip()))
    if number_lines:
        return max(number_lines, key=lambda x: x[0])[1]

    return None

def extract_numeric_from_text(line_text):
    if not line_text:
        return None
    numbers = re.findall(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?', line_text)
    if numbers:
        return float(numbers[0].replace(',', '').replace('$', ''))
    return None

def extract_invoice_amount(file_path):
    client = vision.ImageAnnotatorClient()
    with open(file_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    texts = response.text_annotations
    if not texts:
        return None, None

    full_text = texts[0].description
    print("OCR Output:\n", full_text)  # Debug the full OCR text

    line_text = extract_amount_line_from_text(full_text)
    amount = extract_numeric_from_text(line_text)
    return line_text, amount

# Example usage
file_path = "/mnt/data/b5972d24-a70c-42e0-893c-ccb7eb335fee.png"
line, amount = extract_invoice_amount(file_path)
print("Detected line:", line)
print("Detected amount:", amount)
