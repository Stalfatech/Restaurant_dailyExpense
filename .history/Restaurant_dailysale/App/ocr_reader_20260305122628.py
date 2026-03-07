import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    # simple preprocessing (more reliable)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(gray, config="--psm 6")

    print("========= OCR TEXT =========")
    print(text)
    print("============================")

    text = text.lower()

    # remove currency symbols
    text = re.sub(r'[\$₹€£]', '', text)

    patterns = [
        r'grand\s*total\s*([\d,.]+)',
        r'total\s*([\d,.]+)',
        r'amount\s*payable\s*([\d,.]+)',
        r'net\s*amount\s*([\d,.]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(",", "")

    # fallback
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:
        return max(numbers, key=lambda x: float(x))

    return None