#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


GOOGLE_DRIVE_ID = "1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p"
DEFAULT_QUALITY = 85
DEFAULT_SETS = ("1", "2", "3", "4")
DEFAULT_TARGET_SIZE = (1024, 1536)
DEFAULT_MTIME_TOLERANCE_SECONDS = 1.0


def default_google_drive_root() -> Path:
    return (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "GoogleDrive-apazent@gmail.com"
        / ".shortcut-targets-by-id"
        / GOOGLE_DRIVE_ID
        / "Gurung stimuli"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sets(value: str) -> tuple[str, ...]:
    sets = tuple(part.strip() for part in value.split(",") if part.strip())
    if not sets:
        raise argparse.ArgumentTypeError("At least one set id is required.")
    return sets


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value.strip().lower())
    if not match:
        raise argparse.ArgumentTypeError("Use WIDTHxHEIGHT, for example 1024x1536.")
    width = int(match.group(1))
    height = int(match.group(2))
    if width < 1 or height < 1:
        raise argparse.ArgumentTypeError("Width and height must be positive.")
    return width, height


def natural_key(value: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def discover_google_drive_numbered_sets(source_root: Path, sets: tuple[str, ...]) -> list[Path]:
    dataset_pattern = re.compile(r"^\d+_")
    files: list[Path] = []
    for dataset_dir in sorted(source_root.iterdir(), key=lambda path: natural_key(path.name)):
        if not dataset_dir.is_dir() or not dataset_pattern.match(dataset_dir.name):
            continue
        for set_id in sets:
            set_dir = dataset_dir / set_id
            if set_dir.is_dir():
                files.extend(sorted(set_dir.glob("*.png"), key=lambda path: natural_key(path.name)))
    return files


def discover_all_pngs(source_root: Path) -> list[Path]:
    return sorted(
        (path for path in source_root.rglob("*.png") if path.is_file() and not any(part.startswith(".") for part in path.parts)),
        key=lambda path: natural_key(str(path)),
    )


def choose_source_and_output(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.preset == "main-stimuli":
        source_root = Path(args.source_root or "discourse part/MainStimuli").expanduser().resolve()
        output_root = Path(args.output_root or "discourse part/MainStimuliJpeg").expanduser().resolve()
    else:
        source_root = Path(args.source_root or default_google_drive_root()).expanduser().resolve()
        output_root = Path(args.output_root or "discourse part/JpegStimuliFullRes").expanduser().resolve()
    return source_root, output_root


def identify_image(path: Path) -> tuple[int, int, str]:
    result = subprocess.run(
        ["magick", "identify", "-format", "%w,%h,%[colorspace]", str(path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    width_text, height_text, colorspace = result.stdout.strip().split(",", 2)
    return int(width_text), int(height_text), colorspace


def convert_png_to_jpeg(
    source: Path,
    target: Path,
    quality: int,
    resize_long_edge: int | None,
    target_size: tuple[int, int] | None,
) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "magick",
        str(source),
        "-auto-orient",
        "-colorspace",
        "sRGB",
        "-strip",
    ]
    if target_size is not None:
        width, height = target_size
        command.extend(["-resize", f"{width}x{height}^", "-gravity", "center", "-extent", f"{width}x{height}"])
    if resize_long_edge is not None:
        command.extend(["-resize", f"{resize_long_edge}x{resize_long_edge}>"])
    command.extend(
        [
            "-sampling-factor",
            "4:2:0",
            "-quality",
            str(quality),
        ]
    )
    command.append(str(target))
    subprocess.run(command, check=True)
    return "converted"


def should_convert(
    source: Path,
    target: Path,
    overwrite: bool,
    refresh_stale_or_wrong_size: bool,
    target_size: tuple[int, int] | None,
    mtime_tolerance_seconds: float,
) -> bool:
    if overwrite or not target.exists():
        return True
    if not refresh_stale_or_wrong_size:
        return False
    if target.stat().st_mtime + mtime_tolerance_seconds < source.stat().st_mtime:
        return True
    if target_size is not None:
        target_width, target_height, _ = identify_image(target)
        if (target_width, target_height) != target_size:
            return True
    return False


def build_rows(
    source_root: Path,
    output_root: Path,
    files: list[Path],
    quality: int,
    resize_long_edge: int | None,
    target_size: tuple[int, int] | None,
    overwrite: bool,
    refresh_stale_or_wrong_size: bool,
    mtime_tolerance_seconds: float,
    dry_run: bool,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, source in enumerate(files, start=1):
        relative_source = source.relative_to(source_root)
        relative_target = relative_source.with_suffix(".jpg")
        target = output_root / relative_target
        source_width, source_height, source_colorspace = identify_image(source)
        needs_convert = should_convert(
            source=source,
            target=target,
            overwrite=overwrite,
            refresh_stale_or_wrong_size=refresh_stale_or_wrong_size,
            target_size=target_size,
            mtime_tolerance_seconds=mtime_tolerance_seconds,
        )
        status = "would_convert" if needs_convert else "would_skip_exists"
        target_width = ""
        target_height = ""
        target_colorspace = ""
        target_bytes = ""
        target_sha256 = ""

        if not dry_run:
            if needs_convert:
                status = convert_png_to_jpeg(source, target, quality, resize_long_edge, target_size)
            else:
                status = "skipped_exists"
            if target.is_file():
                width, height, colorspace = identify_image(target)
                target_width = str(width)
                target_height = str(height)
                target_colorspace = colorspace
                target_bytes = str(target.stat().st_size)
                target_sha256 = sha256(target)

        rows.append(
            {
                "index": str(index),
                "status": status,
                "source_relative": str(relative_source),
                "target_relative": str(relative_target),
                "source_bytes": str(source.stat().st_size),
                "source_width": str(source_width),
                "source_height": str(source_height),
                "source_colorspace": source_colorspace,
                "target_bytes": target_bytes,
                "target_width": target_width,
                "target_height": target_height,
                "target_colorspace": target_colorspace,
                "target_sha256": target_sha256,
            }
        )
    return rows


def write_manifest(output_root: Path, rows: list[dict[str, str]], args: argparse.Namespace, source_root: Path) -> None:
    if not rows:
        return
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = output_root / "jpeg_stimuli_manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = output_root / "jpeg_stimuli_summary.txt"
    converted_rows = [row for row in rows if row["target_bytes"]]
    total_bytes = sum(int(row["target_bytes"]) for row in converted_rows)
    average_bytes = total_bytes / len(converted_rows) if converted_rows else 0
    summary.write_text(
        "\n".join(
            [
                f"generated_at={datetime.now().isoformat(timespec='seconds')}",
                f"preset={args.preset}",
                f"source_root={source_root}",
                f"output_root={output_root}",
                f"quality={args.quality}",
                f"resize_long_edge={args.resize_long_edge or ''}",
                f"target_size={'' if args.target_size is None else f'{args.target_size[0]}x{args.target_size[1]}'}",
                f"refresh_stale_or_wrong_size={args.refresh_stale_or_wrong_size}",
                f"dry_run={args.dry_run}",
                f"files={len(rows)}",
                f"converted_or_existing={len(converted_rows)}",
                f"total_jpeg_bytes={total_bytes}",
                f"average_jpeg_bytes={average_bytes:.1f}",
                f"average_jpeg_kb={average_bytes / 1024:.1f}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def select_files(args: argparse.Namespace, source_root: Path) -> list[Path]:
    if args.preset == "google-drive-numbered-sets":
        files = discover_google_drive_numbered_sets(source_root, args.sets)
    elif args.preset == "all-pngs":
        files = discover_all_pngs(source_root)
    elif args.preset == "main-stimuli":
        files = discover_all_pngs(source_root)
    else:
        raise ValueError(f"Unknown preset: {args.preset}")

    if args.sample:
        rng = random.Random(args.seed)
        files = sorted(rng.sample(files, min(args.sample, len(files))), key=lambda path: natural_key(str(path)))
    if args.limit:
        files = files[: args.limit]
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Gurung PNG stimuli to Git-friendly JPEGs while preserving folder structure.",
    )
    parser.add_argument(
        "--preset",
        choices=("google-drive-numbered-sets", "all-pngs", "main-stimuli"),
        default="google-drive-numbered-sets",
        help="Input layout to convert. Default converts numbered Google Drive dataset folders and set folders.",
    )
    parser.add_argument("--source-root", help="Override source root.")
    parser.add_argument("--output-root", help="Override output root.")
    parser.add_argument("--sets", type=parse_sets, default=DEFAULT_SETS, help="Comma-separated set folders for Google Drive preset.")
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY, help="JPEG quality, default 85.")
    parser.add_argument("--resize-long-edge", type=int, help="Optional max long edge. Omit to preserve full resolution.")
    parser.add_argument(
        "--target-size",
        type=parse_size,
        help=(
            "Normalize output to exact WIDTHxHEIGHT without stretching, using resize-to-cover and center crop. "
            "For the default Google Drive preset, omitted means 1024x1536."
        ),
    )
    parser.add_argument(
        "--preserve-source-size",
        action="store_true",
        help="Do not apply the default 1024x1536 normalization for the Google Drive preset.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing JPEGs.")
    parser.add_argument(
        "--refresh-stale-or-wrong-size",
        dest="refresh_stale_or_wrong_size",
        action="store_true",
        default=None,
        help="Regenerate existing JPEGs when the source PNG is newer or the target does not match --target-size. Default on for the Google Drive preset.",
    )
    parser.add_argument(
        "--no-refresh-stale-or-wrong-size",
        dest="refresh_stale_or_wrong_size",
        action="store_false",
        help="Do not refresh existing JPEGs unless they are missing or --overwrite is set.",
    )
    parser.add_argument(
        "--mtime-tolerance-seconds",
        type=float,
        default=DEFAULT_MTIME_TOLERANCE_SECONDS,
        help="How much older a JPEG may be before it is treated as stale.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only scan and write no outputs.")
    parser.add_argument("--sample", type=int, help="Convert a deterministic random sample instead of all files.")
    parser.add_argument("--seed", type=int, default=20260626, help="Random seed for --sample.")
    parser.add_argument("--limit", type=int, help="Convert only the first N discovered files.")
    return parser.parse_args()


def main() -> None:
    if shutil.which("magick") is None:
        raise SystemExit("ImageMagick 'magick' was not found. Install it with Homebrew before running this script.")

    args = parse_args()
    if not (1 <= args.quality <= 100):
        raise SystemExit("--quality must be between 1 and 100.")
    if args.preserve_source_size and (args.target_size is not None or args.resize_long_edge is not None):
        raise SystemExit("--preserve-source-size cannot be combined with --target-size or --resize-long-edge.")
    if args.target_size is None and args.preset == "google-drive-numbered-sets" and not args.preserve_source_size:
        args.target_size = DEFAULT_TARGET_SIZE
    if args.refresh_stale_or_wrong_size is None:
        args.refresh_stale_or_wrong_size = args.preset == "google-drive-numbered-sets"
    if args.target_size is not None and args.resize_long_edge is not None:
        raise SystemExit("--target-size and --resize-long-edge cannot be used together.")
    if args.mtime_tolerance_seconds < 0:
        raise SystemExit("--mtime-tolerance-seconds cannot be negative.")

    source_root, output_root = choose_source_and_output(args)
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist: {source_root}")

    files = select_files(args, source_root)
    if not files:
        raise SystemExit(f"No PNG files found under: {source_root}")

    rows = build_rows(
        source_root=source_root,
        output_root=output_root,
        files=files,
        quality=args.quality,
        resize_long_edge=args.resize_long_edge,
        target_size=args.target_size,
        overwrite=args.overwrite,
        refresh_stale_or_wrong_size=args.refresh_stale_or_wrong_size,
        mtime_tolerance_seconds=args.mtime_tolerance_seconds,
        dry_run=args.dry_run,
    )
    if not args.dry_run:
        write_manifest(output_root, rows, args, source_root)

    converted = sum(1 for row in rows if row["status"] == "converted")
    skipped = sum(1 for row in rows if row["status"].startswith("skipped"))
    would_convert = sum(1 for row in rows if row["status"] == "would_convert")
    would_skip = sum(1 for row in rows if row["status"].startswith("would_skip"))
    target_sizes = [int(row["target_bytes"]) for row in rows if row["target_bytes"]]
    average_kb = (sum(target_sizes) / len(target_sizes) / 1024) if target_sizes else 0
    print(f"source_root={source_root}")
    print(f"output_root={output_root}")
    print(
        f"files={len(rows)} converted={converted} skipped={skipped} "
        f"would_convert={would_convert} would_skip={would_skip} average_jpeg_kb={average_kb:.1f}"
    )
    if not args.dry_run:
        print(f"manifest={output_root / 'jpeg_stimuli_manifest.csv'}")


if __name__ == "__main__":
    main()
