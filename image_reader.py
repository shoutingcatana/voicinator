from PIL import Image
import pytesseract as tess
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tess.pytesseract.tesseract_cmd = (tesseract_path)


def extract_text(path):
    img = Image.open(path)
    text = tess.image_to_string(img)
    return text

