#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from server import SET_NUMBERS, WORKSPACE_DIR, resolve_data_root, scan_datasets


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
DEFAULT_DOCS_DIR = WORKSPACE_DIR / "docs"
DEFAULT_ASSET_BASE_URL = "https://gurung.duckdns.org"


def safe_slug(value: str) -> str:
    allowed = []
    for char in value.strip().replace(" ", "_"):
        if char.isalnum() or char in {"-", "_", "."}:
            allowed.append(char)
        else:
            allowed.append("_")
    slug = "".join(allowed).strip("._")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "item"


def convert_image(
    source: Path,
    destination: Path,
    cwebp: str,
    max_width: int,
    quality: int,
    force: bool,
) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not force and destination.exists() and destination.stat().st_mtime >= source.stat().st_mtime:
        return False

    command = [
        cwebp,
        "-q",
        str(quality),
        "-m",
        "6",
        "-mt",
        "-resize",
        str(max_width),
        "0",
        "-resize_mode",
        "down_only",
        str(source),
        "-o",
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not convert {source}:\n{result.stdout.strip()}\n{result.stderr.strip()}"
        )
    return True


def asset_url(relative_path: str, asset_base_url: str) -> str:
    base = asset_base_url.strip().rstrip("/")
    return f"{base}/{relative_path}" if base else relative_path


def exported_image_info(
    source: Path,
    destination: Path,
    url: str,
    stem: str,
    original_filename: str,
) -> dict[str, object]:
    source_stat = source.stat()
    output_stat = destination.stat()
    return {
        "filename": destination.name,
        "originalFilename": original_filename,
        "stem": stem,
        "url": url,
        "bytes": output_stat.st_size,
        "sourceBytes": source_stat.st_size,
        "modified": datetime.fromtimestamp(source_stat.st_mtime).isoformat(timespec="seconds"),
    }


def replace_image_metadata(
    folder_slug: str,
    source_dir: Path,
    set_key: str,
    image: dict[str, object] | None,
    docs_dir: Path,
    cwebp: str,
    max_width: int,
    quality: int,
    force: bool,
    asset_base_url: str,
    expected_assets: set[Path],
    counters: dict[str, int],
) -> dict[str, object] | None:
    if image is None:
        return None

    source = source_dir / str(image["filename"])
    stem = str(image["stem"])
    output_name = f"{safe_slug(stem)}.webp"
    output = docs_dir / "assets" / folder_slug / set_key / output_name
    relative_url = f"assets/{folder_slug}/{set_key}/{output_name}"
    url = asset_url(relative_url, asset_base_url)

    converted = convert_image(source, output, cwebp, max_width, quality, force)
    expected_assets.add(output.resolve())
    counters["converted" if converted else "skipped"] += 1

    return exported_image_info(source, output, url, stem, str(image["filename"]))


def convert_set(
    dataset: dict[str, object],
    set_key: str,
    docs_dir: Path,
    cwebp: str,
    max_width: int,
    quality: int,
    force: bool,
    asset_base_url: str,
    expected_assets: set[Path],
    counters: dict[str, int],
) -> None:
    sets = dataset["sets"]
    assert isinstance(sets, dict)
    set_data = sets[set_key]
    assert isinstance(set_data, dict)

    folder_slug = safe_slug(str(dataset["folderName"]))
    source_dir = Path(str(set_data["path"]))
    set_data["path"] = f"assets/{folder_slug}/{set_key}"

    images = set_data["images"]
    assert isinstance(images, dict)
    for stem, image in list(images.items()):
        images[stem] = replace_image_metadata(
            folder_slug,
            source_dir,
            set_key,
            image,
            docs_dir,
            cwebp,
            max_width,
            quality,
            force,
            asset_base_url,
            expected_assets,
            counters,
        )

    set_data["core"] = {stem: images[stem] for stem in set_data["core"]}
    set_data["endings"] = {stem: images[stem] for stem in set_data["endings"]}

    extra = set_data["extra"]
    assert isinstance(extra, list)
    set_data["extra"] = [
        replace_image_metadata(
            folder_slug,
            source_dir,
            set_key,
            image,
            docs_dir,
            cwebp,
            max_width,
            quality,
            force,
            asset_base_url,
            expected_assets,
            counters,
        )
        for image in extra
    ]


