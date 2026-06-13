#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASETS_JSON = ROOT / "docs" / "data" / "datasets.json"
OUTPUT_JSON = ROOT / "trial_viewer" / "image_descriptions.json"
EXPECTED_IMAGES = [
    "ic_1",
    "coh_1",
    "coh_2",
    "tr_target",
    "it_target",
    "end_coh_it",
    "end_ic_tr",
    "end_ic_it",
]
SET_VARIANTS = {
    1: "existing",
    2: "draft",
}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def source_data() -> dict[str, Any]:
    data = load_json(DATASETS_JSON)
    return {
        f"{dataset['number']}:{set_number}": {
            "dataset_number": dataset["number"],
            "dataset_name": dataset["displayName"],
            "set": set_number,
            "source_format": "webp",
            "source_dir": dataset[variant]["path"],
            "images": {
                stem: dataset[variant]["images"][stem]
                for stem in EXPECTED_IMAGES
            },
        }
        for dataset in data["datasets"]
        for set_number, variant in SET_VARIANTS.items()
    }


def ordered_keys(sources: dict[str, Any]) -> list[str]:
    return [
        f"{dataset_number}:{set_number}"
        for dataset_number in sorted({source["dataset_number"] for source in sources.values()})
        for set_number in (1, 2)
    ]


def empty_payload(sources: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "gurung-image-descriptions-v1",
        "description": "Vision-generated descriptions of Gurung stimulus WebP images.",
        "source": {
            "datasets_json": "docs/data/datasets.json",
            "image_root": "docs/assets",
            "source_format": "webp",
        },
        "order": "set 1 dataset 1 -> set 2 dataset 1 -> set 1 dataset 2 -> set 2 dataset 2 -> ...",
        "createdAt": now(),
        "updatedAt": now(),
        "status": {
            "completedGroups": 0,
            "totalGroups": len(sources),
            "completedImages": 0,
            "totalImages": len(sources) * len(EXPECTED_IMAGES),
        },
        "groups": [],
    }


def load_payload(sources: dict[str, Any]) -> dict[str, Any]:
    if OUTPUT_JSON.exists():
        return load_json(OUTPUT_JSON)
    return empty_payload(sources)


def group_key(group: dict[str, Any]) -> str:
    return f"{int(group['dataset_number'])}:{int(group['set'])}"


def normalize_image(stem: str, description: str, source: dict[str, Any]) -> dict[str, Any]:
    image = source["images"][stem]
    return {
        "image_type": stem,
        "filename": image["filename"],
        "source_path": image["url"],
        "description": description.strip(),
    }


