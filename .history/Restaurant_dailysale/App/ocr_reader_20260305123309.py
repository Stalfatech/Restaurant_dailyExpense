import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    # Read image
    img = cv2.imread(file_path)

    # Resize (improves OCR accuracy)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # Threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2
    )

    # OCR
    text = pytesseract.image_to_string(thresh, config="--psm 6")

    print("OCR RESULT:\n", text)

    text = text.lower()

    # Remove currency
    text = re.sub(r'[\$₹€£]', '', text)
    text = re.sub(r'\b(usd|inr|aed|eur|gbp)\b', '', text)

    patterns = [
        r'grand\s*total[:\-\s]*([\d,.]+)',
        r'total[:\-\s]*([\d,.]+)',
        r'amount\s*payable[:\-\s]*([\d,.]+)',
        r'net\s*amount[:\-\s]*([\d,.]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))

    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:
        return float(max(numbers, key=lambda x: float(x)))

    return None