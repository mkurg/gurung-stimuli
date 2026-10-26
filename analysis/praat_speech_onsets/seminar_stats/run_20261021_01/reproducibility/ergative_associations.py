"""Describe ERG flags by noun, picture action and subject indefinite marking."""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

from seminar_stats import INK, MUTED, TRANSITIVE_COUNT_COLORS, summarize, trial_rows

INDEFINITE = "Indefinite marker"
UNMARKED = "No indefinite marker"
UNRESOLVED = "Unresolved subject"
UNRESOLVED_NOUN = "Unresolved noun"


def normalize(text):
    return unicodedata.normalize("NFC", text.replace("\u02dce", "\u1ebd"))


def canonical_noun(word, codebook):
    visited = set()
    while word in codebook["noun_aliases"]:
        if word in visited:
            raise ValueError(f"Cyclic noun alias: {word}")
        visited.add(word)
        word = codebook["noun_aliases"][word]
    return word


def strip_case(token, codebook):
    endings = "|".join(re.escape(s) for s in codebook["noun_case_suffixes"])
    match = re.fullmatch(rf"(.+?)-({endings})(\(\?\))?", token)
    return (match[1], match[2], bool(match[3]) or match[2] == "?") if match else (token, "", False)


def subject_coding(text, codebook):
    tokens = normalize(text).split()
    prefixes = set(codebook["initial_tokens_to_skip"])
    indefinite_word = codebook["indefinite_word"]
    index, evidence, notes = 0, [], []
    while index < len(tokens):
        base, suffix, uncertain = strip_case(tokens[index], codebook)
        if base == indefinite_word:
            evidence.append(tokens[index])
            if uncertain:
                notes.append("uncertain_case_on_kri")
        elif tokens[index] not in prefixes:
            break
        index += 1
    if index == len(tokens):
        return dict(subject_head_raw="", noun_group=UNRESOLVED_NOUN,
                    indefiniteness=UNRESOLVED, indefinite_evidence="", case_suffix="",
                    coding_notes=["no_initial_noun_candidate"])

    head = tokens[index]
    stem, suffix, uncertain = strip_case(head, codebook)
    ending = codebook["indefinite_noun_ending"]
    attached_marker = stem.endswith(ending)
    if attached_marker:
        evidence.append(head)
        stem = stem[:-len(ending)]
    recognized = stem in codebook["noun_inventory"]
    if not recognized:
        notes.append("unrecognized_noun_after_ri_removal" if attached_marker else "unrecognized_initial_head")
    if uncertain:
        notes.append("uncertain_case_on_head")
    if index + 1 < len(tokens):
        base, marker_case, marker_uncertain = strip_case(tokens[index + 1], codebook)
        if base == indefinite_word:
            evidence.append(tokens[index + 1])
            if marker_uncertain:
                notes.append("uncertain_case_on_kri")

    # Only the initial subject phrase supplies indefinite evidence; later kri is not borrowed.
    status = INDEFINITE if evidence else (UNMARKED if recognized else UNRESOLVED)
    return dict(subject_head_raw=head,
                noun_group=canonical_noun(stem, codebook) if recognized else UNRESOLVED_NOUN,
                indefiniteness=status, indefinite_evidence="; ".join(evidence),
                case_suffix=suffix, coding_notes=notes)


def condition_table(text):
    result = {}
    for row in csv.DictReader(text.splitlines()):
        item = int(row["item_trigger"])
        if item in result:
            raise ValueError(f"Duplicate condition-table item: {item}")
        result[item] = row
    return result


def load_condition_tables(snapshot, table_directory=None):
    tables, sources, seen_lists = {}, [], {}
    for bundle in snapshot["bundles"]:
        session = bundle["session"]
        list_number = int(session["list"])
        name = f"isolated_main_list{list_number}_all_120.csv"
        matches = [s for s in session["sources"] if PureWindowsPath(s["path"]).name == name]
        if len(matches) != 1:
            raise ValueError(f"{session['recording']}: expected one source for {name}")
        source = matches[0]
        if list_number in tables:
            if seen_lists[list_number] != source["sha256"]:
                raise ValueError(f"List {list_number} has inconsistent source hashes.")
            continue
        path = table_directory / name if table_directory else Path(source["path"])
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if sha != source["sha256"]:
            raise ValueError(f"Condition table changed since snapshot: {path}")
        seen_lists[list_number] = sha
        text = content.decode("utf-8-sig")
        tables[list_number] = condition_table(text)
        sources.append({"experiment_list": list_number, "path": str(path), "sha256": sha,
                        "rows": list(tables[list_number].values())})
    return tables, sources


