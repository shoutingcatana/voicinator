from PIL import Image
import pytesseract as tess
import io
from pdf2image import convert_from_path

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tess.pytesseract.tesseract_cmd = (tesseract_path)


def extract_text_from_image(image_data):
    image = Image.open(io.BytesIO(image_data))
    text = tess.image_to_string(image)
    return text


def convert_pdf_to_images(pdf_path):
    # Konvertiert alle Seiten der PDF in Bilder
    images = convert_from_path(pdf_path, poppler_path=r"C:\Users\hauer\PycharmProjects\voicinator\Release-24.07.0-0"
                                                      r" (1)\poppler-24.07.0\Library\bin")
    return images



