import easyocr

class OCRParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OCRParser, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, use_gpu=False):
        if getattr(self, '_initialized', False):
            return
        # Initialize EasyOCR reader once (run on CPU to free up VRAM for Ollama)
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)
        self._initialized = True

    def extract_text(self, image_path):
        try:
            results = self.reader.readtext(image_path)
            # Combine all detected text blocks into a single string
            extracted_text = " ".join([result[1] for result in results])
            return extracted_text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