def code_rows(rows, snapshot, codebook, tables):
    trial_index = {(b["session"]["session_id"], t["id"]): t
                   for b in snapshot["bundles"] for t in b["session"]["trials"]}
    result = []
    for row in rows:
        if not row["eligible"] or row["category"] == "Itr":
            continue
        trial = trial_index[(row["session_id"], row["trial_id"])]
        condition = tables[int(row["experiment_list"])][int(row["item_trigger"])]
        if (condition["condition_id"] != row["condition"] or condition["transitivity"] != "transitive"
                or int(condition["dataset_number"]) != trial["image_set"]
                or int(condition["stimulus_set"]) != trial["stimulus_set"]
                or Path(condition["target_image"]).name != trial["image_filename"]):
            raise ValueError(f"Picture/condition mismatch: {row['recording']} {row['trial_id']}")
        label = condition["dataset_label"]
        if label.replace("_", " ") != trial["scene"]:
            raise ValueError(f"Scene-label mismatch: {row['recording']} {row['trial_id']}")
        action = label.split("_", 1)[1].replace("_", " ")
        coding = subject_coding(row["transcription"], codebook)
        erg = row["category"] == "Tr ERG"
        if coding["case_suffix"] in {"i", "yi", "ye"} and not erg:
            coding["coding_notes"].append("visible_case_ending_but_not_flagged_erg")
        if row["need_help"]:
            coding["coding_notes"].append("need_help_flag_kept_in_analysis")
        result.append({**row, **coding, "ergative": erg, "picture_action": action,
                       "picture_verb": action.split()[0], "dataset_label": label,
                       "image_set": trial["image_set"], "image_filename": trial["image_filename"],
                       "coding_method": "initial_subject_phrase_rule_v1"})
    return result


def rate(rows):
    n = len(rows)
    erg = sum(r["ergative"] for r in rows)
    return {"n": n, "erg": erg, "zero": n - erg, "erg_percent": 100 * erg / n if n else None,
            "participants": len({r["recording"] for r in rows}),
            "recordings": sorted({r["recording"] for r in rows}),
            "need_help": sum(r["need_help"] for r in rows)}


