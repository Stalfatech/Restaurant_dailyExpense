import pytesseract
import re
import cv2
from pdf2image import convert_from_path
from PIL import Image


def extract_invoice_amount(file_path):

    text = ""

    # PDF support
    if file_path.lower().endswith(".pdf"):
        images = convert_from_path(file_path)
        for img in images:
            text += pytesseract.image_to_string(img)

    else:
        img = cv2.imread(file_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)

    text = text.lower()

    patterns = [
        r'grand total[:\s]*([\d,.]+)',
        r'amount payable[:\s]*([\d,.]+)',
        r'net amount[:\s]*([\d,.]+)',
        r'total amount[:\s]*([\d,.]+)',
        r'total[:\s]*([\d,.]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(",", "")

    return None