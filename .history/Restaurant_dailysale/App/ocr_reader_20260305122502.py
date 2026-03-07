import pytesseract
import cv2
import re
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    # Read image
    img = cv2.imread(file_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Improve contrast
    gray = cv2.equalizeHist(gray)

    # Threshold for sharper text
    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # OCR read
    text = pytesseract.image_to_string(
        thresh,
        config="--psm 6"
    )

    text = text.lower()

    # Remove currency symbols
    text = re.sub(r'[\$₹€£]', '', text)

    # Remove currency codes
    text = re.sub(r'\b(usd|inr|aed|eur|gbp)\b', '', text)

    patterns = [
        r'grand\s*total\s*([\d,.]+)',
        r'total\s*([\d,.]+)',
        r'amount\s*payable\s*([\d,.]+)',
        r'net\s*amount\s*([\d,.]+)'
    ]

    # Search for total patterns
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(",", "")

    # Fallback: detect all currency numbers
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:
        return max(numbers, key=lambda x: float(x))

    return None