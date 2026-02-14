"""
OCR Service using TrOCR for document text extraction.

This service handles:
- PDF to image conversion
- TrOCR-based text extraction
- Multi-page document processing
- Text cleanup and merging
"""

import logging
import io
from typing import List, Optional
from pathlib import Path
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from pdf2image import convert_from_bytes
import numpy as np

logger = logging.getLogger("ocr_service")

# Global model cache
_trocr_processor: Optional[TrOCRProcessor] = None
_trocr_model: Optional[VisionEncoderDecoderModel] = None
_device: Optional[str] = None


def _load_trocr_model():
    """
    Load TrOCR model and processor (lazy loading).
    Model is cached globally to avoid reloading.
    """
    global _trocr_processor, _trocr_model, _device
    
    if _trocr_processor is not None and _trocr_model is not None:
        return _trocr_processor, _trocr_model, _device
    
    logger.info("Loading TrOCR model: microsoft/trocr-base-printed")
    
    try:
        # Determine device (GPU if available, else CPU)
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {_device}")
        
        # Load processor and model
        _trocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
        _trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")
        _trocr_model.to(_device)
        _trocr_model.eval()  # Set to evaluation mode
        
        logger.info("TrOCR model loaded successfully")
        return _trocr_processor, _trocr_model, _device
        
    except Exception as e:
        logger.error(f"Failed to load TrOCR model: {e}")
        raise


def pdf_to_images(pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images.
    
    Args:
        pdf_bytes: PDF file as bytes
        dpi: Resolution for conversion (default 300 for good OCR quality)
        
    Returns:
        List of PIL Image objects (one per page)
    """
    try:
        logger.info(f"Converting PDF to images (DPI: {dpi})")
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        logger.info(f"Converted PDF to {len(images)} page(s)")
        return images
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        raise ValueError(f"Failed to convert PDF: {str(e)}")


def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text from a single image using TrOCR.
    
    Args:
        image: PIL Image object
        
    Returns:
        Extracted text as string
    """
    processor, model, device = _load_trocr_model()
    
    try:
        # Convert image to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Preprocess image
        pixel_values = processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        
        # Generate text
        with torch.no_grad():
            generated_ids = model.generate(pixel_values)
        
        # Decode text
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return generated_text.strip()
        
    except Exception as e:
        logger.error(f"TrOCR text extraction failed: {e}")
        return ""


def extract_text_from_images(images: List[Image.Image]) -> str:
    """
    Extract text from multiple images and merge into single text.
    
    Args:
        images: List of PIL Image objects
        
    Returns:
        Merged text from all images
    """
    logger.info(f"Extracting text from {len(images)} image(s)")
    
    all_text = []
    for i, image in enumerate(images):
        logger.info(f"Processing image {i+1}/{len(images)}")
        text = extract_text_from_image(image)
        if text:
            all_text.append(text)
    
    # Merge with double newlines between pages
    merged_text = "\n\n".join(all_text)
    logger.info(f"Extracted {len(merged_text)} characters total")
    
    return merged_text


def extract_text_from_pdf(pdf_bytes: bytes, dpi: int = 300) -> str:
    """
    Extract text from PDF using TrOCR.
    
    This is the main entry point for PDF OCR.
    
    Args:
        pdf_bytes: PDF file as bytes
        dpi: Resolution for PDF to image conversion
        
    Returns:
        Extracted text from all pages
    """
    try:
        # Convert PDF to images
        images = pdf_to_images(pdf_bytes, dpi=dpi)
        
        # Extract text from images
        text = extract_text_from_images(images)
        
        return text
        
    except Exception as e:
        logger.error(f"PDF OCR failed: {e}")
        raise


def extract_text_from_document(file_data: bytes, file_type: str) -> str:
    """
    Extract text from document (PDF or image).
    
    Args:
        file_data: Document file as bytes
        file_type: File type ('PDF', 'JPG', 'PNG', etc.)
        
    Returns:
        Extracted text
    """
    file_type = file_type.upper()
    
    try:
        if file_type == "PDF":
            return extract_text_from_pdf(file_data)
        
        elif file_type in ["JPG", "JPEG", "PNG"]:
            # Load image from bytes
            image = Image.open(io.BytesIO(file_data))
            return extract_text_from_image(image)
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
    except Exception as e:
        logger.error(f"Document OCR failed for type {file_type}: {e}")
        raise


def cleanup_ocr_text(text: str) -> str:
    """
    Clean up OCR text by removing extra whitespace, fixing common OCR errors.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Join with single newlines
    cleaned = "\n".join(lines)
    
    return cleaned


# Preload model on module import (optional, for faster first request)
def preload_model():
    """
    Preload TrOCR model to avoid delay on first request.
    Call this during application startup.
    """
    try:
        _load_trocr_model()
        logger.info("TrOCR model preloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload TrOCR model: {e}")
