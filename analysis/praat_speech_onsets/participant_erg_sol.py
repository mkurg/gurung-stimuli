"""Plot participant-level transitive speech latency against ERG use and balance."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

from seminar_stats import INK, MUTED, latency_summary, summarize, trial_rows


def participant_summary(rows):
    result = []
    for recording in sorted({r["recording"] for r in rows}):
        selected = [r for r in rows if r["recording"] == recording and r["eligible"]
                    and r["category"] in ("Tr ERG", "Tr zero")]
        if not selected:
            continue
        erg = sum(r["category"] == "Tr ERG" for r in selected)
        share = 100 * erg / len(selected)
        sol = latency_summary([r["sol_ms"] for r in selected])
        result.append({"recording": recording, "transitive_n": len(selected),
                       "erg_n": erg, "zero_n": len(selected) - erg,
                       "erg_percent": share, "distance_from_50_pp": abs(share - 50),
                       "transitive_mean_sol_ms": sol["mean_ms"],
                       "transitive_median_sol_ms": sol["median_ms"],
                       "need_help_n": sum(r["need_help"] for r in selected),
                       "zero_without_saved_decision_n": sum(r["category"] == "Tr zero"
                           and not r["ergative_flag_saved"] for r in selected)})
    return result


def correlation(rows, xkey, ykey):
    xs, ys = [r[xkey] for r in rows], [r[ykey] for r in rows]
    if len(rows) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(xs, ys)


def association_summary(people):
    results = {}
    for xkey in ("erg_percent", "distance_from_50_pp"):
        entries = {}
        for ykey in ("transitive_mean_sol_ms", "transitive_median_sol_ms"):
            leave_one_out = {p["recording"]: correlation([r for r in people if r != p], xkey, ykey)
                             for p in people}
            available = [v for v in leave_one_out.values() if v is not None]
            entries[ykey] = {"pearson_r": correlation(people, xkey, ykey),
                             "leave_one_out_r": leave_one_out,
                             "leave_one_out_range": [min(available), max(available)] if available else None}
        results[xkey] = entries
    return results


def make_figure(people, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.text import Text
    from matplotlib.transforms import Bbox

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False})
    cmap = LinearSegmentedColormap.from_list("erg_share", ["#d55e00", "#90858d", "#0072b2"])
    norm = Normalize(0, 100)
    fig, axes = plt.subplots(1, 2, figsize=(16, 8.6))
    fig.subplots_adjust(left=.075, right=.965, top=.77, bottom=.34, wspace=.23)
    ys = [p["transitive_mean_sol_ms"] for p in people]
    low, high = math.floor((min(ys) - 130) / 100) * 100, math.ceil((max(ys) + 130) / 100) * 100
    for ax, xkey, title, xlabel in (
        (axes[0], "erg_percent", "Direction of case-marking preference", "Transitive responses marked ERG (%)"),
        (axes[1], "distance_from_50_pp", "How far from a 50/50 split?", "Distance from 50/50 (percentage points)"),
    ):
        xs = [p[xkey] for p in people]
        ax.scatter(xs, ys, c=[p["erg_percent"] for p in people], cmap=cmap, norm=norm,
                   s=100, edgecolors="white", linewidths=1.2, zorder=3)
        ax.set(xlim=(-5, 105) if xkey == "erg_percent" else (-3, 53), ylim=(low, high),
               xlabel=xlabel, ylabel="Mean transitive speech-onset latency (ms)")
        ax.set_xticks([0, 25, 50, 75, 100] if xkey == "erg_percent" else [0, 10, 20, 30, 40, 50])
        ax.set_title(title, loc="left", fontsize=14, pad=17)
        ax.grid(color="#e7edef", linewidth=.8)
        ax.tick_params(length=0, pad=8)
        if xkey == "erg_percent":
            ax.axvline(50, color="#b2bec5", linestyle="--", linewidth=1.2)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bounds = ax.get_window_extent(renderer)
        point_boxes = [Bbox.from_bounds(*ax.transData.transform((x, y)) - 7, 14, 14)
                       for x, y in zip(xs, ys)]
        occupied = []
        # Choose label offsets in display coordinates, avoiding points and earlier labels.
        offsets = [(dx, dy) for dy in (12, -16, 26, -30, 40, -44)
                   for dx in (10, -10, 28, -28, 48, -48)]
        for p, x, y in sorted(zip(people, xs, ys), key=lambda t: (t[2], t[1])):
            label = ax.annotate(p["recording"], (x, y), xytext=(10, 12), textcoords="offset points",
                                fontsize=10, va="center", ha="left", color=INK,
                                arrowprops={"arrowstyle": "-", "color": "#bec8cd", "lw": .65}, zorder=4)
            best = None
            for dx, dy in offsets:
                label.set_position((dx, dy))
                label.set_ha("left" if dx > 0 else "right")
                box = label.get_window_extent(renderer)
                # Annotation extents include the leader; measure text itself for collisions.
                box = Text.get_window_extent(label, renderer).expanded(1.10, 1.25)
                outside = box.x0 < bounds.x0 or box.x1 > bounds.x1 or box.y0 < bounds.y0 or box.y1 > bounds.y1
                overlap = sum(box.overlaps(b) for b in occupied + point_boxes)
                score = 1000 * outside + 100 * overlap + abs(dx) + abs(dy)
                if best is None or score < best[0]:
                    best = (score, dx, dy, box)
            _, dx, dy, box = best
            label.set_position((dx, dy))
            label.set_ha("left" if dx > 0 else "right")
            occupied.append(box)
    bar_ax = fig.add_axes([.32, .205, .36, .018])
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=bar_ax, orientation="horizontal",
                 ticks=[0, 25, 50, 75, 100], label="ERG use (%); orange = mostly non-ERG, blue = mostly ERG")
    fig.text(.075, .94, "Speech-onset latency and ERG use", fontsize=26, fontweight="bold", va="top")
    fig.text(.075, .885, f"{len(people)} participants; one point per participant; same eligible transitive trials used for both measures",
             fontsize=12, color=MUTED, va="top")
    fig.text(.075, .04, "Left: 0% = all non-ERG, 50% = evenly split, 100% = all ERG. Right: 0 = balanced, 50 = exclusively one form.\n"
             "Unsuitable excluded; Need help included; no SOL cutoff or EEG artifact rejection. Non-ERG = not marked ERG.\n"
             "Descriptive between-participant associations, not a within-participant ERG effect or a causal test.",
             fontsize=10, color=MUTED, linespacing=1.6)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    for text in fig.findobj(Text):
        if text.get_visible() and text.get_text():
            box = text.get_window_extent(renderer)
            if box.x0 < -1 or box.x1 > width + 1 or box.y0 < -1 or box.y1 > height + 1:
                raise ValueError(f"Clipped participant-plot label: {text.get_text()}")
    name = "12_participant_sol_vs_erg_use.png"
    fig.savefig(output / name, dpi=220, facecolor="white")
    plt.close(fig)
    return name


def report(people, associations, timestamp, figure):
    lines = ["# Participant Speed and ERG Use", "", "Frozen snapshot: " + timestamp, "",
             "Each participant is one observation. Both ERG percentage and SOL use the same eligible transitive trials. "
             "SOL is acoustic onset minus EEG S200, not a PsychoPy keyboard reaction time. "
             "Unsuitable trials are excluded; Need help is included; no SOL cutoff or EEG artifact rejection.", "",
             "ERG use = 100 * ERG / (ERG + not-marked-ERG). Distance from balance = abs(ERG percentage - 50), "
             "in percentage points. No arbitrary categorical cutoff is imposed. "
             "An absent ERG decision is counted as not marked ERG, as in the viewer, not independently verified absence.", "",
             "| Participant | ERG | Non-ERG | ERG (%) | Distance from 50/50 (pp) | Mean transitive SOL (ms) | Median (ms) |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for p in people:
        lines.append(f"| {p['recording']} | {p['erg_n']} | {p['zero_n']} | {p['erg_percent']:.1f} | "
                     f"{p['distance_from_50_pp']:.1f} | {p['transitive_mean_sol_ms']:.0f} | {p['transitive_median_sol_ms']:.0f} |")
    lines += ["", "## Descriptive Correlations", "",
              "Pearson r gives each participant equal weight. These exploratory correlations do not adjust for "
              "pictures, noun choice, participant characteristics or trial order; no inferential p-values are reported. "
              "They cannot establish that using ERG makes an individual faster/slower. "
              "The leave-one-out range shows sensitivity to omitting one participant, not a confidence interval.", "",
              "| Predictor | Latency statistic | Pearson r | Leave-one-out range |", "|---|---|---:|---|"]
    for predictor, entries in associations.items():
        for outcome, entry in entries.items():
            r = entry["pearson_r"]
            limits = entry["leave_one_out_range"]
            rlabel = f"{r:.3f}" if r is not None else "n.a."
            interval = f"{limits[0]:.3f} to {limits[1]:.3f}" if limits else "n.a."
            lines.append(f"| {predictor} | {outcome} | {rlabel} | {interval} |")
    lines += ["", f"![Speech onset and ERG use]({figure})", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.source_dir.resolve()
    source = output / "source_snapshot.json"
    snapshot = json.loads(source.read_text(encoding="utf-8"))
    rows = trial_rows(snapshot)
    cohort = summarize(rows, snapshot)
    people = participant_summary(rows)
    counts = cohort["totals"]["eligible_category_counts"]
    if sum(p["erg_n"] for p in people) != counts["Tr ERG"] or sum(p["zero_n"] for p in people) != counts["Tr zero"]:
        raise ValueError("Participant totals do not match the frozen cohort.")
    associations = association_summary(people)
    figure = make_figure(people, output)
    payload = {"snapshot_at_utc": snapshot["generated_at_utc"],
               "snapshot_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "participants": people, "descriptive_correlations": associations}
    (output / "participant_erg_sol_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (output / "participant_erg_sol.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(people[0]))
        writer.writeheader()
        writer.writerows(people)
    (output / "PARTICIPANT_ERG_SOL.md").write_text(report(people, associations, snapshot["generated_at_utc"], figure), encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
