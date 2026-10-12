"""Place working Praat files in recording folders without replacing files."""

import shutil
from pathlib import Path

from recording_library import file_hash


def praat_targets(vhdr, output_root=None):
    header = Path(vhdr).resolve()
    folder = Path(output_root).resolve() / header.stem if output_root else header.parent
    return {"stimtrak_wav": folder / f"{header.stem}.wav",
            "textgrid": folder / f"{header.stem}_annotations.TextGrid"}


def check_praat_targets(vhdr, output_root=None):
    for path in praat_targets(vhdr, output_root).values():
        if path.exists():
            raise ValueError(f"Praat output already exists: {path}. Nothing was overwritten. Use the existing recording entry or resolve this filename conflict first.")


def place_praat_files(config, reuse_identical=False, output_root=None):
    targets = praat_targets(config["vhdr"], output_root)
    sources = {key: Path(config[key]).resolve() for key in targets}
    hashes = {key: file_hash(path) for key, path in sources.items()}
    for key, target in targets.items():
        if target.exists() and target != sources[key]:
            if not reuse_identical or file_hash(target) != hashes[key]:
                raise ValueError(f"Praat output already exists: {target}. Existing files and annotations were not replaced.")
    for key, target in targets.items():
        if target == sources[key] or target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with sources[key].open("rb") as source, target.open("xb") as output:
            shutil.copyfileobj(source, output)
    for key, target in targets.items():
        if file_hash(target) != hashes[key] or file_hash(sources[key]) != hashes[key]:
            raise ValueError("A Praat file changed while copying. Original files were kept; no new paths were registered.")
    return dict(config, **{key: str(path) for key, path in targets.items()})
