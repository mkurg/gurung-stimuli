from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SET_NUMBERS = {1, 2, 3, 4}
EXPECTED_IMAGES = {
    "ic_1",
    "coh_1",
    "coh_2",
    "tr_target",
    "it_target",
    "end_coh_it",
    "end_ic_tr",
    "end_ic_it",
}
MAX_REVIEW_LENGTH = 3000


def review_key(dataset_number: int, set_number: int, stem: str) -> str:
    return f"{dataset_number}:{set_number}:{stem}"


def empty_reviews_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "updatedAt": "",
        "reviews": {},
    }


def load_reviews(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_reviews_payload()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_reviews_payload()

    if not isinstance(raw, dict):
        return empty_reviews_payload()

    reviews: dict[str, list[dict[str, str]]] = {}
    raw_reviews = raw.get("reviews")
    if isinstance(raw_reviews, dict):
        for key, entries in raw_reviews.items():
            if not isinstance(key, str) or not isinstance(entries, list):
                continue
            clean_entries = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                text = entry.get("text")
                if not isinstance(text, str) or not text.strip():
                    continue
                created_at = entry.get("createdAt")
                review_id = entry.get("id")
                clean_entries.append(
                    {
                        "id": review_id if isinstance(review_id, str) else "",
                        "text": text.strip(),
                        "createdAt": created_at if isinstance(created_at, str) else "",
                    }
                )
            if clean_entries:
                reviews[key] = clean_entries

    updated_at = raw.get("updatedAt")
    return {
        "version": 1,
        "updatedAt": updated_at if isinstance(updated_at, str) else "",
        "reviews": reviews,
    }


def write_reviews(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def validate_review_payload(payload: dict[str, Any]) -> tuple[int, int, str, str]:
    try:
        dataset_number = int(payload.get("datasetNumber", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Dataset number is invalid.") from exc

    try:
        set_number = int(payload.get("setNumber", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Set number is invalid.") from exc

    stem = payload.get("stem")
    text = payload.get("text")

    if dataset_number <= 0:
        raise ValueError("Dataset number is invalid.")
    if set_number not in SET_NUMBERS:
        raise ValueError("Set number is invalid.")
    if stem not in EXPECTED_IMAGES:
        raise ValueError("Image stem is invalid.")
    if not isinstance(text, str):
        raise ValueError("Review text is invalid.")

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Review text is empty.")
    if len(clean_text) > MAX_REVIEW_LENGTH:
        raise ValueError(f"Review text is too long. Use {MAX_REVIEW_LENGTH} characters or fewer.")

    return dataset_number, set_number, str(stem), clean_text


def append_review(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    dataset_number, set_number, stem, text = validate_review_payload(payload)
    reviews_payload = load_reviews(path)
    now = datetime.now().isoformat(timespec="seconds")
    key = review_key(dataset_number, set_number, stem)
    seed = f"{key}:{now}:{text}".encode("utf-8")
    entry = {
        "id": hashlib.sha1(seed).hexdigest()[:12],
        "text": text,
        "createdAt": now,
    }
    reviews = reviews_payload.setdefault("reviews", {})
    assert isinstance(reviews, dict)
    entries = reviews.setdefault(key, [])
    assert isinstance(entries, list)
    entries.append(entry)
    reviews_payload["updatedAt"] = now
    write_reviews(path, reviews_payload)
    return {
        "ok": True,
        "key": key,
        "review": entry,
        "reviews": reviews_payload,
    }
