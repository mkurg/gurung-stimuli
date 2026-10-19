"""Describe speech-onset latencies by picture-elicited action."""

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from seminar_stats import INK, MUTED, latency_summary, summarize, trial_rows


def action_rows(snapshot, condition_sources):
    all_rows = trial_rows(snapshot)
    cohort = summarize(all_rows, snapshot)
    tables = {}
    for source in condition_sources:
        table = {}
        for entry in source["rows"]:
            item = int(entry["item_trigger"])
            if item in table:
                raise ValueError(f"Duplicate condition-table item: {item}")
            table[item] = entry
        list_number = int(source["experiment_list"])
        if list_number in tables:
            raise ValueError(f"Duplicate experiment list: {list_number}")
        tables[list_number] = table
    index = {(b["session"]["session_id"], t["id"]): t
             for b in snapshot["bundles"] for t in b["session"]["trials"]}
    result = []
    for row in all_rows:
        if not row["eligible"]:
            continue
        trial = index[(row["session_id"], row["trial_id"])]
        entry = tables[int(row["experiment_list"])][int(row["item_trigger"])]
        if (entry["condition_id"] != row["condition"]
                or int(entry["dataset_number"]) != trial["image_set"]
                or int(entry["stimulus_set"]) != trial["stimulus_set"]
                or entry["dataset_label"].replace("_", " ") != trial["scene"]):
            raise ValueError(f"Condition/picture mismatch: {row['recording']} {row['trial_id']}")
        kind = "intransitive" if row["category"] == "Itr" else "transitive"
        if entry["transitivity"] != kind:
            raise ValueError(f"Transitivity mismatch: {row['recording']} {row['trial_id']}")
        it_action, tr_action = entry["dataset_label"].split("_", 1)
        action = (it_action if kind == "intransitive" else tr_action).replace("_", " ")
        result.append({**row, "transitivity": kind, "picture_action": action})
    if len(result) != cohort["totals"]["eligible"]:
        raise ValueError("Action rows do not reconcile to the eligible cohort.")
    return result


def group_summary(rows):
    if not rows:
        raise ValueError("No eligible responses to summarize.")
    participant_values = defaultdict(list)
    for row in rows:
        participant_values[(row["transitivity"], row["recording"])].append(row["sol_ms"])
    participant_means = {key: statistics.mean(values) for key, values in participant_values.items()}
    result = {}
    for kind in sorted({r["transitivity"] for r in rows}):
        selected = [r for r in rows if r["transitivity"] == kind]
        overall = latency_summary([r["sol_ms"] for r in selected])
        groups = defaultdict(list)
        for row in selected:
            groups[row["picture_action"]].append(row)
        summaries = []
        for action, values in groups.items():
            centered = [r["sol_ms"] - participant_means[(kind, r["recording"])] for r in values]
            summaries.append({"action": action, **latency_summary([r["sol_ms"] for r in values]),
                              "participants": len({r["recording"] for r in values}),
                              "recordings": sorted({r["recording"] for r in values}),
                              "need_help": sum(r["need_help"] for r in values),
                              "tr_erg": sum(r["category"] == "Tr ERG" for r in values),
                              "participant_centered_mean_ms": overall["mean_ms"] + statistics.mean(centered)})
        summaries.sort(key=lambda g: (g["mean_ms"], g["action"]))
        if sum(g["n"] for g in summaries) != len(selected):
            raise ValueError("Action totals do not reconcile.")
        fastest, slowest = summaries[0]["action"], summaries[-1]["action"]
        paired = []
        for rec in sorted({r["recording"] for r in selected}):
            fast = [r["sol_ms"] for r in groups[fastest] if r["recording"] == rec]
            slow = [r["sol_ms"] for r in groups[slowest] if r["recording"] == rec]
            if fast and slow:
                paired.append({"recording": rec, "fast_n": len(fast), "slow_n": len(slow),
                               "fast_mean_ms": statistics.mean(fast), "slow_mean_ms": statistics.mean(slow),
                               "slow_minus_fast_ms": statistics.mean(slow) - statistics.mean(fast)})
        result[kind] = {"overall": overall, "groups": summaries,
                        "participant_means_ms": {rec: mean for (k, rec), mean in participant_means.items() if k == kind},
                        "posthoc_extreme_comparison": {"fastest_action": fastest, "slowest_action": slowest,
                                                       "paired_participants": len(paired),
                                                       "slower_action_longer_count": sum(r["slow_minus_fast_ms"] > 0 for r in paired),
                                                       "participants": paired}}
    return result