def clean_stale_assets(assets_dir: Path, expected_assets: set[Path]) -> int:
    if not assets_dir.exists():
        return 0

    removed = 0
    for path in sorted(assets_dir.rglob("*.webp")):
        if path.resolve() not in expected_assets:
            path.unlink()
            removed += 1

    for path in sorted(assets_dir.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass

    return removed


def asset_version(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:12]


def versioned_html(filename: str, assets: tuple[str, ...]) -> str:
    html = (STATIC_DIR / filename).read_text(encoding="utf-8")
    versions = {asset: asset_version(STATIC_DIR / asset) for asset in assets}
    for filename, version in versions.items():
        html = html.replace(filename, f"{filename}?v={version}")
    return html


def copy_static_files(docs_dir: Path) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in ("styles.css", "app.js", "lists.css", "lists.js"):
        shutil.copy2(STATIC_DIR / name, docs_dir / name)
    (docs_dir / "index.html").write_text(
        versioned_html("index.html", ("styles.css", "app.js")),
        encoding="utf-8",
    )
    (docs_dir / "lists.html").write_text(
        versioned_html("lists.html", ("lists.css", "lists.js")),
        encoding="utf-8",
    )
    (docs_dir / ".nojekyll").write_text("", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def export_static(args: argparse.Namespace) -> dict[str, int | str]:
    data_root = resolve_data_root(args.root)
    docs_dir = Path(args.out).expanduser().resolve()
    cwebp = shutil.which(args.cwebp)
    if cwebp is None:
        raise FileNotFoundError(f"Could not find cwebp executable: {args.cwebp}")

    data = scan_datasets(data_root)
    data["root"] = "static export"
    data["exportedAt"] = datetime.now().isoformat(timespec="seconds")
    data["export"] = {
        "imageFormat": "webp",
        "maxWidth": args.max_width,
        "quality": args.quality,
        "assetBaseUrl": args.asset_base_url,
    }

    copy_static_files(docs_dir)

    expected_assets: set[Path] = set()
    counters = {"converted": 0, "skipped": 0}

    for dataset in data["datasets"]:
        assert isinstance(dataset, dict)
        dataset["folderPath"] = f"assets/{safe_slug(str(dataset['folderName']))}"
        for set_number in SET_NUMBERS:
            convert_set(
                dataset,
                str(set_number),
                docs_dir,
                cwebp,
                args.max_width,
                args.quality,
                args.force,
                args.asset_base_url,
                expected_assets,
                counters,
            )

    removed = clean_stale_assets(docs_dir / "assets", expected_assets)

    write_json(docs_dir / "data" / "datasets.json", data)
    write_json(
        docs_dir / "data" / "export-info.json",
        {
            "exportedAt": data["exportedAt"],
            "sourceRoot": "local Drive export",
            "docsDir": "docs",
            "converted": counters["converted"],
            "skipped": counters["skipped"],
            "removedStaleAssets": removed,
            "datasetCount": data["summary"]["datasetCount"],
            "sets": SET_NUMBERS,
            "assetBaseUrl": args.asset_base_url,
        },
    )

    return {
        "docsDir": str(docs_dir),
        "converted": counters["converted"],
        "skipped": counters["skipped"],
        "removed": removed,
        "datasets": data["summary"]["datasetCount"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the Gurung trial viewer as a GitHub Pages site.")
    parser.add_argument("--root", help="Path to the Gurung stimuli folder.")
    parser.add_argument("--out", default=str(DEFAULT_DOCS_DIR), help="Output directory, default: docs")
    parser.add_argument("--max-width", type=int, default=640, help="Maximum exported image width.")
    parser.add_argument("--quality", type=int, default=76, help="WebP quality, 0-100.")
    parser.add_argument("--cwebp", default="cwebp", help="Path or name of the cwebp executable.")
    parser.add_argument("--force", action="store_true", help="Rebuild all WebP images.")
    parser.add_argument(
        "--asset-base-url",
        default=os.environ.get("GURUNG_ASSET_BASE_URL", DEFAULT_ASSET_BASE_URL),
        help=(
            "Base URL for exported image URLs. Use an empty string for relative docs/assets URLs. "
            f"Default: {DEFAULT_ASSET_BASE_URL}"
        ),
    )
    args = parser.parse_args()

    try:
        result = export_static(args)
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {result['datasets']} datasets to {result['docsDir']}")
    print(f"WebP images converted: {result['converted']}")
    print(f"WebP images already current: {result['skipped']}")
    print(f"Stale WebP assets removed: {result['removed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
