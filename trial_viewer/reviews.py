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
REVIEW_STATUSES = {"open", "on_review", "done", "deferred"}
REVIEW_STATUS_ALIASES = {
    "on review": "on_review",
    "on-review": "on_review",
}


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

    reviews: dict[str, list[dict[str, Any]]] = {}
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
                status = normalize_review_status(entry)
                done = status == "done"
                clean_entry: dict[str, Any] = {
                    "id": review_id if isinstance(review_id, str) else "",
                    "text": text.strip(),
                    "createdAt": created_at if isinstance(created_at, str) else "",
                    "status": status,
                    "done": done,
                }
                done_at = entry.get("doneAt")
                if done and isinstance(done_at, str):
                    clean_entry["doneAt"] = done_at
                deferred_at = entry.get("deferredAt")
                if status == "deferred" and isinstance(deferred_at, str):
                    clean_entry["deferredAt"] = deferred_at
                on_review_at = entry.get("onReviewAt")
                if status == "on_review" and isinstance(on_review_at, str):
                    clean_entry["onReviewAt"] = on_review_at
                clean_entries.append(clean_entry)
            if clean_entries:
                reviews[key] = clean_entries

    updated_at = raw.get("updatedAt")
    return {
        "version": 1,
        "updatedAt": updated_at if isinstance(updated_at, str) else "",
        "reviews": reviews,
    }


def normalize_review_status(entry: dict[str, Any]) -> str:
    status = normalize_review_status_value(entry.get("status"))
    if status:
        return status
    return "done" if entry.get("done") is True else "open"


def normalize_review_status_value(status: Any) -> str | None:
    if not isinstance(status, str):
        return None
    clean_status = status.strip().lower()
    canonical_status = REVIEW_STATUS_ALIASES.get(clean_status, clean_status)
    return canonical_status if canonical_status in REVIEW_STATUSES else None


def write_reviews(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def validate_review_target(payload: dict[str, Any]) -> tuple[int, int, str]:
    try:
        dataset_number = int(payload.get("datasetNumber", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Dataset number is invalid.") from exc

    try:
        set_number = int(payload.get("setNumber", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Set number is invalid.") from exc

    stem = payload.get("stem")
    if dataset_number <= 0:
        raise ValueError("Dataset number is invalid.")
    if set_number not in SET_NUMBERS:
        raise ValueError("Set number is invalid.")
    if stem not in EXPECTED_IMAGES:
        raise ValueError("Image stem is invalid.")

    return dataset_number, set_number, str(stem)


def validate_review_payload(payload: dict[str, Any]) -> tuple[int, int, str, str]:
    dataset_number, set_number, stem = validate_review_target(payload)
    text = payload.get("text")

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
        "status": "open",
        "done": False,
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


def delete_review(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    dataset_number, set_number, stem = validate_review_target(payload)
    review_id = payload.get("id", payload.get("reviewId"))
    if not isinstance(review_id, str) or not review_id.strip():
        raise ValueError("Review id is invalid.")

    clean_review_id = review_id.strip()
    reviews_payload = load_reviews(path)
    key = review_key(dataset_number, set_number, stem)
    reviews = reviews_payload.setdefault("reviews", {})
    assert isinstance(reviews, dict)
    entries = reviews.get(key, [])
    if not isinstance(entries, list):
        entries = []

    kept_entries = [
        entry for entry in entries if not isinstance(entry, dict) or entry.get("id") != clean_review_id
    ]
    if len(kept_entries) == len(entries):
        raise ValueError("Review not found.")

    if kept_entries:
        reviews[key] = kept_entries
    else:
        reviews.pop(key, None)

    reviews_payload["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    write_reviews(path, reviews_payload)
    return {
        "ok": True,
        "key": key,
        "deletedId": clean_review_id,
        "reviews": reviews_payload,
    }


def set_review_done(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if "done" not in payload or not isinstance(payload.get("done"), bool):
        raise ValueError("Review done state is invalid.")
    return set_review_status(path, {**payload, "status": "done" if payload["done"] else "open"})


def set_review_status(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    dataset_number, set_number, stem = validate_review_target(payload)
    review_id = payload.get("id", payload.get("reviewId"))
    if not isinstance(review_id, str) or not review_id.strip():
        raise ValueError("Review id is invalid.")
    status = normalize_review_status_value(payload.get("status"))
    if status is None and isinstance(payload.get("done"), bool):
        status = "done" if payload["done"] else "open"
    if status is None:
        raise ValueError("Review status is invalid.")

    clean_review_id = review_id.strip()
    reviews_payload = load_reviews(path)
    key = review_key(dataset_number, set_number, stem)
    reviews = reviews_payload.setdefault("reviews", {})
    assert isinstance(reviews, dict)
    entries = reviews.get(key, [])
    if not isinstance(entries, list):
        entries = []

    now = datetime.now().isoformat(timespec="seconds")
    updated_entry: dict[str, Any] | None = None
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == clean_review_id:
            entry["status"] = status
            entry["done"] = status == "done"
            if status == "done":
                entry["doneAt"] = now
                entry.pop("deferredAt", None)
                entry.pop("onReviewAt", None)
            elif status == "on_review":
                entry["onReviewAt"] = now
                entry.pop("doneAt", None)
                entry.pop("deferredAt", None)
            elif status == "deferred":
                entry["deferredAt"] = now
                entry.pop("doneAt", None)
                entry.pop("onReviewAt", None)
            else:
                entry.pop("doneAt", None)
                entry.pop("deferredAt", None)
                entry.pop("onReviewAt", None)
            updated_entry = entry
            break

    if updated_entry is None:
        raise ValueError("Review not found.")

    reviews_payload["updatedAt"] = now
    write_reviews(path, reviews_payload)
    return {
        "ok": True,
        "key": key,
        "review": updated_entry,
        "reviews": reviews_payload,
    }
