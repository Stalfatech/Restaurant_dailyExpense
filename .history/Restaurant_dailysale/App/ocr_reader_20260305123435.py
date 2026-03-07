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

    # remove currency
    text = re.sub(r'[\$₹€£]', '', text)

    # -------- find TOTAL line --------
    total_match = re.search(r'total[^0-9]*([\d]+\.[\d]+)', text)

    if total_match:
        amount = total_match.group(1)

        # fix OCR mistake like 684.694 -> 684.69
        amount = round(float(amount), 2)

        return amount

    # fallback: get highest amount
    numbers = re.findall(r'\d+\.\d{2,3}', text)

    if numbers:
        numbers = [round(float(n),2) for n in numbers]
        return max(numbers)

    return None