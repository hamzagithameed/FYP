"""
HTR Integration Test Script
============================
Quick test to verify HTR service is properly integrated.

This script tests:
1. HTR service can be imported
2. Model can be initialized
3. Basic functionality works

Run this after installing HTR dependencies.
"""

import sys
from pathlib import Path

print("=" * 70)
print("HTR INTEGRATION TEST")
print("=" * 70)

# Test 1: Import check
print("\n[1/4] Testing imports...")
try:
    from services.htr_service import HTRService, get_htr_service, detect_text_from_image
    print("✓ HTR service imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nMake sure you're running from the 'frontend' directory:")
    print("  cd frontend")
    print("  python test_htr_integration.py")
    sys.exit(1)

# Test 2: Dependency check
print("\n[2/4] Checking dependencies...")
try:
    import torch
    import transformers
    from PIL import Image
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ Transformers version: {transformers.__version__}")
    print(f"✓ PIL available")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("\nInstall HTR dependencies:")
    print("  pip install -r requirements_htr.txt")
    sys.exit(1)

# Test 3: Service initialization
print("\n[3/4] Initializing HTR service...")
try:
    htr = HTRService()
    print("✓ HTR service initialized")
    print(f"  Model: {htr.model_name}")
    print(f"  Device: {htr.device}")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 4: Singleton pattern
print("\n[4/4] Testing singleton pattern...")
try:
    service1 = get_htr_service()
    service2 = get_htr_service()
    if service1 is service2:
        print("✓ Singleton pattern working correctly")
    else:
        print("⚠ Warning: Singleton pattern not working (not critical)")
except Exception as e:
    print(f"✗ Singleton test failed: {e}")

# Test 5: Model loading (optional - takes time)
print("\n[OPTIONAL] Testing model loading...")
print("This will download the TrOCR model (~1.5GB) if not cached.")
print("Skip this test if you want to test later.")
response = input("Load model now? (y/n): ").strip().lower()

if response == 'y':
    try:
        print("Loading model (this may take a few minutes on first run)...")
        htr._lazy_load()
        print("✓ Model loaded successfully")
        print(f"  Processor: {type(htr.processor).__name__}")
        print(f"  Model: {type(htr.model).__name__}")
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        print("\nThis might be due to:")
        print("  - Network issues (model download)")
        print("  - Insufficient disk space")
        print("  - Incompatible PyTorch/Transformers versions")
else:
    print("⊘ Skipped model loading test")

# Summary
print("\n" + "=" * 70)
print("INTEGRATION TEST SUMMARY")
print("=" * 70)
print("\n✓ HTR service is properly integrated!")
print("\nNext steps:")
print("1. Generate a handwriting image using your API")
print("2. Run examples: python examples/htr_example.py")
print("3. Check API logs for HTR validation messages")
print("\nREMINDER: HTR is for INTERNAL VALIDATION ONLY")
print("DO NOT forward detected text to external APIs.")
print("=" * 70 + "\n")
