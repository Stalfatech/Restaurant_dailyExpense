import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    # Read image
    img = cv2.imread(file_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Improve text clarity
    gray = cv2.medianBlur(gray, 3)

    # Increase contrast
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # OCR read
    text = pytesseract.image_to_string(
        thresh,
        config="--oem 3 --psm 6"
    )

    print("OCR TEXT:", text)  # Debug

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

    # Search patterns first
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(",", "")

    # Fallback: pick highest amount
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:
        return max(numbers, key=lambda x: float(x))

    return None