def normalize_group(group: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    key = group_key(group)
    if key not in sources:
        raise ValueError(f"Unknown dataset/set group: {key}")

    source = sources[key]
    descriptions_by_stem = {
        image["image_type"]: image["description"]
        for image in group.get("images", [])
    }
    missing = [stem for stem in EXPECTED_IMAGES if stem not in descriptions_by_stem]
    if missing:
        raise ValueError(f"{key} is missing descriptions for: {', '.join(missing)}")

    return {
        "dataset_number": source["dataset_number"],
        "dataset_name": source["dataset_name"],
        "set": source["set"],
        "source_format": source["source_format"],
        "source_dir": source["source_dir"],
        "completedAt": now(),
        "images": [
            normalize_image(stem, descriptions_by_stem[stem], source)
            for stem in EXPECTED_IMAGES
        ],
    }


def refresh_status(payload: dict[str, Any], sources: dict[str, Any]) -> None:
    completed_groups = len(payload["groups"])
    completed_images = sum(len(group.get("images", [])) for group in payload["groups"])
    payload["updatedAt"] = now()
    payload["status"] = {
        "completedGroups": completed_groups,
        "totalGroups": len(sources),
        "completedImages": completed_images,
        "totalImages": len(sources) * len(EXPECTED_IMAGES),
    }


def sort_groups(payload: dict[str, Any], sources: dict[str, Any]) -> None:
    rank = {key: index for index, key in enumerate(ordered_keys(sources))}
    payload["groups"].sort(key=lambda group: rank[group_key(group)])


def add_groups(input_payload: Any) -> None:
    sources = source_data()
    payload = load_payload(sources)
    groups = input_payload if isinstance(input_payload, list) else [input_payload]
    existing = {group_key(group): group for group in payload["groups"]}

    for group in groups:
        normalized = normalize_group(group, sources)
        existing[group_key(normalized)] = normalized

    payload["groups"] = list(existing.values())
    sort_groups(payload, sources)
    refresh_status(payload, sources)
    write_json_atomic(OUTPUT_JSON, payload)
    print_status(payload)


def print_status(payload: dict[str, Any]) -> None:
    status = payload["status"]
    print(
        f"{status['completedGroups']}/{status['totalGroups']} groups, "
        f"{status['completedImages']}/{status['totalImages']} images"
    )


def cmd_init(_args: argparse.Namespace) -> None:
    sources = source_data()
    payload = load_payload(sources)
    sort_groups(payload, sources)
    refresh_status(payload, sources)
    write_json_atomic(OUTPUT_JSON, payload)
    print_status(payload)


def cmd_add(_args: argparse.Namespace) -> None:
    add_groups(json.load(sys.stdin))


def cmd_next(args: argparse.Namespace) -> None:
    sources = source_data()
    payload = load_payload(sources)
    done = {group_key(group) for group in payload["groups"]}
    pending = [key for key in ordered_keys(sources) if key not in done]
    for key in pending[: args.limit]:
      source = sources[key]
      print(f"{source['dataset_number']} set {source['set']} {source['dataset_name']} {source['source_dir']}")


def cmd_validate(_args: argparse.Namespace) -> None:
    sources = source_data()
    payload = load_payload(sources)
    done = {group_key(group): group for group in payload["groups"]}
    errors: list[str] = []

    for key in ordered_keys(sources):
        group = done.get(key)
        if group is None:
            errors.append(f"missing group {key}")
            continue
        stems = [image.get("image_type") for image in group.get("images", [])]
        if stems != EXPECTED_IMAGES:
            errors.append(f"{key} has wrong image order: {stems}")
        for image in group.get("images", []):
            if not str(image.get("description", "")).strip():
                errors.append(f"{key} {image.get('image_type')} has empty description")

    refresh_status(payload, sources)
    write_json_atomic(OUTPUT_JSON, payload)
    print_status(payload)
    if errors:
        for error in errors[:50]:
            print(error, file=sys.stderr)
        if len(errors) > 50:
            print(f"... {len(errors) - 50} more errors", file=sys.stderr)
        raise SystemExit(1)
    print("valid")


def cmd_sheet(args: argparse.Namespace) -> None:
    sources = source_data()
    key = f"{args.dataset}:{args.set}"
    if key not in sources:
        raise SystemExit(f"Unknown dataset/set group: {key}")

    montage = shutil.which("montage")
    if montage is None:
        raise SystemExit("Could not find ImageMagick montage")

    source = sources[key]
    output_dir = Path(args.out).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"dataset_{args.dataset:02d}_set_{args.set}.jpg"
    image_paths = [
        ROOT / "docs" / source["source_dir"] / source["images"][stem]["filename"]
        for stem in EXPECTED_IMAGES
    ]
    command = [
        montage,
        "-font",
        "/System/Library/Fonts/Helvetica.ttc",
        "-pointsize",
        "18",
        "-label",
        "%t",
        *[str(path) for path in image_paths],
        "-thumbnail",
        "180x270",
        "-geometry",
        "180x300+12+12",
        "-tile",
        "4x2",
        str(output),
    ]
    subprocess.run(command, check=True)
    print(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=cmd_init)

    add_parser = subparsers.add_parser("add")
    add_parser.set_defaults(func=cmd_add)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("--limit", type=int, default=10)
    next_parser.set_defaults(func=cmd_next)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.set_defaults(func=cmd_validate)

    sheet_parser = subparsers.add_parser("sheet")
    sheet_parser.add_argument("dataset", type=int)
    sheet_parser.add_argument("set", type=int, choices=(1, 2))
    sheet_parser.add_argument("--out", default="/private/tmp/gurung_desc_sheets")
    sheet_parser.set_defaults(func=cmd_sheet)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
