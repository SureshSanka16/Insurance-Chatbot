"""
TR-OCR Text Extraction Module
Uses Microsoft's TrOCR (Transformer-based OCR) for extracting text from claim documents

TrOCR is a state-of-the-art OCR model that combines:
- Vision Transformer (ViT) for image understanding
- Transformer decoder for text generation
"""

from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import numpy as np
from typing import Union, List
import io
import pymupdf as fitz  # PyMuPDF for PDF handling


class TrOCRExtractor:
    """
    Extract text from claim document images using TrOCR
    
    Supports:
    - Handwritten text
    - Printed text
    - Forms and invoices
    - Multi-line documents
    """
    
    def __init__(self, model_name: str = "microsoft/trocr-base-printed"):
        """
        Initialize TrOCR model
        
        Args:
            model_name: HuggingFace model identifier
                - "microsoft/trocr-base-printed" - For printed text (default)
                - "microsoft/trocr-base-handwritten" - For handwritten text
                - "microsoft/trocr-large-printed" - Larger model for better accuracy
        """
        print(f"Loading TrOCR model: {model_name}...")
        
        try:
            self.processor = TrOCRProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            
            # Use GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            print(f"✓ TrOCR model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"✗ Error loading TrOCR model: {e}")
            print("\nTo install required packages:")
            print("pip install transformers torch pillow")
            raise
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract all text from a single image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text as string
        """
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Extract text
            text = self._process_image(image)
            
            return text
            
        except Exception as e:
            print(f"Error extracting text from {image_path}: {e}")
            return ""
    
    def extract_text_from_bytes(self, image_bytes: bytes, file_type: str = 'image') -> str:
        """
        Extract text from image or PDF bytes (for uploaded files)
        
        Args:
            image_bytes: Image or PDF data as bytes
            file_type: 'image' or 'pdf'
            
        Returns:
            Extracted text as string
        """
        try:
            # Check if it's a PDF
            if file_type == 'pdf' or image_bytes[:4] == b'%PDF':
                return self.extract_text_from_pdf_bytes(image_bytes)
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Extract text
            text = self._process_image(image)
            
            return text
            
        except Exception as e:
            print(f"Error extracting text from bytes: {e}")
            return ""
    
    def _process_image(self, image: Image.Image) -> str:
        """
        Process PIL Image and extract text
        
        For documents with multiple lines/sections, this method:
        1. Splits image into regions
        2. Processes each region
        3. Combines results
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            # For simple OCR (single region)
            text = self._extract_single_region(image)
            
            # If image is large, try splitting into regions for better accuracy
            width, height = image.size
            if height > 1000 or width > 1000:
                # Process in regions
                regions = self._split_image_into_regions(image)
                texts = [self._extract_single_region(region) for region in regions]
                text = "\n".join([t for t in texts if t.strip()])
            
            return text
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            print(f"Processing PDF: {pdf_path}")
            
            # Try to extract embedded text first (faster)
            text = self._extract_embedded_text_from_pdf(pdf_path)
            
            if text and len(text.strip()) > 50:
                print(f"✓ Extracted embedded text from PDF ({len(text)} chars)")
                return text
            
            # If no embedded text, convert to images and OCR
            print("No embedded text found, converting PDF to images...")
            text = self._extract_text_from_pdf_via_ocr(pdf_path)
            
            return text
            
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF data as bytes
            
        Returns:
            Extracted text
        """
        try:
            print("Processing PDF from bytes...")
            
            # Try embedded text first
            text = self._extract_embedded_text_from_pdf_bytes(pdf_bytes)
            
            if text and len(text.strip()) > 50:
                print(f"✓ Extracted embedded text from PDF ({len(text)} chars)")
                return text
            
            # Convert PDF to images and OCR
            print("No embedded text found, converting PDF to images...")
            text = self._extract_text_from_pdf_bytes_via_ocr(pdf_bytes)
            
            return text
            
        except Exception as e:
            print(f"Error extracting text from PDF bytes: {e}")
            return ""
    
    def _extract_embedded_text_from_pdf(self, pdf_path: str) -> str:
        """Extract embedded text from PDF (if available)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting embedded text: {e}")
            return ""
    
    def _extract_embedded_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract embedded text from PDF bytes"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting embedded text: {e}")
            return ""
    
    def _extract_text_from_pdf_via_ocr(self, pdf_path: str) -> str:
        """Convert PDF to images and run OCR"""
        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convert page to image (300 DPI)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data)).convert("RGB")
                
                # Extract text
                page_text = self._process_image(image)
                all_text += page_text + "\n\n"
                
                print(f"  Page {page_num + 1}: Extracted {len(page_text)} chars")
            
            doc.close()
            return all_text.strip()
            
        except Exception as e:
            print(f"Error in PDF OCR: {e}")
            return ""
    
    def _extract_text_from_pdf_bytes_via_ocr(self, pdf_bytes: bytes) -> str:
        """Convert PDF bytes to images and run OCR"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            all_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convert page to image (300 DPI)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data)).convert("RGB")
                
                # Extract text
                page_text = self._process_image(image)
                all_text += page_text + "\n\n"
                
                print(f"  Page {page_num + 1}: Extracted {len(page_text)} chars")
            
            doc.close()
            return all_text.strip()
            
        except Exception as e:
            print(f"Error in PDF OCR: {e}")
            return ""
    
    def _extract_single_region(self, image: Image.Image) -> str:
        """
        Extract text from a single image region using TrOCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            # Prepare image for model
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            generated_ids = self.model.generate(pixel_values)
            
            # Decode to text
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return generated_text.strip()
            
        except Exception as e:
            print(f"Error in single region extraction: {e}")
            return ""
    
    def _split_image_into_regions(self, image: Image.Image, num_splits: int = 3) -> List[Image.Image]:
        """
        Split large image into smaller regions for processing
        
        Args:
            image: PIL Image object
            num_splits: Number of vertical splits
            
        Returns:
            List of image regions
        """
        width, height = image.size
        region_height = height // num_splits
        
        regions = []
        for i in range(num_splits):
            top = i * region_height
            bottom = (i + 1) * region_height if i < num_splits - 1 else height
            
            region = image.crop((0, top, width, bottom))
            regions.append(region)
        
        return regions
    
    def extract_from_multiple_images(self, image_paths: List[str]) -> str:
        """
        Extract and combine text from multiple images
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Combined extracted text
        """
        all_text = []
        
        for i, path in enumerate(image_paths, 1):
            print(f"Processing image {i}/{len(image_paths)}: {path}")
            text = self.extract_text_from_image(path)
            if text:
                all_text.append(f"=== Document {i} ===\n{text}")
        
        return "\n\n".join(all_text)


