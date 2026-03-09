import pytesseract
import cv2
import re
import numpy as np
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\poppler\Library\bin\poppler-windows-25.12.0-0.zip\poppler-windows-25.12.0-0"


def extract_invoice_amount(file_path):

    images = []

    # ---------- HANDLE PDF ----------
    if file_path.lower().endswith(".pdf"):

        pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)

        for page in pages:
            img = np.array(page)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            images.append(img)

    # ---------- HANDLE IMAGE ----------
    else:
        img = cv2.imread(file_path)
        images.append(img)

    detected_values = []

    for img in images:

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        text = pytesseract.image_to_string(gray, config="--psm 6")

        print("OCR TEXT:\n", text)

        text = text.lower()

        text = re.sub(r'[\$₹€£]', '', text)

        keywords = [
            "grand total",
            "invoice total",
            "net total",
            "amount payable",
            "balance due",
            "total"
        ]

        for key in keywords:

            pattern = rf'{key}[^0-9]*([\d,]+\.\d+)'

            matches = re.findall(pattern, text)

            for m in matches:
                detected_values.append(float(m.replace(",", "")))

        numbers = re.findall(r'\d+\.\d{2}', text)

        numbers = [float(n) for n in numbers if float(n) > 50]

        detected_values.extend(numbers)

    if detected_values:
        return max(detected_values)

    return None