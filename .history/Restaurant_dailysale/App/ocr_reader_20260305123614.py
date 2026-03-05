import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.GaussianBlur(gray, (5,5), 0)

    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(thresh)

    print("OCR TEXT:\n", text)

    text = text.lower()

    # remove currency symbols
    text = re.sub(r'[\$₹€£]', '', text)

    # keywords to search
    keywords = [
        "grand total",
        "invoice total",
        "total amount",
        "net total",
        "balance due",
        "total"
    ]

    # search keyword-based totals
    for word in keywords:
        pattern = rf'{word}[^0-9]*([\d]+\.[\d]+)'
        match = re.search(pattern, text)

        if match:
            return round(float(match.group(1)), 2)

    # fallback: detect all amounts
    numbers = re.findall(r'\d+\.\d{2,3}', text)

    if numbers:

        numbers = [round(float(n), 2) for n in numbers]

        # return largest value (usually invoice total)
        return max(numbers)

    return None