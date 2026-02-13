import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_amount_from_text(text):
    # Basic regex for currency values
    matches = re.findall(r'\d+(?:\.\d{1,2})?', text)


    if matches:
        # Return highest value (usually total amount)
        return max([float(m) for m in matches])
    return None


def extract_amount_from_invoice(file_path):
    text = ""

    if file_path.lower().endswith('.pdf'):
        pages = convert_from_path(file_path, poppler_path=r"C:\poppler\Library\bin")
        for page in pages:
            text += pytesseract.image_to_string(page)
    else:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)

    print("========== OCR TEXT ==========")
    print(text)
    print("========== END OCR ==========")

    return extract_amount_from_text(text)

