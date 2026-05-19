from abc import ABC, abstractmethod
import pytesseract
import fitz  # PyMuPDF
import PyPDF2
from PIL import Image
import io
import os

# Abstract base class
class BaseParser(ABC):
    
    @abstractmethod
    def parse(self, filepath: str) -> str:
        pass

# TextParser - reads .txt files
class TextParser(BaseParser):
    
    def parse(self, filepath: str) -> str:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            return text
        except Exception as e:
            return f"Error reading file: {e}"

# PDFParser - reads .pdf files
class PDFParser(BaseParser):
    
    def parse(self, filepath: str) -> str:
        # First try normal PDF text extraction
        text = self.extract_with_pypdf2(filepath)
        
        # If no text found, use OCR (scanned PDF)
        if not text.strip():
            text = self.extract_with_ocr(filepath)
        
        return text
    
    def extract_with_pypdf2(self, filepath: str) -> str:
        try:
            text = ""
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            return ""
    
    def extract_with_ocr(self, filepath: str) -> str:
        try:
            text = ""
            # Open PDF with fitz (PyMuPDF)
            doc = fitz.open(filepath)
            for page in doc:
                # Convert page to image
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                # Run OCR on image
                text += pytesseract.image_to_string(img)
            return text
        except Exception as e:
            return f"OCR Error: {e}"

# ParserFactory - automatically picks right parser
class ParserFactory:
    
    @staticmethod
    def get_parser(filepath: str) -> BaseParser:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".txt":
            return TextParser()
        elif ext == ".pdf":
            return PDFParser()
        else:
            raise ValueError(f"Unsupported file type: {ext}")

# FileParser - single interface for everything
class FileParser:
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def parse(self) -> str:
        parser = ParserFactory.get_parser(self.filepath)
        return parser.parse(self.filepath)


# Test it!
if __name__ == "__main__":
    parser = FileParser()
    
    print("=== Testing TXT file ===")
    txt_result = parser.parse("/usercode/obama.txt")
    print(txt_result[:200])
    
    print("\n=== Testing Normal PDF ===")
    pdf_result = parser.parse("/usercode/obama.pdf")
    print(pdf_result[:200])
    
    print("\n=== Testing Scanned PDF (OCR) ===")
    ocr_result = parser.parse("/usercode/obama-ocr.pdf")
    print(ocr_result[:200])