import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.eero_parse import parse_eero_screenshot_text
from backend.models import HomeInternetUsageMonth, User
from backend import schemas
from backend.routers.auth import get_current_user

try:
    import pytesseract
except ImportError:
    pytesseract = None

router = APIRouter(prefix="/internet-usage", tags=["internet-usage"])

OCR_PREVIEW_LEN = 4000


def _ocr_image(image: Image.Image) -> str:
    if pytesseract is None:
        raise HTTPException(
            status_code=503,
            detail="OCR is not available (pytesseract not installed). Enter usage manually.",
        )
    try:
        return pytesseract.image_to_string(image, config="--psm 6")
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not run OCR. Install Tesseract on the server "
                "(e.g. apt install tesseract-ocr) or enter totals manually. "
                f"Details: {e!s}"
            ),
        )


@router.get("", response_model=List[schemas.HomeInternetUsageMonth])
def list_usage(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(HomeInternetUsageMonth)
    if year is not None:
        q = q.filter(HomeInternetUsageMonth.year == year)
    rows = q.order_by(HomeInternetUsageMonth.year.desc(), HomeInternetUsageMonth.month.desc()).all()
    return rows


@router.put("/month", response_model=schemas.HomeInternetUsageMonth)
def upsert_month(
    data: schemas.HomeInternetUsageMonthUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(HomeInternetUsageMonth)
        .filter(
            HomeInternetUsageMonth.year == data.year,
            HomeInternetUsageMonth.month == data.month,
        )
        .first()
    )
    payload = data.model_dump()
    if row:
        for k, v in payload.items():
            setattr(row, k, v)
        row.updated_at = datetime.utcnow()
    else:
        row = HomeInternetUsageMonth(**payload)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{usage_id}", response_model=schemas.HomeInternetUsageMonth)
def update_usage(
    usage_id: int,
    data: schemas.HomeInternetUsageMonthUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(HomeInternetUsageMonth).filter(HomeInternetUsageMonth.id == usage_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{usage_id}")
def delete_usage(
    usage_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(HomeInternetUsageMonth).filter(HomeInternetUsageMonth.id == usage_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}


@router.post("/parse-eero-screenshot", response_model=schemas.EeroScreenshotParseResult)
async def parse_eero_screenshot(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file (PNG or JPEG).")
    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 15 MB).")
    try:
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image. Try PNG or JPEG.")

    text = _ocr_image(image)
    parsed = parse_eero_screenshot_text(text)
    preview = text.strip().replace("\r\n", "\n")
    if len(preview) > OCR_PREVIEW_LEN:
        preview = preview[:OCR_PREVIEW_LEN] + "\n…"

    return schemas.EeroScreenshotParseResult(
        ocr_text_preview=preview or "(no text detected)",
        suggested_year=parsed["suggested_year"],
        suggested_month=parsed["suggested_month"],
        suggested_total_gb=parsed["suggested_total_gb"],
        total_parse_hint=parsed["total_parse_hint"],
        parse_note=parsed["parse_note"],
        ocr_available=pytesseract is not None,
    )