# Alternative: Use EasyOCR (fallback if TrOCR has issues)
class EasyOCRExtractor:
    """
    Fallback OCR using EasyOCR library
    
    EasyOCR is lighter and supports multiple languages
    """
    
    def __init__(self, languages: List[str] = ['en']):
        """
        Initialize EasyOCR
        
        Args:
            languages: List of language codes (e.g., ['en'] for English)
        """
        try:
            import easyocr
            print("Loading EasyOCR...")
            self.reader = easyocr.Reader(languages, gpu=torch.cuda.is_available())
            print("✓ EasyOCR loaded successfully")
        except ImportError:
            print("EasyOCR not installed. Install with: pip install easyocr")
            raise
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text using EasyOCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text as string
        """
        try:
            result = self.reader.readtext(image_path)
            
            # Combine all detected text
            texts = [detection[1] for detection in result]
            return "\n".join(texts)
            
        except Exception as e:
            print(f"Error extracting text with EasyOCR: {e}")
            return ""


# Factory function to get appropriate OCR extractor
def get_ocr_extractor(method: str = "trocr") -> Union[TrOCRExtractor, EasyOCRExtractor]:
    """
    Factory function to get OCR extractor
    
    Args:
        method: "trocr" or "easyocr"
        
    Returns:
        OCR extractor instance
    """
    if method.lower() == "trocr":
        return TrOCRExtractor()
    elif method.lower() == "easyocr":
        return EasyOCRExtractor()
    else:
        raise ValueError(f"Unknown OCR method: {method}")


if __name__ == "__main__":
    # Test OCR extraction
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python trocr_extractor.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print("\n" + "="*60)
    print("Testing TR-OCR Text Extraction")
    print("="*60)
    
    try:
        # Initialize extractor
        extractor = TrOCRExtractor()
        
        # Extract text
        print(f"\nExtracting text from: {image_path}")
        text = extractor.extract_text_from_image(image_path)
        
        print("\n" + "="*60)
        print("EXTRACTED TEXT")
        print("="*60)
        print(text)
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying EasyOCR fallback...")
        try:
            extractor = EasyOCRExtractor()
            text = extractor.extract_text_from_image(image_path)
            print("\n" + "="*60)
            print("EXTRACTED TEXT (EasyOCR)")
            print("="*60)
            print(text)
            print("="*60)
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
