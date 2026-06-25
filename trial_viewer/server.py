#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import html
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

from reviews import append_review, delete_review as delete_review_entry, load_reviews, set_review_status


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
WORKSPACE_DIR = APP_DIR.parent
IDEAS_FILE = APP_DIR / "missing_picture_ideas.json"
REVIEWS_FILE = Path(os.environ.get("GURUNG_REVIEWS_FILE", APP_DIR / "reviews.json")).expanduser()
MAX_IDEA_LENGTH = 5000
MAX_UPLOAD_BYTES = 24 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = 36 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30
CHROME_FETCH_TIMEOUT_SECONDS = 45
STATIC_EXPORT_TIMEOUT_SECONDS = 180
STATIC_PUBLISH_TIMEOUT_SECONDS = 120
DEFAULT_STATIC_REMOTE = ""
DEFAULT_ASSET_BASE_URL = ""

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SET_NUMBERS = [1, 2, 3, 4]
SET_ALIASES = {"existing": 1, "draft": 2}
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


def asset_version(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:12]


def versioned_index_html() -> bytes:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    versions = {
        "styles.css": asset_version(STATIC_DIR / "styles.css"),
        "app.js": asset_version(STATIC_DIR / "app.js"),
    }
    for filename, version in versions.items():
        html = html.replace(filename, f"{filename}?v={version}")
    return html.encode("utf-8")


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


def set_folder(dataset_folder: Path, set_number: int) -> Path:
    candidate = dataset_folder / str(set_number)
    if candidate.is_dir():
        return candidate
    if set_number == 1:
        return dataset_folder
    return candidate


def normalize_set_number(value: object) -> int | None:
    if isinstance(value, int) and value in SET_NUMBERS:
        return value
    text = str(value).strip().lower()
    if text in SET_ALIASES:
        return SET_ALIASES[text]
    if text.isdigit() and int(text) in SET_NUMBERS:
        return int(text)
    return None


def find_dataset_folder(root: Path, dataset_number: int) -> Path | None:
    return next(
        (
            folder
            for folder in root.iterdir()
            if folder.is_dir()
            and (parsed := parse_dataset_folder(folder))
            and parsed[0] == dataset_number
        ),
        None,
    )


