# HTR Service Documentation

## Overview

The HTR (Handwritten Text Recognition) service provides text detection capabilities for generated handwriting images. This service uses Microsoft's TrOCR model from HuggingFace.

**⚠️ CRITICAL: INTERNAL USE ONLY**

This service is designed **exclusively for internal validation, quality checking, and logging**. 

### What HTR Does:
- ✅ Detects text from generated handwriting images
- ✅ Validates generation quality internally
- ✅ Logs detected text for monitoring
- ✅ Provides similarity scores for quality checks

### What HTR Does NOT Do:
- ❌ **DO NOT** forward detected text to external APIs
- ❌ **DO NOT** send detected text to handwriting generation endpoints
- ❌ **DO NOT** use detected text in the generation pipeline
- ❌ **DO NOT** expose detected text to frontend users (unless for debugging)

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_htr.txt
```

Or install manually:

```bash
pip install transformers torch pillow sentencepiece accelerate
```

### 2. Model Download

The TrOCR model will be automatically downloaded from HuggingFace on first use (~1.5GB for base model).

**Models available:**
- `microsoft/trocr-base-handwritten` (default, lightweight, ~1.5GB)
- `microsoft/trocr-large-handwritten` (more accurate, heavier, ~3GB)

---

## Usage

### Basic Usage

```python
from services.htr_service import detect_text_from_image

# Detect text from a generated image
detected_text = detect_text_from_image("api_outputs/generated_word.png")
print(f"Internal validation: {detected_text}")

# REMINDER: DO NOT send this text to external APIs
```

### Advanced Usage

```python
from services.htr_service import HTRService

# Initialize service
htr = HTRService()

# Detect text with logging
text = htr.detect_text_from_image("output.png", log_result=True)

# Validate generation quality
result = htr.validate_generation(
    image_path="output.png",
    expected_text="hello world",
    similarity_threshold=0.7
)

print(f"Match: {result['match']}")
print(f"Similarity: {result['similarity']:.2%}")
print(f"Valid: {result['valid']}")
```

### Integration in API

The HTR service is already integrated into the API endpoints:

```python
# In api/main.py - already implemented
def _generate_stylized_image(text: str, style_dir: Path) -> Path:
    # ... generation code ...
    
    # INTERNAL VALIDATION ONLY
    try:
        htr_service = get_htr_service()
        detected_text = htr_service.detect_text_from_image(output_path)
        logger.info(f"[HTR CHECK] Expected: '{text}' | Detected: '{detected_text}'")
    except Exception as e:
        logger.warning(f"HTR validation failed (non-critical): {e}")
    
    return output_path
```

---

## Architecture

### Flow Diagram

```
User Request
    ↓
Generate Handwriting Image (existing flow - NOT MODIFIED)
    ↓
Image Saved to Disk
    ↓
[HTR Service] ← Read image for validation
    ↓
Detect Text (INTERNAL ONLY)
    ↓
Log Results (console/logs)
    ↓
Return Image to User (existing flow - NOT MODIFIED)
```

### Key Points:
1. HTR runs **AFTER** image generation
2. HTR does **NOT** modify the generation process
3. HTR results are **NOT** sent to external APIs
4. HTR failures are **non-critical** (logged but don't break requests)

---

## API Reference

### `HTRService`

Main service class for handwritten text recognition.

#### Methods:

**`__init__(model_name: str = "microsoft/trocr-base-handwritten")`**
- Initialize the HTR service
- Model is lazy-loaded on first use

**`detect_text_from_image(image_source, log_result=True) -> str`**
- Detect text from an image
- Args:
  - `image_source`: Path (str/Path) or PIL Image
  - `log_result`: Whether to log the result
- Returns: Detected text string

**`validate_generation(image_path, expected_text, similarity_threshold=0.7) -> dict`**
- Validate generated image against expected text
- Returns dict with:
  - `detected_text`: What HTR detected
  - `expected_text`: What was expected
  - `match`: Boolean for exact match
  - `similarity`: Float similarity score (0-1)
  - `valid`: Boolean if passes threshold

### Helper Functions

**`get_htr_service() -> HTRService`**
- Get singleton instance of HTR service
- Reuses same model across requests

**`detect_text_from_image(image_source) -> str`**
- Convenience function for quick detection
- Uses singleton service internally

---

## Examples

See `examples/htr_example.py` for comprehensive examples:

```bash
cd frontend
python examples/htr_example.py
```

Examples include:
1. Basic text detection
2. Generation validation
3. Convenience function usage
4. Batch validation

---

## Configuration

### Change Model

To use a different model, modify the initialization:

```python
# Use larger, more accurate model
htr = HTRService(model_name="microsoft/trocr-large-handwritten")
```

### Adjust Validation Threshold

```python
# Stricter validation (90% similarity required)
result = htr.validate_generation(
    image_path="output.png",
    expected_text="hello",
    similarity_threshold=0.9
)
```

---

## Performance

### Model Loading
- First request: ~5-10 seconds (model download + load)
- Subsequent requests: Instant (model cached)

### Inference Speed
- Base model: ~0.5-1 second per image (CPU)
- Base model: ~0.1-0.3 seconds per image (GPU)
- Large model: ~1-2 seconds per image (CPU)

### Memory Usage
- Base model: ~1.5GB RAM
- Large model: ~3GB RAM

---

## Troubleshooting

### Model Download Issues

If model download fails:

```python
# Manually download model
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
```

### CUDA Out of Memory

If GPU memory is insufficient:

```python
# Force CPU usage
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

htr = HTRService()  # Will use CPU
```

### Low Accuracy

If detection accuracy is poor:
1. Try the larger model: `microsoft/trocr-large-handwritten`
2. Ensure images are clear and high-contrast
3. Check image preprocessing (should be RGB)

---

## Security & Privacy

### Data Handling
- HTR processes images **locally** (no external API calls)
- Detected text is **logged only** (not stored permanently)
- No data is sent to HuggingFace or external services after model download

### Best Practices
- ✅ Use HTR for internal quality monitoring
- ✅ Log detected text for debugging
- ✅ Keep HTR failures non-critical
- ❌ Never expose raw HTR output to end users
- ❌ Never send HTR results to external APIs
- ❌ Never use HTR output in generation pipeline

---

## Future Enhancements

Potential improvements (not implemented):

1. **Batch Processing**: Process multiple images in parallel
2. **Confidence Scores**: Return confidence for each detection
3. **Character-level Analysis**: Detailed per-character accuracy
4. **Custom Fine-tuning**: Train on project-specific handwriting
5. **Real-time Monitoring**: Dashboard for quality metrics

---

## Support

For issues or questions:
1. Check logs for error messages
2. Verify dependencies are installed
3. Ensure images exist and are readable
4. Check GPU/CPU availability

---

## License

This service uses Microsoft TrOCR, which is licensed under MIT License.
See: https://github.com/microsoft/unilm/tree/master/trocr

---

**Remember: HTR is for INTERNAL VALIDATION ONLY. Do not forward detected text to external APIs or generation endpoints.**
