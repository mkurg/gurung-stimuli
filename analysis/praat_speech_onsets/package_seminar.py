"""Package the frozen seminar figures, tables, provenance and reproduction scripts."""

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


FIGURES = (
    "01_sol_distribution.png", "02_sol_by_participant.png", "03_transitive_counts.png",
    "04_progress_and_review.png", "05_sol_by_category.png", "06_eligible_overview.png",
    "07_erg_by_noun.png", "08_erg_by_action.png", "09_erg_by_indefinite_marker.png",
    "10_sol_by_transitive_action.png", "11_sol_by_intransitive_action.png",
    "12_participant_sol_vs_erg_use.png",
)


def figure_names(output):
    path = output / "extended_summary.json"
    extra = json.loads(path.read_text(encoding="utf-8"))["figures"] if path.is_file() else []
    names = [*FIGURES, *extra]
    if len(set(names)) != len(names) or any(Path(name).name != name or not name.endswith(".png") for name in names):
        raise ValueError("Invalid or duplicate figure names")
    return names


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def contact_sheets(paths, output):
    from PIL import Image, ImageDraw, ImageOps
    output.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(paths), 4):
        sheet = Image.new("RGB", (2200, 1500), "#dce2e5")
        draw = ImageDraw.Draw(sheet)
        for slot, path in enumerate(paths[start:start+4]):
            x, y = (slot % 2) * 1100, (slot // 2) * 750
            with Image.open(path) as image:
                thumb = ImageOps.contain(image.convert("RGB"), (1080, 710))
                sheet.paste(thumb, (x + (1100-thumb.width)//2, y + 30 + (710-thumb.height)//2))
            draw.text((x+12, y+10), path.name, fill="#202c33")
        sheet.save(output / f"contact_{start//4+1:02}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--rendered-dir", type=Path, help="Only make QA sheets from already rendered PDF pages")
    args = parser.parse_args()
    output = args.source_dir.resolve()
    figures = figure_names(output)
    if args.rendered_dir:
        paths = sorted(args.rendered_dir.glob("page-*.png"))
        if len(paths) != len(figures):
            raise ValueError(f"Expected {len(figures)} rendered PDF pages, found {len(paths)}")
        contact_sheets(paths, args.rendered_dir)
        return

    from PIL import Image
    from pypdf import PdfReader
    from reportlab.pdfgen import canvas

    for name in figures:
        if not (output / name).is_file():
            raise ValueError(f"Missing seminar figure: {name}")
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    rows = json.loads((output / "all_main_trials.json").read_text(encoding="utf-8"))
    participant_data = json.loads((output / "participant_erg_sol_summary.json").read_text(encoding="utf-8"))
    people = {p["recording"]: p for p in participant_data["participants"]}
    n_people = summary["totals"]["participants"]
    eligible = [r for r in rows if r["eligible"]]
    if len(eligible) != summary["totals"]["eligible"]:
        raise ValueError("Export counts do not match the frozen summary")
    write_csv(output / "eligible_trials.csv", eligible)
    overview = []
    for p in summary["participants"]:
        c = p["eligible_category_counts"]
        tr = people.get(p["recording"], {})
        overview.append({"recording": p["recording"], "eligible": p["eligible"],
                         "Itr": c["Itr"], "Tr ERG": c["Tr ERG"], "Tr zero": c["Tr zero"],
                         "unsuitable": p["unsuitable"], "pending": p["pending_not_unsuitable"],
                         "need_help_all": p["need_help_all_main"], "need_help_eligible": p["need_help_eligible"],
                         "mean_sol_ms": p["sol"]["mean_ms"], "median_sol_ms": p["sol"]["median_ms"],
                         "transitive_erg_percent": tr.get("erg_percent"),
                         "mean_transitive_sol_ms": tr.get("transitive_mean_sol_ms")})
    write_csv(output / "participant_overview.csv", overview)
    timing = []
    counts = summary["totals"]["eligible_category_counts"]
    total_tr = counts["Tr ERG"] + counts["Tr zero"]
    for cutoff in summary["timing_cutoffs"]:
        c = cutoff["category_counts"]
        retained_tr = c["Tr ERG"] + c["Tr zero"]
        timing.append({"minimum_sol_ms": cutoff["cutoff_ms"], "all_retained": cutoff["retained"],
                       "Itr": c["Itr"], "Tr ERG": c["Tr ERG"], "Tr zero": c["Tr zero"],
                       "transitive_retained": retained_tr, "transitive_lost": total_tr-retained_tr,
                       "transitive_lost_percent": 100*(total_tr-retained_tr)/total_tr})
    write_csv(output / "timing_retention.csv", timing)

    reports = ["SEMINAR_REPORT.md", "ERGATIVE_ASSOCIATIONS.md", "ACTION_SOL_REPORT.md", "PARTICIPANT_ERG_SOL.md"]
    if (output / "EXTENDED_REPORT.md").is_file():
        reports.append("EXTENDED_REPORT.md")
    (output / "FULL_REPORT.md").write_text("\n\n---\n\n".join(
        (output / name).read_text(encoding="utf-8") for name in reports), encoding="utf-8")

    pdf_dir = output / "output" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"lab_seminar_{n_people}_participants.pdf"
    pdf = canvas.Canvas(str(pdf_path))
    pdf.setTitle(f"Gurung speech production: {n_people}-participant descriptive figures")
    pdf.setAuthor("Descriptive statistics from saved Praat annotations")
    for name in figures:
        with Image.open(output / name) as image:
            width, height = (dimension * 72 / 220 for dimension in image.size)
        pdf.setPageSize((width, height))
        pdf.drawImage(str(output / name), 0, 0, width=width, height=height)
        pdf.showPage()
    pdf.save()
    if len(PdfReader(pdf_path).pages) != len(figures):
        raise ValueError("Wrong PDF page count")

    repro = output / "reproducibility"
    repro.mkdir(exist_ok=True)
    root = Path(__file__).parent
    scripts = ["seminar_stats.py", "ergative_associations.py", "ergative_codebook.json",
               "action_sol_stats.py", "participant_erg_sol.py", "package_seminar.py",
               "test_seminar_stats.py", "test_ergative_associations.py", "test_action_sol_stats.py", "test_participant_erg_sol.py"]
    if (output / "extended_summary.json").is_file():
        scripts.extend(["extended_descriptives.py", "test_extended_descriptives.py"])
    for name in scripts:
        shutil.copy2(root / name, repro / name)
    conditions = repro / "condition_tables"
    conditions.mkdir(exist_ok=True)
    for source in json.loads((output / "condition_sources.json").read_text(encoding="utf-8")):
        path = Path(source["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Condition source changed after collection")
        shutil.copy2(path, conditions / path.name)
    readme = f"""# Seminar Summary: {n_people} Participants

Frozen saved-data snapshot: {summary['generated_at_utc']}.

Open output/pdf/lab_seminar_{n_people}_participants.pdf for all {len(figures)} figures.
FULL_REPORT.md contains all counts, definitions, tables and interpretation notes.
Individual high-resolution PNGs are alongside this file. CSV tables use UTF-8 with BOM.

Eligible = main trial + saved nonblank transcription + exactly one valid onset + not Unsuitable.
Need help is included. No SOL cutoff, participant exclusion, outlier trimming or EEG artifact rejection.
SOL = saved acoustic onset minus EEG S200. ERG is the manual flag; not marked ERG is not independently verified absence.
Noun and indefinite-marker coding is provisional; inspect trial_linguistic_coding.csv.

## Reproduce From This Snapshot

Requires Python with numpy, scipy, matplotlib, pillow, reportlab, pypdf and tzdata.
Run from this extracted bundle; use a new output directory:

```powershell
python reproducibility/seminar_stats.py --snapshot source_snapshot.json{" --participant-ages participant_ages.json" if (output / "participant_ages.json").is_file() else ""} --output-dir regenerated
python reproducibility/ergative_associations.py --snapshot regenerated/source_snapshot.json --codebook reproducibility/ergative_codebook.json --condition-table-dir reproducibility/condition_tables --output-dir regenerated
python reproducibility/action_sol_stats.py --source-dir regenerated
python reproducibility/participant_erg_sol.py --source-dir regenerated
{"python reproducibility/extended_descriptives.py --source-dir regenerated" if len(figures) > len(FIGURES) else ""}
python reproducibility/package_seminar.py --source-dir regenerated
```

To collect newer saved data on the original computer, omit --snapshot in the first command and add --expected-participants {n_people}.
The interface must be running for a new collection; frozen-snapshot reproduction does not need it.
Run the included test modules from the reproducibility directory with python -m unittest.
MANIFEST.json records SHA-256 hashes of included files. Original EEG, audio and working annotations were not changed.
The bundle contains participant transcriptions and decisions, but no raw audio/EEG.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    archive = output / f"lab_seminar_{n_people}_participants.zip"
    included = [p for p in output.rglob("*") if p.is_file() and p != archive
                and p.name != "MANIFEST.json" and "__pycache__" not in p.parts and "tmp" not in p.relative_to(output).parts]
    manifest = {"snapshot_at_utc": summary["generated_at_utc"], "figure_count": len(figures),
                "participants": n_people, "sha256": {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                                       for p in sorted(included)}}
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(included) + [output / "MANIFEST.json"]:
            handle.write(path, path.relative_to(output))
    with zipfile.ZipFile(archive) as handle:
        if handle.testzip() is not None:
            raise ValueError("Bundle ZIP failed integrity check")
    print(json.dumps({"pdf": str(pdf_path), "pdf_pages": len(figures), "archive": str(archive),
                      "files": len(included)+1, "transitive_timing_retention": timing}, indent=2), flush=True)


if __name__ == "__main__":
    main()
