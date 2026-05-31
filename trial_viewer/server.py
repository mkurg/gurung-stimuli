#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
WORKSPACE_DIR = APP_DIR.parent

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
CORE_IMAGES = ["ic_1", "coh_1", "coh_2", "tr_target", "it_target"]
ENDING_IMAGES = ["end_coh_it", "end_ic_tr", "end_ic_it"]
EXPECTED_IMAGES = CORE_IMAGES + ENDING_IMAGES

TRIAL_PATHS = [
    {
        "id": "transitive-cohesive",
        "name": "Transitive cohesive",
        "steps": ["coh_1", "coh_2", "tr_target"],
    },
    {
        "id": "intransitive-cohesive",
        "name": "Intransitive cohesive",
        "steps": ["coh_1", "coh_2", "it_target", "end_coh_it"],
    },
    {
        "id": "transitive-incohesive",
        "name": "Transitive incohesive",
        "steps": ["ic_1", "tr_target", "end_ic_tr"],
    },
    {
        "id": "intransitive-incohesive",
        "name": "Intransitive incohesive",
        "steps": ["ic_1", "it_target", "end_ic_it"],
    },
]


def natural_key(value: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def candidate_roots() -> list[Path]:
    roots: list[Path] = []

    env_root = os.environ.get("GURUNG_STIMULI_ROOT")
    if env_root:
        roots.append(Path(env_root).expanduser())

    for name in ("Gurung stimuli", "stimuli", "data"):
        roots.append(WORKSPACE_DIR / name)

    cloud_storage = Path.home() / "Library" / "CloudStorage"
    if cloud_storage.exists():
        for google_drive in sorted(cloud_storage.glob("GoogleDrive-*"), key=lambda p: p.name):
            shortcut_root = google_drive / ".shortcut-targets-by-id"
            if shortcut_root.exists():
                roots.extend(sorted(shortcut_root.glob("*/Gurung stimuli"), key=lambda p: str(p)))
            roots.append(google_drive / "My Drive" / "Gurung stimuli")

    roots.append(
        Path.home()
        / "Library"
        / "CloudStorage"
        / "GoogleDrive-apazent@gmail.com"
        / ".shortcut-targets-by-id"
        / "1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p"
        / "Gurung stimuli"
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def resolve_data_root(explicit_root: str | None = None) -> Path:
    candidates = [Path(explicit_root).expanduser()] if explicit_root else candidate_roots()
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()

    checked = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(
        "Could not find the Gurung stimuli folder. Set GURUNG_STIMULI_ROOT or pass --root.\n"
        f"Checked:\n{checked}"
    )


def parse_dataset_folder(path: Path) -> tuple[int, str] | None:
    match = re.match(r"^(\d+)_(.+)$", path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def file_info(path: Path, dataset_number: int, variant: str) -> dict[str, object]:
    stat = path.stat()
    return {
        "filename": path.name,
        "stem": path.stem,
        "url": f"/image/{dataset_number}/{variant}/{quote(path.name)}",
        "bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def scan_image_dir(folder: Path, dataset_number: int, variant: str) -> dict[str, object]:
    exists = folder.is_dir()
    files: list[dict[str, object]] = []

    if exists:
        for child in sorted(folder.iterdir(), key=lambda p: natural_key(p.name)):
            if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(file_info(child, dataset_number, variant))

    by_stem: dict[str, dict[str, object]] = {}
    for image in files:
        by_stem.setdefault(str(image["stem"]).lower(), image)

    images: dict[str, dict[str, object] | None] = {
        stem: by_stem.get(stem.lower()) for stem in EXPECTED_IMAGES
    }
    expected_stems = {stem.lower() for stem in EXPECTED_IMAGES}
    extra = [image for image in files if str(image["stem"]).lower() not in expected_stems]
    missing = [stem for stem, image in images.items() if image is None]

    return {
        "exists": exists,
        "path": str(folder),
        "fileCount": len(files),
        "images": images,
        "core": {stem: images[stem] for stem in CORE_IMAGES},
        "endings": {stem: images[stem] for stem in ENDING_IMAGES},
        "missing": missing,
        "extra": extra,
        "complete": exists and not missing,
    }


def scan_datasets(root: Path) -> dict[str, object]:
    datasets: list[dict[str, object]] = []

    for folder in sorted(root.iterdir(), key=lambda p: natural_key(p.name)):
        if not folder.is_dir():
            continue
        parsed = parse_dataset_folder(folder)
        if not parsed:
            continue

        dataset_number, label = parsed
        existing = scan_image_dir(folder, dataset_number, "existing")
        draft = scan_image_dir(folder / "2", dataset_number, "draft")

        issue_tags: list[str] = []
        if not existing["complete"]:
            issue_tags.append("existing-missing")
        if not draft["exists"]:
            issue_tags.append("draft-missing")
        elif draft["fileCount"] == 0:
            issue_tags.append("draft-empty")
        elif not draft["complete"]:
            issue_tags.append("draft-incomplete")
        if existing["extra"] or draft["extra"]:
            issue_tags.append("extra-images")
        draft_missing_endings = [
            stem for stem in ENDING_IMAGES if draft["images"].get(stem) is None
        ]
        if draft_missing_endings:
            if draft["exists"] and draft["fileCount"] > 0:
                issue_tags.append("draft-needs-endings")

        datasets.append(
            {
                "number": dataset_number,
                "folderName": folder.name,
                "displayName": label.replace(" ", "_"),
                "folderPath": str(folder),
                "existing": existing,
                "draft": draft,
                "issueTags": sorted(set(issue_tags)),
            }
        )

    summary = {
        "datasetCount": len(datasets),
        "existingComplete": sum(1 for item in datasets if item["existing"]["complete"]),
        "existingWithProblems": sum(1 for item in datasets if not item["existing"]["complete"]),
        "draftFolders": sum(1 for item in datasets if item["draft"]["exists"]),
        "draftComplete": sum(1 for item in datasets if item["draft"]["complete"]),
        "draftEmpty": sum(
            1 for item in datasets if item["draft"]["exists"] and item["draft"]["fileCount"] == 0
        ),
        "draftNeedsEndings": sum(
            1 for item in datasets if "draft-needs-endings" in item["issueTags"]
        ),
        "extraImages": sum(
            len(item["existing"]["extra"]) + len(item["draft"]["extra"]) for item in datasets
        ),
    }

    return {
        "root": str(root),
        "expected": EXPECTED_IMAGES,
        "core": CORE_IMAGES,
        "endings": ENDING_IMAGES,
        "paths": TRIAL_PATHS,
        "summary": summary,
        "scannedAt": datetime.now().isoformat(timespec="seconds"),
        "datasets": datasets,
    }


class TrialViewerHandler(SimpleHTTPRequestHandler):
    data_root: Path

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = parsed.path
        if clean == "/":
            clean = "/index.html"
        clean = clean.lstrip("/")
        return str((STATIC_DIR / clean).resolve())

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/datasets":
            self.send_json(scan_datasets(self.data_root))
            return
        if parsed.path.startswith("/image/"):
            self.send_image(parsed.path)
            return
        super().do_GET()

    def send_json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_image(self, request_path: str) -> None:
        parts = request_path.split("/", 4)
        if len(parts) != 5:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Image URL is incomplete.")
            return

        _, _, dataset_text, variant, encoded_filename = parts
        if variant not in {"existing", "draft"}:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown image variant.")
            return
        if not dataset_text.isdigit():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown dataset.")
            return

        filename = unquote(encoded_filename)
        if Path(filename).name != filename or "\x00" in filename:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Invalid filename.")
            return
        if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Unsupported image type.")
            return

        dataset_number = int(dataset_text)
        dataset_folder = next(
            (
                folder
                for folder in self.data_root.iterdir()
                if folder.is_dir()
                and (parsed := parse_dataset_folder(folder))
                and parsed[0] == dataset_number
            ),
            None,
        )
        if dataset_folder is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Dataset not found.")
            return

        image_dir = dataset_folder if variant == "existing" else dataset_folder / "2"
        image_path = (image_dir / filename).resolve()
        try:
            image_path.relative_to(image_dir.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Image is outside the dataset folder.")
            return
        if not image_path.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Image not found.")
            return

        content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(image_path.stat().st_size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with image_path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


def bind_server(host: str, port: int, strict_port: bool) -> ThreadingHTTPServer:
    attempts = [port] if strict_port else range(port, port + 20)
    last_error: OSError | None = None
    for candidate_port in attempts:
        try:
            return ThreadingHTTPServer((host, candidate_port), TrialViewerHandler)
        except OSError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Local viewer for Gurung experimental trials.")
    parser.add_argument("--root", help="Path to the Gurung stimuli folder.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    parser.add_argument("--strict-port", action="store_true")
    args = parser.parse_args()

    try:
        TrialViewerHandler.data_root = resolve_data_root(args.root)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    server = bind_server(args.host, args.port, args.strict_port)
    host, port = server.server_address
    print(f"Trial viewer: http://{host}:{port}", flush=True)
    print(f"Data root: {TrialViewerHandler.data_root}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
