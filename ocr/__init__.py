"""
OCR Package for Health Insurance Claims Processing

This package provides OCR capabilities for extracting and parsing
health insurance claim documents.

Components:
- TrOCRExtractor: Extract text from images using TR-OCR
- EasyOCRExtractor: Alternative OCR using EasyOCR
- ClaimTextParser: Parse OCR text to structured claim JSON
- OCRClaimProcessor: Complete end-to-end pipeline

Example Usage:
    from ocr import TrOCRExtractor, ClaimTextParser, OCRClaimProcessor
    
    # Simple extraction
    extractor = TrOCRExtractor()
    text = extractor.extract_text_from_image("claim.jpg")
    
    # Parse to JSON
    parser = ClaimTextParser()
    claim = parser.parse_text_to_claim(text)
    
    # Complete pipeline
    processor = OCRClaimProcessor()
    result = processor.process_claim_from_images("claim.jpg")
"""

from ocr.trocr_extractor import TrOCRExtractor, EasyOCRExtractor, get_ocr_extractor
from ocr.text_parser import ClaimTextParser
from ocr.claim_processor import OCRClaimProcessor

__all__ = [
    'TrOCRExtractor',
    'EasyOCRExtractor',
    'get_ocr_extractor',
    'ClaimTextParser',
    'OCRClaimProcessor'
]

__version__ = '1.0.0'

