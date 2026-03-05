import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    text = pytesseract.image_to_string(gray, config="--psm 6")

    print("OCR TEXT:\n", text)

    text = text.lower()

    # remove currency
    text = re.sub(r'[\$₹€£]', '', text)

    # keywords
    keywords = [
        "grand total",
        "invoice total",
        "net total",
        "amount payable",
        "balance due",
        "total"
    ]

    detected_values = []

    for key in keywords:

        pattern = rf'{key}[^0-9]*([\d,]+\.\d+)'

        matches = re.findall(pattern, text)

        for m in matches:
            detected_values.append(float(m.replace(",", "")))

    # If totals found → return biggest one
    if detected_values:
        return max(detected_values)

    # Fallback → detect all numbers
    numbers = re.findall(r'\d+\.\d{2}', text)

    numbers = [float(n) for n in numbers if float(n) > 50]

    if numbers:
        return max(numbers)

    return None