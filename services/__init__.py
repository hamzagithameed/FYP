"""
Services Module
===============
Contains isolated service modules for the application.

HTR Service: Handwritten Text Recognition for internal validation only.
"""

from .htr_service import HTRService, get_htr_service, detect_text_from_image

__all__ = ["HTRService", "get_htr_service", "detect_text_from_image"]