def make_figures(summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.text import Text

    blue, orange = "#0072b2", "#d55e00"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": INK,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False})
    names = []
    for kind, data in summary.items():
        groups = data["groups"]
        maximum = math.ceil(max(g["q3_ms"] for g in groups) / 250) * 250
        if kind == "transitive":
            fig = plt.figure(figsize=(17, 10))
            axes = [fig.add_axes([.135, .20, .245, .59]), fig.add_axes([.645, .20, .245, .59])]
            middle = (len(groups) + 1) // 2
            parts = [groups[:middle], groups[middle:]]
            name = "10_sol_by_transitive_action.png"
        else:
            fig = plt.figure(figsize=(14, 8.8))
            axes = [fig.add_axes([.145, .20, .67, .59])]
            parts = [groups]
            name = "11_sol_by_intransitive_action.png"
        for ax, part in zip(axes, parts):
            positions = list(range(len(part)))
            ax.hlines(positions, [g["q1_ms"] for g in part], [g["q3_ms"] for g in part], color="#c1cbd0", linewidth=6, zorder=1)
            ax.scatter([g["mean_ms"] for g in part], positions, s=62, color=blue, zorder=3, edgecolors="white", linewidths=.7)
            ax.scatter([g["median_ms"] for g in part], positions, s=43, color=orange, marker="D", zorder=4, edgecolors="white", linewidths=.7)
            ax.axvline(data["overall"]["mean_ms"], color=INK, linestyle="--", linewidth=1.1, zorder=0)
            for y, g in zip(positions, part):
                ax.text(maximum + 70, y, f"{g['mean_ms']:,.0f}   {g['n']} ({g['participants']})", fontsize=11, va="center", clip_on=False)
            ax.text(maximum + 70, -.95, "Mean ms   n (people)", color=MUTED, fontsize=10, clip_on=False)
            ax.set_yticks(positions, [g["action"] for g in part], fontsize=12)
            ax.set(xlim=(500, maximum), ylim=(len(part) - .5, -.5), xlabel="Speech-onset latency from S200 (ms)")
            ax.set_xticks([x for x in (500, 1000, 1500, 2000, 2500) if x <= maximum])
            ax.tick_params(length=0, pad=8)
            ax.grid(axis="x", color="#e7edef", linewidth=.8, zorder=0)
        fig.text(.06, .95, "Speech onset by " + kind + " action", fontsize=25, fontweight="bold", va="top")
        people = len(data["participant_means_ms"])
        fig.text(.06, .905, f"{data['overall']['n']} eligible responses; {people} contributing participants; {len(groups)} picture-elicited actions", fontsize=12, color=MUTED, va="top")
        fig.legend(handles=[Line2D([0], [0], ls="", marker="o", color=blue, label="Mean"),
                            Line2D([0], [0], ls="", marker="D", color=orange, label="Median"),
                            Line2D([0], [0], color="#c1cbd0", linewidth=6, label="Middle 50% of trials"),
                            Line2D([0], [0], color=INK, ls="--", label=f"Overall mean {data['overall']['mean_ms']:,.0f} ms")],
                   loc="upper left", bbox_to_anchor=(.055, .86), ncol=4, frameon=False, fontsize=12)
        fig.text(.06, .055, "Unsuitable excluded; saved transcription and one valid onset required; Need help included. No SOL cutoff.\n"
                 "Descriptive pooled trials, not adjusted for participant, ERG, picture or trial order. Grey ranges are not confidence intervals.",
                 fontsize=10, color=MUTED, linespacing=1.5, va="bottom")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        width, height = fig.canvas.get_width_height()
        for text in fig.findobj(Text):
            if text.get_visible() and text.get_text():
                box = text.get_window_extent(renderer)
                if box.x0 < -1 or box.x1 > width + 1 or box.y0 < -1 or box.y1 > height + 1:
                    raise ValueError(f"Clipped label in {name}: {text.get_text()}")
        fig.savefig(output / name, dpi=220, facecolor="white")
        plt.close(fig)
        names.append(name)
    return names


def report(summary, timestamp, figures):
    lines = ["# Speech Onset by Picture-Elicited Action", "", "Frozen cohort: " + timestamp + ".", "",
             "SOL = saved acoustic speech onset minus S200. Eligible main trials only; Unsuitable excluded; "
             "transcription and one valid onset required; Need help included. All contributing participants included; no timing exclusions.", "",
             "Actions describe the pictures, not a guaranteed spoken verb. Pooled means/medians are descriptive. "
             "Picture, participant, ERG marking, noun choice and trial order can differ across actions. "
             "Only one or two eligible examples of an action usually remain per person. "
             "No causal claim, significance test or normality assumption is made.", "",
             "Participant-centering subtracts each participant's mean within transitivity, averages these residuals per action, "
             "then adds the pooled transitivity mean. This is a descriptive check, not a fully adjusted model or independent effect estimate. "
             "Extreme-action contrasts below were selected after inspecting the means and are not confirmatory comparisons."]
    for kind, data in summary.items():
        lines += ["", "## " + kind.title(), "", "| Action | n | People | Mean ms | Median ms | Q1 ms | Q3 ms | Participant-centered mean ms |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for g in data["groups"]:
            lines.append(f"| {g['action']} | {g['n']} | {g['participants']} | {g['mean_ms']:.1f} | {g['median_ms']:.1f} | "
                         f"{g['q1_ms']:.1f} | {g['q3_ms']:.1f} | {g['participant_centered_mean_ms']:.1f} |")
        p = data["posthoc_extreme_comparison"]
        lines += ["", f"In {p['slower_action_longer_count']}/{p['paired_participants']} participants with usable responses for both "
                  f"{p['fastest_action']} and {p['slowest_action']}, the participant's mean was longer for {p['slowest_action']}."]
    lines += ["", "## Figures", ""] + [f"![{name}]({name})" for name in figures]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    snapshot_path = source / "source_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    conditions = json.loads((source / "condition_sources.json").read_text(encoding="utf-8"))
    rows = action_rows(snapshot, conditions)
    summary = group_summary(rows)
    output = (args.output_dir or source).resolve()
    output.mkdir(parents=True, exist_ok=True)
    figures = make_figures(summary, output)
    provenance = {"snapshot_at_utc": snapshot["generated_at_utc"],
                  "snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                  "condition_metadata_sha256": hashlib.sha256((source / "condition_sources.json").read_bytes()).hexdigest(),
                  "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / "action_sol_summary.json").write_text(json.dumps({**provenance, "results": summary}, indent=2) + "\n", encoding="utf-8")
    (output / "ACTION_SOL_REPORT.md").write_text(report(summary, snapshot["generated_at_utc"], figures), encoding="utf-8")
    print(json.dumps({kind: {"n": data["overall"]["n"], "fastest": data["groups"][0], "slowest": data["groups"][-1],
                            "paired_extreme_comparison": data["posthoc_extreme_comparison"]} for kind, data in summary.items()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
