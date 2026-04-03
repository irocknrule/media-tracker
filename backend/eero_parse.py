"""
Heuristics to extract month, year, and total data usage from eero app screenshots
after OCR. Tuned for the eero "Data usage" monthly view (large TB/GB headline).
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _norm_num(s: str) -> float:
    return float(s.replace(",", "."))


def amount_to_gb(value: float, unit: str) -> float:
    u = unit.lower()
    if u == "tb":
        return value * 1000.0
    if u == "gb":
        return value
    if u == "mb":
        return value / 1000.0
    return value


def parse_month_year(text: str) -> Tuple[Optional[int], Optional[int]]:
    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{4})\b",
        text,
        re.I,
    )
    if m:
        key = m.group(1).lower()[:3]
        return MONTH_MAP.get(key), int(m.group(2))
    m = re.search(r"\b(20\d{2})[-/](\d{1,2})\b", text)
    if m:
        return int(m.group(2)), int(m.group(1))
    m = re.search(r"\b(\d{1,2})/(\d{4})\b", text)
    if m:
        mo, yr = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return mo, yr
    return None, None


def parse_total_gb_from_ocr(text: str) -> Tuple[Optional[float], str]:
    """
    Returns (total_gb, hint). Prefers TB amounts (eero monthly total is usually TB).
    """
    if not text or not text.strip():
        return None, "empty_ocr"

    # TB patterns (allow minor OCR splits like "T B")
    tb_pattern = re.compile(
        r"\b(\d+[.,]?\d*)\s*TB\b|(\d+[.,]?\d*)\s+T\s+B\b",
        re.I,
    )
    tb_vals: list[float] = []
    for m in tb_pattern.finditer(text):
        raw = m.group(1) or m.group(2)
        if raw:
            try:
                tb_vals.append(_norm_num(raw))
            except ValueError:
                continue
    if tb_vals:
        return amount_to_gb(max(tb_vals), "tb"), "tb_max"

    # Single large GB headline (less reliable than TB)
    gb_pattern = re.compile(r"\b(\d+[.,]?\d*)\s*GB\b", re.I)
    gb_vals: list[float] = []
    for m in gb_pattern.finditer(text):
        try:
            gb_vals.append(_norm_num(m.group(1)))
        except ValueError:
            continue
    if gb_vals:
        big = [g for g in gb_vals if g >= 200]
        if len(big) == 1:
            return big[0], "single_large_gb"
        if gb_vals:
            return amount_to_gb(max(gb_vals), "gb"), "gb_max"

    return None, "no_match"


def parse_eero_screenshot_text(text: str) -> Dict[str, Any]:
    month, year = parse_month_year(text)
    total_gb, total_hint = parse_total_gb_from_ocr(text)
    note_parts = []
    if total_gb is None:
        note_parts.append(
            "Could not read a clear total from the image. Enter the monthly total manually "
            "(check the large TB or GB figure at the top of Data usage)."
        )
    if month is None or year is None:
        note_parts.append(
            "Could not read the billing month from the screenshot. Choose year and month manually."
        )
    return {
        "suggested_year": year,
        "suggested_month": month,
        "suggested_total_gb": round(total_gb, 4) if total_gb is not None else None,
        "total_parse_hint": total_hint,
        "parse_note": " ".join(note_parts) if note_parts else None,
    }
