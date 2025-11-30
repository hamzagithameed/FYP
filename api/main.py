import asyncio
import base64
import logging
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader

# Import authentication
try:
    from auth import (
        connect_to_mongo,
        close_mongo_connection,
        create_access_token,
        decode_access_token,
        create_user,
        authenticate_user,
        user_doc_to_response,
        UserCreate,
        UserLogin,
        Token,
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logging.warning("Auth module not available. Install dependencies: pip install motor pymongo passlib python-jose python-dotenv")

# Import HTR service for internal validation only (optional)
# DO NOT forward HTR-detected text to external APIs or generation endpoints
try:
    from services.htr_service import get_htr_service
    HTR_AVAILABLE = True
except ImportError:
    HTR_AVAILABLE = False
    logging.warning("HTR service not available. Install dependencies: pip install -r requirements_htr.txt")

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOM_GENERATED_DIR = BASE_DIR / "custom_generated"
API_OUTPUT_DIR = BASE_DIR / "api_outputs"
STYLE_UPLOAD_DIR = BASE_DIR / "uploaded_styles"

CUSTOM_GENERATED_DIR.mkdir(exist_ok=True)
API_OUTPUT_DIR.mkdir(exist_ok=True)
STYLE_UPLOAD_DIR.mkdir(exist_ok=True)


class TextPayload(BaseModel):
    text: str = Field(..., min_length=1, description="Text that should be rendered")


app = FastAPI(title="InkWave API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on startup"""
    if AUTH_AVAILABLE:
        try:
            await connect_to_mongo()
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    if AUTH_AVAILABLE:
        try:
            await close_mongo_connection()
        except Exception as e:
            logging.error(f"Failed to close MongoDB connection: {e}")


# Dependency to get current user from JWT token
async def get_current_user(authorization: str = Header(None)):
    """
    Get current user from JWT token in Authorization header
    
    Args:
        authorization: Authorization header with Bearer token
    
    Returns:
        dict: User data
    
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not AUTH_AVAILABLE:
        # If auth is not available, return a mock user for development
        return {"id": "dev", "name": "Dev User", "email": "dev@inkwave.app"}
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


# Optional authentication dependency (doesn't require token)
async def get_current_user_optional(authorization: str = Header(None)):
    """
    Get current user from JWT token, but don't require it
    
    Returns:
        dict: User data or None
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except:
        return None


def _run_command(command: List[str]) -> None:
    """Execute an external command and surface stdout/stderr on failure."""
    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr or exc.stdout or str(exc)
        raise HTTPException(status_code=500, detail=f"Generation failed: {detail}") from exc


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """
    Register a new user
    
    Args:
        user_data: User registration data (name, email, password)
    
    Returns:
        Token: JWT token and user data
    """
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Create user
        user = await create_user(user_data)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "name": user.name}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password
    
    Args:
        credentials: User login credentials (email, password)
    
    Returns:
        Token: JWT token and user data
    """
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Authenticate user
        user_doc = await authenticate_user(credentials.email, credentials.password)
        
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Convert to response model
        user = user_doc_to_response(user_doc)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "name": user.name}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Failed to login")


@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        dict: User information
    """
    return current_user


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _ensure_text(text: str) -> str:
    clean = text.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return clean


def _split_words(sentence: str) -> List[str]:
    words = [w for w in sentence.split() if w.strip()]
    if not words:
        raise HTTPException(status_code=400, detail="Sentence must include at least one word.")
    return words


def _encode_image(image_path: Path) -> str:
    with image_path.open("rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


def _combine_images(image_paths: List[Path], output_path: Path, padding: int = 8) -> Path:
    images = [Image.open(p).convert("RGB") for p in image_paths]
    target_height = max(img.height for img in images)
    resized = []
    for img in images:
        if img.height != target_height:
            new_img = Image.new("RGB", (img.width, target_height), "white")
            offset = (target_height - img.height) // 2
            new_img.paste(img, (0, offset))
            resized.append(new_img)
        else:
            resized.append(img)
    total_width = sum(img.width for img in resized) + padding * (len(resized) - 1 if len(resized) > 1 else 0)
    canvas = Image.new("RGB", (total_width, target_height), "white")
    cursor = 0
    for img in resized:
        canvas.paste(img, (cursor, 0))
        cursor += img.width + padding
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def _generate_word_image(text: str) -> Path:
    image_id = uuid.uuid4().hex
    output_path = API_OUTPUT_DIR / f"word_{image_id}.png"
    command = [
        sys.executable,
        "trainCopy.py",
        "--text_to_generate",
        text,
        "--device",
        "cpu",
        "--output_path",
        str(output_path),
    ]
    _run_command(command)
    if not output_path.exists():
        raise HTTPException(status_code=500, detail="Word image was not created.")
    
    # INTERNAL VALIDATION ONLY: Run HTR to detect text from generated image
    # DO NOT forward this detected text to external APIs or generation endpoints
    if HTR_AVAILABLE:
        try:
            htr_service = get_htr_service()
            detected_text = htr_service.detect_text_from_image(output_path, log_result=True)
            logger.info(f"[HTR INTERNAL CHECK] Generated: '{text}' | Detected: '{detected_text}'")
        except Exception as e:
            # HTR is for validation only - don't fail the request if it errors
            logger.warning(f"HTR validation failed (non-critical): {e}")
    
    return output_path


def _generate_stylized_image(text: str, style_dir: Path) -> Path:
    image_id = uuid.uuid4().hex
    output_path = API_OUTPUT_DIR / f"stylized_{image_id}.png"
    command = [
        sys.executable,
        "generate_handwriting.py",
        "--text_to_generate",
        text,
        "--style_dir",
        str(style_dir),
        "--output_path",
        str(output_path),
    ]
    _run_command(command)
    if not output_path.exists():
        raise HTTPException(status_code=500, detail="Stylized image was not created.")
    
    # INTERNAL VALIDATION ONLY: Run HTR to detect text from stylized image
    # DO NOT forward this detected text to external APIs or generation endpoints
    if HTR_AVAILABLE:
        try:
            htr_service = get_htr_service()
            detected_text = htr_service.detect_text_from_image(output_path, log_result=True)
            logger.info(f"[HTR INTERNAL CHECK] Stylized: '{text}' | Detected: '{detected_text}'")
        except Exception as e:
            # HTR is for validation only - don't fail the request if it errors
            logger.warning(f"HTR validation failed (non-critical): {e}")
    
    return output_path


@app.post("/api/word")
async def generate_word(payload: TextPayload):
    text = _ensure_text(payload.text)
    image_path = await asyncio.to_thread(_generate_word_image, text)
    return {
        "text": text,
        "filename": image_path.name,
        "image_base64": _encode_image(image_path),
    }


@app.post("/api/sentence")
async def generate_sentence(payload: TextPayload):
    text = _ensure_text(payload.text)
    words = _split_words(text)
    word_images = []
    for word in words:
        image_path = await asyncio.to_thread(_generate_word_image, word)
        word_images.append(image_path)
    merged_path = API_OUTPUT_DIR / f"sentence_{uuid.uuid4().hex}.png"
    merged_path = await asyncio.to_thread(_combine_images, word_images, merged_path)
    return {
        "text": text,
        "word_count": len(words),
        "filename": merged_path.name,
        "image_base64": _encode_image(merged_path),
    }


@app.post("/api/stylized")
async def generate_stylized(
    text: str = Form(..., description="Text to render using the uploaded handwriting samples"),
    samples: List[UploadFile] = File(..., description="At least five handwriting reference images"),
):
    clean_text = _ensure_text(text)
    if len(samples) < 5:
        raise HTTPException(status_code=400, detail="Please upload at least five reference images.")

    style_set_id = uuid.uuid4().hex
    style_dir = STYLE_UPLOAD_DIR / style_set_id
    style_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for upload in samples:
        suffix = Path(upload.filename or "").suffix or ".png"
        target = style_dir / f"{uuid.uuid4().hex}{suffix}"
        with target.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        saved_files.append(target)

    try:
        words = _split_words(clean_text)
        stylized_images = []
        for word in words:
            image_path = await asyncio.to_thread(_generate_stylized_image, word, style_dir)
            stylized_images.append(image_path)
        merged_path = API_OUTPUT_DIR / f"stylized_sentence_{uuid.uuid4().hex}.png"
        merged_path = await asyncio.to_thread(_combine_images, stylized_images, merged_path)
    finally:
        for upload in samples:
            upload.file.close()

    return {
        "text": clean_text,
        "word_count": len(words),
        "reference_images": [str(path.relative_to(BASE_DIR)) for path in saved_files],
        "filename": merged_path.name,
        "image_base64": _encode_image(merged_path),
    }



@app.post("/convert/pdf")
async def convert_to_pdf(
    sentence: str = Form(..., description="The text that was generated"),
    images: UploadFile = File(..., description="The generated handwriting image"),
):
    """
    Convert a generated handwriting image to PDF format.
    
    This endpoint takes the generated image and creates a PDF document
    with the image centered on the page.
    """
    try:
        # Generate unique ID for this PDF
        pdf_id = uuid.uuid4().hex
        
        # Save uploaded image temporarily
        image_path = API_OUTPUT_DIR / f"temp_image_{pdf_id}.png"
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(images.file, buffer)
        
        # Create PDF
        pdf_path = API_OUTPUT_DIR / f"converted_{pdf_id}.pdf"
        
        # Open the image to get dimensions
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Create PDF with appropriate page size
        # Use A4 size as default
        page_width, page_height = A4
        
        # Create canvas
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        
        # Calculate scaling to fit image on page with margins
        margin = 50  # 50 points margin
        available_width = page_width - (2 * margin)
        available_height = page_height - (2 * margin)
        
        # Calculate scale factor to fit image
        scale_width = available_width / img_width
        scale_height = available_height / img_height
        scale = min(scale_width, scale_height, 1.0)  # Don't scale up, only down
        
        # Calculate final dimensions
        final_width = img_width * scale
        final_height = img_height * scale
        
        # Center the image on the page
        x = (page_width - final_width) / 2
        y = (page_height - final_height) / 2
        
        # Draw the image
        c.drawImage(
            str(image_path),
            x, y,
            width=final_width,
            height=final_height,
            preserveAspectRatio=True
        )
        
        # Add text at the bottom (optional)
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, 30, f"Generated text: {sentence}")
        c.drawCentredString(page_width / 2, 15, "Created with InkWave")
        
        # Save PDF
        c.save()
        
        # Clean up temporary image
        try:
            image_path.unlink()
        except:
            pass
        
        # Return PDF file
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename="inkwave-handwriting.pdf",
            headers={
                "Content-Disposition": "attachment; filename=inkwave-handwriting.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"PDF conversion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert to PDF: {str(e)}")
    finally:
        if images.file:
            images.file.close()


@app.post("/api/detect")
async def detect_handwriting(
    image: UploadFile = File(..., description="Handwriting image to detect text from")
):
    """
    Detect handwritten text from an uploaded image using HTR (Handwritten Text Recognition).
    
    This endpoint uses Microsoft TrOCR model to recognize handwritten text from images.
    """
    if not HTR_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="HTR service not available. Please install dependencies: pip install -r requirements_htr.txt"
        )
    
    try:
        # Generate unique ID for this detection
        detection_id = uuid.uuid4().hex
        
        # Save uploaded image temporarily
        image_path = API_OUTPUT_DIR / f"detect_{detection_id}.png"
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        logger.info(f"Processing HTR detection for image: {image.filename}")
        
        # Get HTR service and detect text
        htr_service = get_htr_service()
        detected_text = htr_service.detect_text_from_image(image_path, log_result=True)
        
        logger.info(f"HTR Detection successful: '{detected_text}'")
        
        # Clean up temporary image
        try:
            image_path.unlink()
        except:
            pass
        
        return {
            "success": True,
            "detected_text": detected_text,
            "filename": image.filename,
            "message": "Text detected successfully"
        }
        
    except Exception as e:
        logger.error(f"HTR detection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect text: {str(e)}"
        )
    finally:
        if image.file:
            image.file.close()
