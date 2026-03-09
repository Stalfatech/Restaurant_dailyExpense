import pytesseract
import cv2
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_invoice_amount(file_path):

    img = cv2.imread(file_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    blur = cv2.GaussianBlur(gray, (5,5), 0)

    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(thresh, config="--psm 6")

    print("OCR TEXT:\n", text)

    text = text.lower()

    # remove currency symbols
    text = re.sub(r'[\$₹€£]', '', text)

    lines = text.split("\n")

    # STEP 1: search lines containing total keywords
    keywords = [
        "grand total",
        "invoice total",
        "net total",
        "amount payable",
        "balance due",
        "total"
    ]

    for line in lines:

        for key in keywords:

            if key in line:

                nums = re.findall(r'\d+\.\d{2}', line)

                if nums:
                    return float(nums[-1])

    # STEP 2: search near TOTAL word (OCR distorted)
    for line in lines:

        if "tot" in line:

            nums = re.findall(r'\d+\.\d{2}', line)

            if nums:
                return float(nums[-1])

    # STEP 3: fallback (largest realistic number)
    numbers = re.findall(r'\d+\.\d{2}', text)

    if numbers:

        numbers = [float(n) for n in numbers]

        # remove tiny numbers like tax
        numbers = [n for n in numbers if n > 50]

        if numbers:
            return max(numbers)

    return None