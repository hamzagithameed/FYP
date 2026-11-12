import asyncio
import base64
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOM_GENERATED_DIR = BASE_DIR / "custom_generated"
API_OUTPUT_DIR = BASE_DIR / "api_outputs"
STYLE_UPLOAD_DIR = BASE_DIR / "uploaded_styles"

CUSTOM_GENERATED_DIR.mkdir(exist_ok=True)
API_OUTPUT_DIR.mkdir(exist_ok=True)
STYLE_UPLOAD_DIR.mkdir(exist_ok=True)


class TextPayload(BaseModel):
    text: str = Field(..., min_length=1, description="Text that should be rendered")


app = FastAPI(title="DiffusionPen API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

