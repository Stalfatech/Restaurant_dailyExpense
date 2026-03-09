import pytesseract
import cv2
import re
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    # Improve OCR accuracy
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    text = pytesseract.image_to_string(thresh)

    text = text.lower()

    # Remove currency symbols
    text = re.sub(r'[\$₹€£]', '', text)
    text = re.sub(r'\b(usd|inr|eur|aed|gbp)\b', '', text)

    # Look for TOTAL first
    lines = text.split("\n")

    for line in lines:
        if "total" in line:
            numbers = re.findall(r'\d+\.\d{2}', line)
            if numbers:
                return numbers[-1]

    # Fallback: get all numbers and return highest
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:
        return max(numbers, key=lambda x: float(x))

    return None