def group_counts(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return [{"group": group, **rate(values)} for group, values in sorted(groups.items())]


def association_summary(rows, snapshot, codebook):
    keys = ("noun_group", "picture_action", "picture_verb", "indefiniteness")
    result = {"snapshot_at_utc": snapshot["generated_at_utc"], "totals": rate(rows),
              "groups": {key: group_counts(rows, key) for key in keys},
              "minimum_noun_trials_in_figure": codebook["minimum_noun_trials_in_figure"]}
    result["by_participant_indefiniteness"] = {
        recording: {key: rate([r for r in rows if r["recording"] == recording and r["indefiniteness"] == key])
                    for key in (INDEFINITE, UNMARKED, UNRESOLVED)}
        for recording in sorted({r["recording"] for r in rows})}
    result["coding_note_counts"] = dict(Counter(note for row in rows for note in row["coding_notes"]))
    for key in keys:
        groups = result["groups"][key]
        if sum(g["n"] for g in groups) != len(rows) or sum(g["erg"] for g in groups) != result["totals"]["erg"]:
            raise ValueError(f"Group-count reconciliation failed: {key}")
    return result


def make_figures(summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    blue = TRANSITIVE_COUNT_COLORS["Tr ERG"]
    orange = TRANSITIVE_COUNT_COLORS["Tr zero"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": INK,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False,
                         "axes.axisbelow": True})
    total = summary["totals"]
    overall = total["erg_percent"]
    footer = "Eligible transitive responses; Unsuitable excluded; Need help included. ERG = manual flag; \u2205 = not marked ERG."
    footer2 = "Pooled descriptive rates, not adjusted for participant or picture. Noun/indefinite coding is provisional."
    figures = []

    def decorate(fig, title, subtitle, extra=""):
        fig.patch.set_facecolor("white")
        fig.text(.06, .95, title, fontsize=25, fontweight="bold", va="top")
        fig.text(.06, .905, subtitle, fontsize=12, color=MUTED, va="top")
        fig.text(.06, .04, footer + "\n" + footer2 + ("\n" + extra if extra else ""),
                 fontsize=10, color=MUTED, linespacing=1.5, va="bottom")

    def finish(fig, name):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        width, height = fig.canvas.get_width_height()
        from matplotlib.text import Text
        for text in fig.findobj(Text):
            if not text.get_visible() or not text.get_text():
                continue
            box = text.get_window_extent(renderer)
            if box.x0 < -1 or box.x1 > width + 1 or box.y0 < -1 or box.y1 > height + 1:
                raise ValueError(f"Clipped label in {name}: {text.get_text()}")
        fig.savefig(output / name, dpi=220, facecolor="white")
        plt.close(fig)
        figures.append(name)

    def bars(ax, groups, row_font=12):
        ys = list(range(len(groups)))
        percentages = [g["erg_percent"] for g in groups]
        ax.barh(ys, percentages, color=blue, height=.61, label="Tr ERG")
        ax.barh(ys, [100 - x for x in percentages], left=percentages, color=orange, height=.61, label="Tr \u2205", alpha=.30)
        for y, g in zip(ys, groups):
            if g["erg_percent"] >= 13:
                ax.text(g["erg_percent"] / 2, y, f"{g['erg_percent']:.0f}%", color="white", va="center", ha="center", fontsize=row_font)
            else:
                ax.text(g["erg_percent"] + 2, y, f"{g['erg_percent']:.0f}%", color=INK, va="center", fontsize=row_font)
            ax.text(105, y, f"{g['erg']}/{g['n']}   ({g['participants']})", fontsize=row_font, va="center", clip_on=False)
        ax.set_yticks(ys, [g["group"] for g in groups], fontsize=row_font)
        ax.set(xlim=(0, 100), ylim=(len(groups) - .5, -.5), xlabel="Responses marked ERG (%)")
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.grid(axis="x", color="#e7edef", lw=.8)
        ax.tick_params(length=0, pad=8)
        ax.axvline(overall, color=INK, linewidth=1.4, linestyle=(0, (3, 3)))
        ax.text(105, -.95, "ERG / n  (people)", fontsize=10, color=MUTED, clip_on=False)

    def legend(fig):
        from matplotlib.lines import Line2D
        fig.legend(handles=[Patch(facecolor=blue, label="Tr ERG"),
                            Patch(facecolor=orange, alpha=.30, label="Tr \u2205"),
                            Line2D([0], [0], color=INK, ls="--", label=f"Overall {overall:.1f}%")],
                   loc="upper left", bbox_to_anchor=(.055, .86), ncol=3, frameon=False, fontsize=12)

    threshold = summary["minimum_noun_trials_in_figure"]
    nouns = [g for g in summary["groups"]["noun_group"] if g["n"] >= threshold and g["group"] != UNRESOLVED_NOUN]
    nouns.sort(key=lambda g: (-g["erg_percent"], -g["n"], g["group"]))
    shown = sum(g["n"] for g in nouns)
    fig = plt.figure(figsize=(14, max(8.4, 3.9 + .39 * len(nouns))))
    ax = fig.add_axes([.18, .20, .66, .60])
    bars(ax, nouns)
    legend(fig)
    decorate(fig, "ERG marking by subject noun", f"{total['n']} eligible transitive responses; {shown} shown in noun groups with at least {threshold} trials",
             f"Case endings and indefinite endings grouped with the noun. Remaining {total['n'] - shown} trials are listed in the full table.")
    finish(fig, "07_erg_by_noun.png")

    actions = sorted(summary["groups"]["picture_action"], key=lambda g: (-g["erg_percent"], -g["n"], g["group"]))
    middle = (len(actions) + 1) // 2
    fig = plt.figure(figsize=(17, 10))
    left = fig.add_axes([.135, .195, .27, .60])
    right = fig.add_axes([.645, .195, .27, .60])
    bars(left, actions[:middle], row_font=12)
    bars(right, actions[middle:], row_font=12)
    legend(fig)
    decorate(fig, "ERG marking by picture-elicited action", f"All {len(actions)} transitive actions; {total['n']} eligible responses; same participant cohort as the other seminar figures",
             "Action labels come from the condition tables, not from the final word of the transcription.")
    finish(fig, "08_erg_by_action.png")

    by_status = {g["group"]: g for g in summary["groups"]["indefiniteness"]}
    groups = [by_status[k] for k in (INDEFINITE, UNMARKED) if k in by_status]
    fig = plt.figure(figsize=(15, 8.4))
    pooled = fig.add_axes([.20, .32, .34, .36])
    bars(pooled, groups, row_font=12)
    detail = fig.add_axes([.80, .24, .17, .52])
    recordings = sorted(summary["by_participant_indefiniteness"])
    for y, rec in enumerate(recordings):
        entries = summary["by_participant_indefiniteness"][rec]
        a, b = entries[INDEFINITE], entries[UNMARKED]
        if a["n"] and b["n"]:
            detail.plot([a["erg_percent"], b["erg_percent"]], [y, y], color="#c1cbcf", lw=1.5, zorder=1)
        for shift, entry, color in ((-.11, a, blue), (.11, b, "#bd550c")):
            if entry["n"]:
                detail.scatter(entry["erg_percent"], y + shift, s=50, color=color, edgecolors="white", lw=.6, zorder=3)
    participant_labels = [f"{rec} ({summary['by_participant_indefiniteness'][rec][INDEFINITE]['n']}/"
                          f"{summary['by_participant_indefiniteness'][rec][UNMARKED]['n']})" for rec in recordings]
    detail.set_yticks(range(len(recordings)), participant_labels, fontsize=10)
    detail.set(xlim=(-5, 105), ylim=(len(recordings) - .5, -.5), xlabel="ERG (%)")
    detail.set_xticks([0, 50, 100])
    detail.tick_params(length=0, pad=6)
    detail.grid(axis="x", color="#e7edef", lw=.8)
    detail.set_title("Within each participant", fontsize=13, loc="right", pad=22)
    from matplotlib.lines import Line2D
    detail.legend(handles=[Line2D([0], [0], marker="o", color=blue, ls="", label=INDEFINITE),
                           Line2D([0], [0], marker="o", color="#bd550c", ls="", label=UNMARKED)],
                  loc="lower left", bbox_to_anchor=(-.23, -.22), frameon=False, fontsize=10)
    fig.text(.20, .755, "Pooled responses", fontsize=14)
    legend(fig)
    unclassified = by_status.get(UNRESOLVED, {}).get("n", 0)
    decorate(fig, "ERG and subject indefinite marking", f"Subject kri or noun-final -ri versus no indefinite marker; {sum(g['n'] for g in groups)} classified / {total['n']} eligible responses",
             f"No indefinite marker does not establish definiteness. {unclassified} unresolved subject(s) excluded. Participant labels: n with / n without marker.")
    finish(fig, "09_erg_by_indefinite_marker.png")
    return figures


def markdown_report(summary, codebook, rows, figures):
    total = summary["totals"]
    lines = ["# ERG Associations: Descriptive Seminar Figures", "",
             f"Frozen snapshot: {summary['snapshot_at_utc']}. {total['n']} eligible transitive trials "
             f"({total['erg']} marked ERG, {total['zero']} not marked ERG), {total['participants']} participants.", "",
             "## Interpretation", "", "Percentages are observed, pooled ERG-flag rates, not adjusted probabilities or causal effects. "
             "Participant, picture/action, noun and indefinite marking are not balanced. No significance test is applied. "
             "The within-participant panel makes some of this imbalance visible; it is not a fitted model.", "",
             "Main trials only. Saved nonblank transcription and one valid onset required; Unsuitable excluded; Need help included. "
             "No SOL cutoff or participant exclusion. ERG is the manual viewer flag. Unmarked includes missing saved ERG decisions; "
             "spelling is never used to override the outcome.", "", "## Coding", "",
             "The initial nominal following an optional initial demonstrative sequence and/or kri is the candidate subject head. "
             "This positional rule has been checked against the token inventory, but is not a validated Gurung grammatical parser. "
             "Interpret noun and indefinite comparisons as provisional until the per-trial coding is checked.", "",
             "Indefinite evidence is kri immediately before/after that head, or a noun ending in ri, following the user's rule. "
             "Later kri in an object phrase is ignored. A question mark after kri marks uncertain case, not uncertain recognition of kri. "
             "Absence of either marker is called **no indefinite marker**, never definite.", "",
             "Visible hyphenated -i, -yi, -ye, or -? are removed for noun grouping only. "
             "Indefinite -ri is removed before matching aliases. Confirmed indefinite variants are grouped with the noun. "
             "Unconfirmed diacritic/compound differences remain separate. Full mapping is in the codebook.", "",
             "The literal ri rule also catches **misteri** (081i main-028); its lexical interpretation needs checking. "
             "It is provisionally included in the indefinite category but its noun group is unresolved. "
             "091i main-075 (`tsu mla...`) lacks a recognized initial subject noun and is unresolved in both analyses.", "",
             "Picture action is the transitive part of dataset_label, matched by list/item code and checked against condition, "
             "image set, stimulus set, target filename and scene. Both original condition-table hashes match the frozen snapshot.", "",
             "## Noun Mapping", "", "| Input form after ending removal | Group |", "|---|---|"]
    lines.extend(f"| {a} | {b} |" for a, b in codebook["noun_aliases"].items())
    for key, title in (("noun_group", "Subject Nouns"), ("picture_action", "Picture Actions"), ("indefiniteness", "Subject Indefinite Marking")):
        lines += ["", "## " + title, "", "| Group | Tr ERG | Tr \u2205 | Total n | ERG (%) | Participants | Need help |", "|---|---:|---:|---:|---:|---:|---:|"]
        groups = sorted(summary["groups"][key], key=lambda g: (-g["erg_percent"], -g["n"], g["group"]))
        for g in groups:
            lines.append(f"| {g['group']} | {g['erg']} | {g['zero']} | {g['n']} | {g['erg_percent']:.1f} | {g['participants']} | {g['need_help']} |")
    lines += ["", "## Indefinite Marking Within Participants", "",
              "| Participant | ERG / n, indefinite | ERG (%) | ERG / n, no marker | ERG (%) |", "|---|---:|---:|---:|---:|"]
    for rec, entries in summary["by_participant_indefiniteness"].items():
        a, b = entries[INDEFINITE], entries[UNMARKED]
        ar = f"{a['erg_percent']:.1f}" if a["n"] else "n.a."
        br = f"{b['erg_percent']:.1f}" if b["n"] else "n.a."
        lines.append(f"| {rec} | {a['erg']}/{a['n']} | {ar} | {b['erg']}/{b['n']} | {br} |")
    lines += ["", "## Coding Checks", "", "| Note | Trials |", "|---|---:|"]
    lines.extend(f"| {key} | {value} |" for key, value in summary["coding_note_counts"].items())
    lines += ["", "Case-ending/flag discrepancies are retained, not silently corrected. "
              "Need help does not exclude a trial. Trial-level notes and original transcription are in trial_linguistic_coding.csv.",
              "", "## Reproduction", "", "Run ergative_associations.py with --snapshot, --codebook and --output-dir. "
              "On another device, pass --condition-table-dir containing the same condition CSVs. "
              "The script verifies their hashes and rejects mismatches, duplicate keys and unmatched trials. "
              "Condition-table contents are also saved in condition_sources.json. Original annotations/decisions are not edited.", "",
              "## Figures", ""]
    lines.extend(f"![{name}]({name})" for name in figures)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, default=Path(__file__).with_name("ergative_codebook.json"))
    parser.add_argument("--condition-table-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    all_rows = trial_rows(snapshot)
    original_summary = summarize(all_rows, snapshot)
    tables, sources = load_condition_tables(snapshot, args.condition_table_dir)
    rows = code_rows(all_rows, snapshot, codebook, tables)
    summary = association_summary(rows, snapshot, codebook)
    expected = original_summary["totals"]["eligible_category_counts"]
    if summary["totals"]["erg"] != expected["Tr ERG"] or summary["totals"]["zero"] != expected["Tr zero"]:
        raise ValueError("Transitive totals changed from the original seminar cohort.")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name, data in (("ergative_summary.json", summary), ("linguistic_codebook.json", codebook),
                       ("condition_sources.json", sources), ("trial_linguistic_coding.json", rows)):
        (output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (output / "trial_linguistic_coding.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({**r, "coding_notes": "; ".join(r["coding_notes"])} for r in rows)
    figures = make_figures(summary, output)
    (output / "ERGATIVE_ASSOCIATIONS.md").write_text(markdown_report(summary, codebook, rows, figures), encoding="utf-8")
    manifest = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "snapshot_sha256": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "codebook_sha256": hashlib.sha256(args.codebook.read_bytes()).hexdigest(),
                "condition_sources": [{k: s[k] for k in ("experiment_list", "path", "sha256")} for s in sources],
                "figure_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in figures}}
    (output / "ergative_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["totals"], indent=2), flush=True)
    print("Figures: " + ", ".join(figures), flush=True)


if __name__ == "__main__":
    main()
