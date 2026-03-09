import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    # Improve OCR accuracy
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    thresh = cv2.adaptiveThreshold(
        gray,255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,2
    )

    text = pytesseract.image_to_string(thresh)

    print("OCR TEXT:\n", text)

    text = text.lower()

    # Remove currency symbols and codes
    text = re.sub(r'[\$₹€£]', '', text)
    text = re.sub(r'\b(usd|inr|aed|eur|gbp)\b', '', text)

    patterns = [
        r'grand\s*total\s*([\d,.]+)',
        r'invoice\s*total\s*([\d,.]+)',
        r'net\s*total\s*([\d,.]+)',
        r'amount\s*payable\s*([\d,.]+)',
        r'total\s*[:\-]?\s*([\d,.]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(",", "")
            return value

    # Fallback → detect all amounts
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:

        numbers = [float(x) for x in numbers]

        # Ignore very small values (tax etc.)
        numbers = [x for x in numbers if x > 50]

        # Return the largest realistic amount
        if numbers:
            return str(max(numbers))

    return None