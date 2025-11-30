"""
HTR (Handwritten Text Recognition) Service
===========================================
This module provides handwritten text recognition capabilities using Microsoft TrOCR.

IMPORTANT: This service is for INTERNAL VALIDATION ONLY.
- DO NOT forward HTR-detected text to external APIs
- DO NOT send detected text to the handwriting-generation API
- DO NOT modify the existing handwriting generation flow
- Use this ONLY for quality checks, logging, and internal validation

The HTR model reads text from stylized handwriting images AFTER they are generated.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


logger = logging.getLogger(__name__)


class HTRService:
    """
    Handwritten Text Recognition service using Microsoft TrOCR.
    
    This service is designed for internal validation and quality checking only.
    DO NOT use the detected text for any external API calls or generation processes.
    """
    
    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten"):
        """
        Initialize the HTR service with TrOCR model.
        
        Args:
            model_name: HuggingFace model identifier for TrOCR
                       Default: "microsoft/trocr-base-handwritten" (lightweight)
                       Alternative: "microsoft/trocr-large-handwritten" (more accurate but heavier)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None
        self._initialized = False
        
        logger.info(f"HTR Service initialized with model: {model_name}")
        logger.info(f"Using device: {self.device}")
    
    def _lazy_load(self):
        """
        Lazy load the model and processor to avoid loading on import.
        Models are only loaded when first needed.
        """
        if self._initialized:
            return
        
        logger.info("Loading TrOCR model and processor...")
        try:
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._initialized = True
            logger.info("TrOCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TrOCR model: {e}")
            raise
    
    def detect_text_from_image(
        self, 
        image_source: Union[str, Path, Image.Image],
        log_result: bool = True
    ) -> str:
        """
        Detect handwritten text from an image.
        
        IMPORTANT: This function is for INTERNAL VALIDATION ONLY.
        DO NOT forward the detected text to external APIs or generation endpoints.
        
        Args:
            image_source: Can be:
                         - Path to image file (str or Path)
                         - PIL Image object
            log_result: Whether to log the detected text (default: True)
        
        Returns:
            str: Detected text from the handwriting image
        
        Example:
            >>> htr = HTRService()
            >>> detected_text = htr.detect_text_from_image("output.png")
            >>> print(f"Internal validation: {detected_text}")
        """
        # Lazy load model on first use
        self._lazy_load()
        
        # Load image
        if isinstance(image_source, (str, Path)):
            image_path = Path(image_source)
            if not image_path.exists():
                logger.error(f"Image file not found: {image_path}")
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = Image.open(image_path).convert("RGB")
            logger.debug(f"Processing image: {image_path}")
        elif isinstance(image_source, Image.Image):
            image = image_source.convert("RGB")
            logger.debug("Processing PIL Image object")
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")
        
        # Process image and generate text
        try:
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
            
            detected_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            if log_result:
                logger.info(f"[HTR INTERNAL VALIDATION] Detected text: '{detected_text}'")
            
            return detected_text
            
        except Exception as e:
            logger.error(f"Error during text detection: {e}")
            raise
    
    def validate_generation(
        self, 
        image_path: Union[str, Path], 
        expected_text: str,
        similarity_threshold: float = 0.7
    ) -> dict:
        """
        Validate a generated handwriting image against expected text.
        
        INTERNAL USE ONLY - for quality checking and validation.
        DO NOT send results to external APIs.
        
        Args:
            image_path: Path to the generated handwriting image
            expected_text: The text that was supposed to be generated
            similarity_threshold: Minimum similarity score (0-1) to consider valid
        
        Returns:
            dict: Validation results containing:
                  - detected_text: What the HTR model detected
                  - expected_text: What was supposed to be generated
                  - match: Whether texts match exactly
                  - similarity: Simple similarity score
                  - valid: Whether generation passes validation
        """
        detected_text = self.detect_text_from_image(image_path, log_result=False)
        
        # Simple similarity check (case-insensitive, whitespace normalized)
        detected_normalized = detected_text.lower().strip()
        expected_normalized = expected_text.lower().strip()
        
        exact_match = detected_normalized == expected_normalized
        
        # Simple character-level similarity
        if len(expected_normalized) == 0:
            similarity = 0.0
        else:
            matching_chars = sum(1 for a, b in zip(detected_normalized, expected_normalized) if a == b)
            similarity = matching_chars / max(len(detected_normalized), len(expected_normalized))
        
        is_valid = exact_match or similarity >= similarity_threshold
        
        result = {
            "detected_text": detected_text,
            "expected_text": expected_text,
            "match": exact_match,
            "similarity": similarity,
            "valid": is_valid
        }
        
        logger.info(f"[HTR VALIDATION] Expected: '{expected_text}' | Detected: '{detected_text}' | "
                   f"Match: {exact_match} | Similarity: {similarity:.2f} | Valid: {is_valid}")
        
        return result


# Singleton instance for reuse across requests
_htr_service_instance: Optional[HTRService] = None


def get_htr_service() -> HTRService:
    """
    Get or create the singleton HTR service instance.
    
    Returns:
        HTRService: Singleton instance of the HTR service
    """
    global _htr_service_instance
    if _htr_service_instance is None:
        _htr_service_instance = HTRService()
    return _htr_service_instance


# Convenience function for quick text detection
def detect_text_from_image(image_source: Union[str, Path, Image.Image]) -> str:
    """
    Convenience function to detect text from an image.
    
    INTERNAL VALIDATION ONLY - DO NOT forward detected text to external APIs.
    
    Args:
        image_source: Path to image or PIL Image object
    
    Returns:
        str: Detected handwritten text
    
    Example:
        >>> from services.htr_service import detect_text_from_image
        >>> text = detect_text_from_image("generated_output.png")
        >>> print(f"Internal check: {text}")
    """
    service = get_htr_service()
    return service.detect_text_from_image(image_source)