def file_info(path: Path, dataset_number: int, set_number: int) -> dict[str, object]:
    stat = path.stat()
    return {
        "filename": path.name,
        "stem": path.stem,
        "url": f"/image/{dataset_number}/{set_number}/{quote(path.name)}",
        "bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def scan_image_dir(folder: Path, dataset_number: int, set_number: int) -> dict[str, object]:
    exists = folder.is_dir()
    files: list[dict[str, object]] = []

    if exists:
        for child in sorted(folder.iterdir(), key=lambda p: natural_key(p.name)):
            if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(file_info(child, dataset_number, set_number))

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
        "set": set_number,
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


def scan_datasets(root: Path, ideas: dict[str, dict[str, str]] | None = None) -> dict[str, object]:
    if ideas is None:
        ideas = load_ideas()

    datasets: list[dict[str, object]] = []

    for folder in sorted(root.iterdir(), key=lambda p: natural_key(p.name)):
        if not folder.is_dir():
            continue
        parsed = parse_dataset_folder(folder)
        if not parsed:
            continue

        dataset_number, label = parsed
        sets: dict[str, dict[str, object]] = {}
        for set_number in SET_NUMBERS:
            set_data = scan_image_dir(set_folder(folder, set_number), dataset_number, set_number)
            add_ideas_to_set(set_data, dataset_number, set_number, ideas)
            sets[str(set_number)] = set_data

        issue_tags: list[str] = []
        for set_number, set_data in sets.items():
            if not set_data["exists"]:
                issue_tags.append(f"set-{set_number}-missing")
            elif set_data["fileCount"] == 0:
                issue_tags.append(f"set-{set_number}-empty")
            elif not set_data["complete"]:
                issue_tags.append(f"set-{set_number}-incomplete")
            if any(set_data["images"].get(stem) is None for stem in CORE_IMAGES):
                issue_tags.append(f"set-{set_number}-core-incomplete")
            if (
                set_data["exists"]
                and set_data["fileCount"] > 0
                and any(set_data["images"].get(stem) is None for stem in ENDING_IMAGES)
            ):
                issue_tags.append(f"set-{set_number}-needs-endings")

        if any(set_data["extra"] for set_data in sets.values()):
            issue_tags.append("extra-images")

        datasets.append(
            {
                "number": dataset_number,
                "folderName": folder.name,
                "displayName": label.replace(" ", "_"),
                "folderPath": str(folder),
                "sets": sets,
                "issueTags": sorted(set(issue_tags)),
            }
        )

    ending_slot_count = len(datasets) * len(ENDING_IMAGES)
    set_summaries: dict[str, dict[str, object]] = {}
    all_ending_count = 0
    for set_number in SET_NUMBERS:
        set_key = str(set_number)
        ending_count = count_present_endings(datasets, set_number)
        all_ending_count += ending_count
        set_summaries[set_key] = {
            "folders": sum(1 for item in datasets if item["sets"][set_key]["exists"]),
            "complete": sum(1 for item in datasets if item["sets"][set_key]["complete"]),
            "empty": sum(
                1
                for item in datasets
                if item["sets"][set_key]["exists"] and item["sets"][set_key]["fileCount"] == 0
            ),
            "incomplete": sum(1 for item in datasets if not item["sets"][set_key]["complete"]),
            "coreIncomplete": sum(
                1
                for item in datasets
                if any(item["sets"][set_key]["images"].get(stem) is None for stem in CORE_IMAGES)
            ),
            "needsEndings": sum(
                1 for item in datasets if f"set-{set_key}-needs-endings" in item["issueTags"]
            ),
            "extraImages": sum(len(item["sets"][set_key]["extra"]) for item in datasets),
            "endings": progress_summary(ending_count, ending_slot_count),
        }

    summary = {
        "datasetCount": len(datasets),
        "sets": set_summaries,
        "extraImages": sum(
            len(set_data["extra"]) for item in datasets for set_data in item["sets"].values()
        ),
        "endings": {
            **{set_key: set_summary["endings"] for set_key, set_summary in set_summaries.items()},
            "all": progress_summary(all_ending_count, ending_slot_count * len(SET_NUMBERS)),
        },
        # Legacy summary fields kept for older local scripts that only know sets 1 and 2.
        "existingComplete": set_summaries["1"]["complete"],
        "existingWithProblems": set_summaries["1"]["incomplete"],
        "draftFolders": set_summaries["2"]["folders"],
        "draftComplete": set_summaries["2"]["complete"],
        "draftEmpty": set_summaries["2"]["empty"],
        "draftNeedsEndings": set_summaries["2"]["needsEndings"],
    }

    return {
        "root": str(root),
        "setNumbers": SET_NUMBERS,
        "expected": EXPECTED_IMAGES,
        "core": CORE_IMAGES,
        "endings": ENDING_IMAGES,
        "paths": TRIAL_PATHS,
        "summary": summary,
        "scannedAt": datetime.now().isoformat(timespec="seconds"),
        "datasets": datasets,
    }


def count_present_endings(datasets: list[dict[str, object]], set_number: int) -> int:
    set_key = str(set_number)
    return sum(
        1
        for dataset in datasets
        for stem in ENDING_IMAGES
        if dataset["sets"][set_key]["images"].get(stem) is not None
    )


def progress_summary(present: int, total: int) -> dict[str, object]:
    percent = round((present / total * 100), 1) if total else 0
    return {
        "present": present,
        "total": total,
        "missing": total - present,
        "percent": percent,
    }


def idea_key(dataset_number: int, set_number: int, stem: str) -> str:
    return f"{dataset_number}:{set_number}:{stem}"


def legacy_idea_keys(dataset_number: int, set_number: int, stem: str) -> list[str]:
    aliases = [name for name, number in SET_ALIASES.items() if number == set_number]
    return [f"{dataset_number}:{alias}:{stem}" for alias in aliases]


def load_ideas(path: Path = IDEAS_FILE) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(raw, dict):
        return {}

    ideas: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        text = value.get("text")
        updated_at = value.get("updatedAt")
        if not isinstance(text, str) or not text.strip():
            continue
        ideas[key] = {
            "text": text.strip(),
            "updatedAt": updated_at if isinstance(updated_at, str) else "",
        }
    return ideas


def write_ideas(ideas: dict[str, dict[str, str]], path: Path = IDEAS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(ideas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def image_bytes_kind(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    return None


def parse_data_url(data_url: object) -> bytes | None:
    if not isinstance(data_url, str):
        return None
    match = re.match(r"^data:image/[a-zA-Z0-9.+-]+;base64,(.+)$", data_url, re.DOTALL)
    if not match:
        return None
    try:
        data = base64.b64decode(match.group(1), validate=True)
    except (binascii.Error, ValueError):
        return None
    return data


def clean_source_url(source_url: str) -> str:
    return html.unescape(source_url.strip()).strip("\"'()[]<> \t\r\n")


def is_chatgpt_content_url(source_url: str) -> bool:
    parsed = urlparse(source_url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"chatgpt.com", "chat.openai.com"}
        and parsed.path.startswith("/backend-api/estuary/content")
    )


def browser_like_headers(source_url: str) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if is_chatgpt_content_url(source_url):
        headers["Referer"] = "https://chatgpt.com/"
    return headers


def fetch_chatgpt_image_with_chrome(source_url: str) -> bytes:
    osascript = shutil.which("osascript")
    if sys.platform != "darwin" or osascript is None:
        raise OSError("Protected ChatGPT image links require an open Chrome tab on macOS.")

    js_code = f"""
(() => {{
  const url = {json.dumps(source_url)};
  const xhr = new XMLHttpRequest();
  xhr.open("GET", url, false);
  xhr.overrideMimeType("text/plain; charset=x-user-defined");
  try {{
    xhr.send(null);
  }} catch (error) {{
    return JSON.stringify({{ ok: false, error: String(error && error.message ? error.message : error) }});
  }}
  if (xhr.status < 200 || xhr.status >= 300) {{
    return JSON.stringify({{ ok: false, error: `Chrome fetch returned HTTP ${{xhr.status}}` }});
  }}
  const contentType = (xhr.getResponseHeader("Content-Type") || "image/png").split(";")[0];
  if (!/^(image\\/|application\\/octet-stream$)/i.test(contentType)) {{
    return JSON.stringify({{ ok: false, error: `ChatGPT returned ${{contentType || "unknown content"}} instead of an image` }});
  }}
  const response = xhr.responseText || "";
  const chunks = [];
  const chunkSize = 0x8000;
  for (let offset = 0; offset < response.length; offset += chunkSize) {{
    const slice = response.slice(offset, offset + chunkSize);
    const chars = new Array(slice.length);
    for (let index = 0; index < slice.length; index += 1) {{
      chars[index] = String.fromCharCode(slice.charCodeAt(index) & 0xff);
    }}
    chunks.push(chars.join(""));
  }}
  return JSON.stringify({{ ok: true, contentType, data: btoa(chunks.join("")) }});
}})();
""".strip()

    apple_script = """
on run argv
  set jsCode to item 1 of argv
  tell application "Google Chrome"
    set targetTab to missing value
    repeat with browserWindow in windows
      repeat with browserTab in tabs of browserWindow
        set tabUrl to URL of browserTab
        if tabUrl starts with "https://chatgpt.com/" or tabUrl starts with "https://chat.openai.com/" then
          set targetTab to browserTab
          exit repeat
        end if
      end repeat
      if targetTab is not missing value then exit repeat
    end repeat
    if targetTab is missing value then error "No open ChatGPT tab found in Google Chrome."
    return execute targetTab javascript jsCode
  end tell
end run
""".strip()

    with tempfile.NamedTemporaryFile("w", suffix=".applescript", delete=False, encoding="utf-8") as script_file:
        script_file.write(apple_script)
        script_path = Path(script_file.name)
    try:
        result = subprocess.run(
            [osascript, str(script_path), js_code],
            capture_output=True,
            text=True,
            timeout=CHROME_FETCH_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise OSError("Timed out while asking Chrome to read the ChatGPT image.") from exc
    finally:
        script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        hint = (
            "Protected ChatGPT image links need Chrome permission. "
            "In Chrome, enable View > Developer > Allow JavaScript from Apple Events, "
            "keep a ChatGPT tab open, and try the drop again."
        )
        raise OSError(f"{hint} {details}".strip())

    try:
        payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise OSError("Chrome returned an unreadable image response.") from exc

    if not payload.get("ok"):
        raise OSError(str(payload.get("error") or "Chrome could not read the ChatGPT image."))

    try:
        data = base64.b64decode(str(payload["data"]), validate=True)
    except (KeyError, binascii.Error, ValueError) as exc:
        raise OSError("Chrome returned invalid image data.") from exc

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Image is too large.")
    return data


def download_image(source_url: object) -> bytes | None:
    if not isinstance(source_url, str):
        return None
    source_url = clean_source_url(source_url)
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        return None

    request = Request(source_url, headers=browser_like_headers(source_url))
    try:
        response = urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS)
    except HTTPError as exc:
        if exc.code in {401, 403} and is_chatgpt_content_url(source_url):
            return fetch_chatgpt_image_with_chrome(source_url)
        raise

    with response:
        content_type = response.headers.get("Content-Type", "")
        if content_type and "image/" not in content_type.lower() and "octet-stream" not in content_type.lower():
            return None

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise ValueError("Image is too large.")
            chunks.append(chunk)
        return b"".join(chunks)


def to_png_bytes(data: bytes) -> bytes:
    kind = image_bytes_kind(data)
    if kind is None:
        raise ValueError("Dropped data is not a recognized image.")
    if kind == "png":
        return data

    sips = shutil.which("sips")
    if sips is None:
        raise ValueError("Only PNG drops are supported unless macOS sips is available.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        input_path = tmp_path / f"input.{kind}"
        output_path = tmp_path / "output.png"
        input_path.write_bytes(data)
        result = subprocess.run(
            [sips, "-s", "format", "png", str(input_path), "--out", str(output_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not output_path.is_file():
            raise ValueError(result.stderr.strip() or result.stdout.strip() or "Could not convert image to PNG.")
        png_data = output_path.read_bytes()

    if image_bytes_kind(png_data) != "png":
        raise ValueError("Image conversion did not produce a PNG.")
    return png_data


def image_paths_for_stem(folder: Path, stem: str) -> list[Path]:
    if not folder.is_dir():
        return []
    return [
        child
        for child in folder.iterdir()
        if child.is_file()
        and child.stem.lower() == stem.lower()
        and child.suffix.lower() in IMAGE_EXTENSIONS
    ]


def atomic_write(path: Path, data: bytes) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_bytes(data)
    tmp_path.replace(path)


def env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def remote_child(remote_root: str, child: str) -> str:
    return f"{remote_root.rstrip('/')}/{child.strip('/')}/"


def split_ssh_remote(remote_root: str) -> tuple[str, str] | None:
    if remote_root.startswith("/") or ":" not in remote_root:
        return None
    host, path = remote_root.split(":", 1)
    if not host or not path.startswith("/"):
        return None
    return host, path.rstrip("/")


def completed_process_summary(result: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
    return output[-3000:] if output else ""


def run_static_export(data_root: Path) -> dict[str, object]:
    if not env_flag("GURUNG_STATIC_EXPORT_ON_UPLOAD", True):
        return {"ok": True, "skipped": True, "message": "Static export disabled."}

    asset_base_url = os.environ.get("GURUNG_ASSET_BASE_URL", DEFAULT_ASSET_BASE_URL)
    command = [
        sys.executable,
        str(APP_DIR / "export_static.py"),
        "--root",
        str(data_root),
        "--asset-base-url",
        asset_base_url,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=str(WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("GURUNG_STATIC_EXPORT_TIMEOUT", STATIC_EXPORT_TIMEOUT_SECONDS)),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Static export timed out."}

    summary = completed_process_summary(result)
    if result.returncode != 0:
        return {"ok": False, "error": summary or f"Static export failed with code {result.returncode}."}
    return {"ok": True, "output": summary}


def ensure_remote_site_dirs(remote_root: str) -> dict[str, object]:
    parsed = split_ssh_remote(remote_root)
    if parsed is None:
        return {"ok": True, "skipped": True}

    ssh = shutil.which("ssh")
    if ssh is None:
        return {"ok": False, "error": "ssh executable not found."}

    host, remote_path = parsed
    command = [
        ssh,
        host,
        "mkdir -p "
        f"{shlex.quote(remote_path)} "
        f"{shlex.quote(f'{remote_path}/data')} "
        f"{shlex.quote(f'{remote_path}/assets')}",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("GURUNG_STATIC_PUBLISH_TIMEOUT", STATIC_PUBLISH_TIMEOUT_SECONDS)),
        check=False,
    )
    if result.returncode != 0:
        return {"ok": False, "error": completed_process_summary(result) or "Could not create remote site folders."}
    return {"ok": True}


def run_rsync(source: Path, destination: str) -> dict[str, object]:
    rsync = shutil.which("rsync")
    if rsync is None:
        return {"ok": False, "error": "rsync executable not found."}

    result = subprocess.run(
        [rsync, "-az", "--delete", f"{source}/", destination],
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("GURUNG_STATIC_PUBLISH_TIMEOUT", STATIC_PUBLISH_TIMEOUT_SECONDS)),
        check=False,
    )
    if result.returncode != 0:
        return {"ok": False, "error": completed_process_summary(result) or f"rsync failed with code {result.returncode}."}
    return {"ok": True, "output": completed_process_summary(result)}


def publish_static_data_and_assets() -> dict[str, object]:
    if not env_flag("GURUNG_STATIC_PUBLISH_ON_UPLOAD", True):
        return {"ok": True, "skipped": True, "message": "Static publish disabled."}

    remote_root = os.environ.get("GURUNG_STATIC_REMOTE", DEFAULT_STATIC_REMOTE).strip()
    if not remote_root:
        return {"ok": True, "skipped": True, "message": "Static publish remote is not configured."}

    docs_dir = WORKSPACE_DIR / "docs"
    mkdir_result = ensure_remote_site_dirs(remote_root)
    if not mkdir_result.get("ok"):
        return mkdir_result

    steps = {
        "data": run_rsync(docs_dir / "data", remote_child(remote_root, "data")),
        "assets": run_rsync(docs_dir / "assets", remote_child(remote_root, "assets")),
    }
    failed = {name: result for name, result in steps.items() if not result.get("ok")}
    if failed:
        return {"ok": False, "steps": steps, "error": "; ".join(str(item.get("error")) for item in failed.values())}
    return {"ok": True, "steps": steps}


def refresh_static_site_after_upload(data_root: Path) -> dict[str, object]:
    export_result = run_static_export(data_root)
    publish_result: dict[str, object] = {"ok": False, "skipped": True, "message": "Skipped because export failed."}
    if export_result.get("ok"):
        publish_result = publish_static_data_and_assets()
    return {
        "ok": bool(export_result.get("ok") and publish_result.get("ok")),
        "export": export_result,
        "publish": publish_result,
    }


def add_ideas_to_set(
    set_data: dict[str, object],
    dataset_number: int,
    set_number: int,
    ideas: dict[str, dict[str, str]],
) -> None:
    set_data["ideas"] = {
        stem: next(
            (
                ideas[key]
                for key in [idea_key(dataset_number, set_number, stem)]
                + legacy_idea_keys(dataset_number, set_number, stem)
                if key in ideas
            ),
            None,
        )
        for stem in EXPECTED_IMAGES
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
        if parsed.path in {"/", "/index.html"}:
            self.send_index()
            return
        if parsed.path == "/api/datasets":
            self.send_json(scan_datasets(self.data_root))
            return
        if parsed.path == "/api/reviews":
            self.send_json(load_reviews(REVIEWS_FILE))
            return
        if parsed.path.startswith("/image/"):
            self.send_image(parsed.path)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/ideas":
            self.save_idea()
            return
        if parsed.path == "/api/upload-image":
            self.save_dropped_image()
            return
        if parsed.path == "/api/publish-static":
            self.publish_static_site()
            return
        if parsed.path == "/api/reviews":
            self.save_review()
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reviews":
            self.update_review()
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reviews":
            self.delete_saved_review()
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_index(self) -> None:
        body = versioned_index_html()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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

    def read_json_body(self, max_bytes: int = 20000) -> dict[str, object] | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid content length.")
            return None

        if content_length <= 0 or content_length > max_bytes:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid request body size.")
            return None

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
            return None

        if not isinstance(payload, dict):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be an object.")
            return None
        return payload

    def save_idea(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            dataset_number = int(payload.get("datasetNumber", ""))
        except (TypeError, ValueError):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Dataset number is invalid.")
            return

        set_number = normalize_set_number(payload.get("setNumber", payload.get("variant")))
        stem = payload.get("stem")
        text = payload.get("text", "")

        if set_number is None:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Set number is invalid.")
            return
        if stem not in EXPECTED_IMAGES:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Image stem is invalid.")
            return
        if not isinstance(text, str):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Idea text is invalid.")
            return

        if find_dataset_folder(self.data_root, dataset_number) is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Dataset not found.")
            return

        clean_text = text.strip()
        if len(clean_text) > MAX_IDEA_LENGTH:
            self.send_error_json(
                HTTPStatus.BAD_REQUEST,
                f"Idea text is too long. Use {MAX_IDEA_LENGTH} characters or fewer.",
            )
            return

        ideas = load_ideas()
        key = idea_key(dataset_number, set_number, stem)
        if clean_text:
            ideas[key] = {
                "text": clean_text,
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
            }
        else:
            ideas.pop(key, None)

        write_ideas(ideas)
        self.send_json({"ok": True, "idea": ideas.get(key), "key": key})

    def save_review(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            result = append_review(REVIEWS_FILE, payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not save review: {exc}")
            return

        self.send_json(result)

    def update_review(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            result = set_review_status(REVIEWS_FILE, payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not update review: {exc}")
            return

        self.send_json(result)

    def delete_saved_review(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            result = delete_review_entry(REVIEWS_FILE, payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not delete review: {exc}")
            return

        self.send_json(result)

    def publish_static_site(self) -> None:
        result = refresh_static_site_after_upload(self.data_root)
        self.send_json({"ok": bool(result.get("ok")), "staticRefresh": result})

    def save_dropped_image(self) -> None:
        payload = self.read_json_body(MAX_UPLOAD_REQUEST_BYTES)
        if payload is None:
            return

        try:
            dataset_number = int(payload.get("datasetNumber", ""))
        except (TypeError, ValueError):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Dataset number is invalid.")
            return

        set_number = normalize_set_number(payload.get("setNumber"))
        stem = payload.get("stem")
        overwrite = payload.get("overwrite") is True
        publish_static = payload.get("publishStatic") is not False

        if set_number is None:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Set number is invalid.")
            return
        if stem not in EXPECTED_IMAGES:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Image stem is invalid.")
            return

        dataset_folder = find_dataset_folder(self.data_root, dataset_number)
        if dataset_folder is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Dataset not found.")
            return

        image_dir = set_folder(dataset_folder, set_number)
        image_dir.mkdir(parents=True, exist_ok=True)
        try:
            image_dir.resolve().relative_to(dataset_folder.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Image folder is outside the dataset folder.")
            return

        existing_paths = image_paths_for_stem(image_dir, str(stem))
        if existing_paths and not overwrite:
            self.send_error_json(
                HTTPStatus.CONFLICT,
                f"{stem}.png would replace an existing image in set {set_number}.",
            )
            return

        try:
            raw_data = parse_data_url(payload.get("fileData"))
            if raw_data is None:
                raw_data = download_image(payload.get("sourceUrl"))
            if raw_data is None:
                self.send_error_json(HTTPStatus.BAD_REQUEST, "Drop an image file or image URL.")
                return
            if len(raw_data) > MAX_UPLOAD_BYTES:
                self.send_error_json(HTTPStatus.BAD_REQUEST, "Image is too large.")
                return

            png_data = to_png_bytes(raw_data)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.BAD_GATEWAY, f"Could not fetch image: {exc}")
            return

        output_path = (image_dir / f"{stem}.png").resolve()
        try:
            output_path.relative_to(image_dir.resolve())
        except ValueError:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Output path is outside the image folder.")
            return

        atomic_write(output_path, png_data)
        for old_path in existing_paths:
            if old_path.resolve() != output_path:
                old_path.unlink(missing_ok=True)

        static_refresh = (
            refresh_static_site_after_upload(self.data_root)
            if publish_static
            else {"ok": True, "skipped": True, "message": "Static publish deferred."}
        )
        self.send_json(
            {
                "ok": True,
                "datasetNumber": dataset_number,
                "setNumber": set_number,
                "stem": stem,
                "filename": output_path.name,
                "path": str(output_path),
                "staticRefresh": static_refresh,
            }
        )

    def send_image(self, request_path: str) -> None:
        parts = request_path.split("/", 4)
        if len(parts) != 5:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Image URL is incomplete.")
            return

        _, _, dataset_text, set_text, encoded_filename = parts
        set_number = normalize_set_number(set_text)
        if set_number is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown image set.")
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
        dataset_folder = find_dataset_folder(self.data_root, dataset_number)
        if dataset_folder is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Dataset not found.")
            return

        image_dir = set_folder(dataset_folder, set_number)
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
