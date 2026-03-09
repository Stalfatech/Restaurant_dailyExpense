import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    # Improve OCR quality
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OCR
    text = pytesseract.image_to_string(thresh, config="--psm 6")

    print("OCR TEXT:\n", text)

    text = text.lower()

    # remove currency
    text = re.sub(r'[\$₹€£]', '', text)

    # keywords
    keywords = [
        "grand total",
        "invoice total",
        "net total",
        "total amount",
        "amount payable",
        "balance due",
        "total"
    ]

    # Try keyword extraction
    for key in keywords:

        pattern = rf'{key}[^0-9]*([\d]+\.\d+)'
        match = re.search(pattern, text)

        if match:
            value = float(match.group(1))

            # ignore small totals like tax
            if value > 50:
                return value

    # Fallback: detect all numbers
    numbers = re.findall(r'\d+\.\d{2,3}', text)

    if numbers:

        numbers = [float(n) for n in numbers]

        # remove very small numbers
        numbers = [n for n in numbers if n > 50]

        if numbers:
            return max(numbers)

    return None