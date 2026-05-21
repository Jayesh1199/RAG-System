from abc import ABC, abstractmethod
import PyPDF2
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
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

# PDFParser - reads .pdf files using PyPDF2 only
# OCR removed: pytesseract requires OS-level Tesseract binary
# which is not available on Render free tier
class PDFParser(BaseParser):
    
    def parse(self, filepath: str) -> str:
        try:
            text = ""
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            
            # If no text extracted, PDF is likely scanned
            # Return helpful message instead of crashing
            if not text.strip():
                return "This PDF appears to be scanned. Text extraction unavailable."
            
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

# ParserFactory - picks the right parser by file extension
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

# FileParser - single interface for all file types
class FileParser:
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def parse(self) -> str:
        parser = ParserFactory.get_parser(self.filepath)
        return parser.parse(self.filepath)
