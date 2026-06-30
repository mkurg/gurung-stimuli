#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


GOOGLE_DRIVE_ID = "1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p"
DEFAULT_SETS = ("1", "2", "3", "4")
EXPECTED_STEMS = (
    "ic_1",
    "coh_1",
    "coh_2",
    "tr_target",
    "it_target",
    "end_coh_it",
    "end_ic_tr",
    "end_ic_it",
)


@dataclass(frozen=True)
class CoverageRow:
    status: str
    source_relative: Path | None
    target_relative: Path
    source_path: Path | None
    target_path: Path


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


def parse_sets(value: str) -> tuple[str, ...]:
    sets = tuple(part.strip() for part in value.split(",") if part.strip())
    if not sets:
        raise argparse.ArgumentTypeError("At least one set id is required.")
    return sets


def natural_key(value: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def has_hidden_relative_part(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part.startswith(".") for part in parts)


def discover_source_pngs(source_root: Path, sets: tuple[str, ...], expected_only: bool) -> list[Path]:
    dataset_pattern = re.compile(r"^\d+_")
    expected = {stem.lower() for stem in EXPECTED_STEMS}
    sources: list[Path] = []

    for dataset_dir in sorted(source_root.iterdir(), key=lambda path: natural_key(path.name)):
        if not dataset_dir.is_dir() or not dataset_pattern.match(dataset_dir.name):
            continue
        for set_id in sets:
            set_dir = dataset_dir / set_id
            if not set_dir.is_dir():
                continue
            for source in sorted(set_dir.glob("*.png"), key=lambda path: natural_key(path.name)):
                if has_hidden_relative_part(source, source_root):
                    continue
                if expected_only and source.stem.lower() not in expected:
                    continue
                sources.append(source)

    return sources


def discover_target_jpegs(jpeg_root: Path) -> list[Path]:
    if not jpeg_root.is_dir():
        return []
    return sorted(
        (
            path
            for path in jpeg_root.rglob("*.jpg")
            if path.is_file() and not has_hidden_relative_part(path, jpeg_root)
        ),
        key=lambda path: natural_key(str(path.relative_to(jpeg_root))),
    )


def build_rows(
    source_root: Path,
    jpeg_root: Path,
    sources: list[Path],
    target_jpegs: list[Path],
    mtime_tolerance_seconds: float,
) -> list[CoverageRow]:
    target_relatives = {target.relative_to(jpeg_root) for target in target_jpegs}
    expected_target_relatives: set[Path] = set()
    rows: list[CoverageRow] = []

    for source in sources:
        source_relative = source.relative_to(source_root)
        target_relative = source_relative.with_suffix(".jpg")
        target_path = jpeg_root / target_relative
        expected_target_relatives.add(target_relative)

        if not target_path.is_file():
            status = "missing"
        elif target_path.stat().st_mtime + mtime_tolerance_seconds < source.stat().st_mtime:
            status = "stale"
        else:
            status = "ok"

        rows.append(
            CoverageRow(
                status=status,
                source_relative=source_relative,
                target_relative=target_relative,
                source_path=source,
                target_path=target_path,
            )
        )

    for orphan_relative in sorted(target_relatives - expected_target_relatives, key=lambda path: natural_key(str(path))):
        rows.append(
            CoverageRow(
                status="orphan",
                source_relative=None,
                target_relative=orphan_relative,
                source_path=None,
                target_path=jpeg_root / orphan_relative,
            )
        )

    return rows


def format_mtime(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def format_bytes(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return str(path.stat().st_size)


def write_csv(path: Path, rows: list[CoverageRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "status",
                "source_relative",
                "target_relative",
                "source_bytes",
                "target_bytes",
                "source_mtime",
                "target_mtime",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "status": row.status,
                    "source_relative": "" if row.source_relative is None else str(row.source_relative),
                    "target_relative": str(row.target_relative),
                    "source_bytes": format_bytes(row.source_path),
                    "target_bytes": format_bytes(row.target_path),
                    "source_mtime": format_mtime(row.source_path),
                    "target_mtime": format_mtime(row.target_path),
                }
            )


def print_group(label: str, rows: list[CoverageRow], limit: int) -> None:
    if not rows:
        return
    print(f"\n{label}:")
    for row in rows[:limit]:
        if row.source_relative is None:
            print(f"  {row.target_relative}")
        else:
            print(f"  {row.source_relative} -> {row.target_relative}")
    remaining = len(rows) - limit
    if remaining > 0:
        print(f"  ... {remaining} more")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report Google Drive PNG stimuli that do not yet have matching committed JPEGs.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=default_google_drive_root(),
        help="Google Drive Gurung stimuli root.",
    )
    parser.add_argument(
        "--jpeg-root",
        type=Path,
        default=Path("psychopy_gurung_v1/JpegStimuliFullRes"),
        help="JPEG mirror root to check.",
    )
    parser.add_argument("--sets", type=parse_sets, default=DEFAULT_SETS, help="Comma-separated set folders to scan.")
    parser.add_argument(
        "--expected-only",
        action="store_true",
        help="Only check canonical experiment image stems instead of every PNG in numbered set folders.",
    )
    parser.add_argument(
        "--mtime-tolerance-seconds",
        type=float,
        default=1.0,
        help="Target JPEGs older than source PNGs by more than this are reported as stale.",
    )
    parser.add_argument("--csv", type=Path, help="Optional CSV report path.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to print per problem group.")
    parser.add_argument("--no-fail", action="store_true", help="Always exit 0, even when missing or stale JPEGs exist.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_root = args.source_root.expanduser().resolve()
    jpeg_root = args.jpeg_root.expanduser().resolve()

    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist: {source_root}")
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1.")

    sources = discover_source_pngs(source_root, args.sets, args.expected_only)
    target_jpegs = discover_target_jpegs(jpeg_root)
    rows = build_rows(source_root, jpeg_root, sources, target_jpegs, args.mtime_tolerance_seconds)

    missing = [row for row in rows if row.status == "missing"]
    stale = [row for row in rows if row.status == "stale"]
    orphan = [row for row in rows if row.status == "orphan"]
    ok = [row for row in rows if row.status == "ok"]

    if args.csv:
        write_csv(args.csv.expanduser().resolve(), rows)

    print(f"source_root={source_root}")
    print(f"jpeg_root={jpeg_root}")
    print(f"sets={','.join(args.sets)} expected_only={args.expected_only}")
    print(
        "source_pngs={source_pngs} target_jpegs={target_jpegs} ok={ok} missing={missing} stale={stale} orphan={orphan}".format(
            source_pngs=len(sources),
            target_jpegs=len(target_jpegs),
            ok=len(ok),
            missing=len(missing),
            stale=len(stale),
            orphan=len(orphan),
        )
    )

    print_group("Missing JPEGs", missing, args.limit)
    print_group("Stale JPEGs", stale, args.limit)
    print_group("Orphan JPEGs", orphan, args.limit)

    if not missing and not stale:
        print("\ncoverage=OK")
    else:
        print("\ncoverage=PENDING")

    if (missing or stale) and not args.no_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
