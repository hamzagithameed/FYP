"""
HTR Service Example Usage
==========================
This script demonstrates how to use the HTR service for internal validation.

IMPORTANT REMINDERS:
- HTR is for INTERNAL VALIDATION ONLY
- DO NOT forward detected text to external APIs
- DO NOT send detected text to handwriting generation endpoints
- Use only for quality checks, logging, and validation
"""

import sys
from pathlib import Path

# Add parent directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.htr_service import HTRService, detect_text_from_image


def example_basic_usage():
    """Example 1: Basic text detection from an image"""
    print("=" * 60)
    print("Example 1: Basic Text Detection")
    print("=" * 60)
    
    # Initialize HTR service
    htr = HTRService()
    
    # Detect text from a generated handwriting image
    # Replace with actual path to your generated image
    image_path = "api_outputs/word_example.png"
    
    if Path(image_path).exists():
        detected_text = htr.detect_text_from_image(image_path)
        print(f"\nDetected text: '{detected_text}'")
        print("\n[REMINDER] This text is for internal validation only.")
        print("DO NOT send this to external APIs.\n")
    else:
        print(f"\nImage not found: {image_path}")
        print("Generate a handwriting image first using the API.\n")


def example_validation():
    """Example 2: Validate generated image against expected text"""
    print("=" * 60)
    print("Example 2: Generation Validation")
    print("=" * 60)
    
    htr = HTRService()
    
    # Validate a generated image
    image_path = "api_outputs/stylized_example.png"
    expected_text = "hello world"
    
    if Path(image_path).exists():
        result = htr.validate_generation(image_path, expected_text)
        
        print(f"\nExpected text: '{result['expected_text']}'")
        print(f"Detected text: '{result['detected_text']}'")
        print(f"Exact match: {result['match']}")
        print(f"Similarity: {result['similarity']:.2%}")
        print(f"Validation passed: {result['valid']}")
        print("\n[REMINDER] This validation is for internal quality checks only.\n")
    else:
        print(f"\nImage not found: {image_path}")
        print("Generate a stylized image first using the API.\n")


def example_convenience_function():
    """Example 3: Using the convenience function"""
    print("=" * 60)
    print("Example 3: Convenience Function")
    print("=" * 60)
    
    # Quick one-liner for text detection
    image_path = "api_outputs/word_example.png"
    
    if Path(image_path).exists():
        text = detect_text_from_image(image_path)
        print(f"\nQuick detection: '{text}'")
        print("\n[REMINDER] Internal use only - do not forward to APIs.\n")
    else:
        print(f"\nImage not found: {image_path}")
        print("Generate an image first.\n")


def example_batch_validation():
    """Example 4: Batch validation of multiple images"""
    print("=" * 60)
    print("Example 4: Batch Validation")
    print("=" * 60)
    
    htr = HTRService()
    
    # Example: Validate multiple generated images
    test_cases = [
        ("api_outputs/word_hello.png", "hello"),
        ("api_outputs/word_world.png", "world"),
        ("api_outputs/stylized_test.png", "test"),
    ]
    
    print("\nValidating multiple images...\n")
    
    for image_path, expected in test_cases:
        if Path(image_path).exists():
            result = htr.validate_generation(image_path, expected)
            status = "✓ PASS" if result['valid'] else "✗ FAIL"
            print(f"{status} | Expected: '{expected}' | Detected: '{result['detected_text']}' | "
                  f"Similarity: {result['similarity']:.2%}")
        else:
            print(f"⊘ SKIP | Image not found: {image_path}")
    
    print("\n[REMINDER] These validations are for internal quality monitoring only.\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("HTR SERVICE EXAMPLES - INTERNAL VALIDATION ONLY")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("- HTR detected text is for INTERNAL USE ONLY")
    print("- DO NOT forward to external APIs")
    print("- DO NOT send to handwriting generation endpoints")
    print("- Use only for logging, quality checks, and validation")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_validation()
        example_convenience_function()
        example_batch_validation()
        
        print("=" * 60)
        print("Examples completed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nNote: Make sure you have:")
        print("1. Installed required packages: pip install transformers torch pillow")
        print("2. Generated some handwriting images using the API")
        print("3. Updated image paths in this script to match your outputs\n")


if __name__ == "__main__":
    main()
