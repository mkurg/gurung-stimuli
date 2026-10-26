"""Extended descriptive statistics from one immutable annotation snapshot."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from seminar_stats import CATEGORIES, COLORS, DISPLAY, INK, MUTED, TRANSITIVE_COUNT_COLORS, latency_summary, report_date

CUTOFFS = (0, 800, 900, 1000, 1100, 1200, 1250, 1300, 1400, 1500, 1600, 1800, 2000)


def mean(values):
    return statistics.mean(values) if values else None


def percent(n, denominator):
    return 100*n/denominator if denominator else None


def selected_summary(rows):
    sol = latency_summary([r["sol_ms"] for r in rows])
    return {**sol, "counts": {c: sum(r["category"] == c for r in rows) for c in CATEGORIES},
            "participants": len({r["recording"] for r in rows}), "need_help": sum(r["need_help"] for r in rows)}


def paired_categories(rows):
    entries = []
    for rec in sorted({r["recording"] for r in rows}):
        selected = [r for r in rows if r["recording"] == rec]
        erg = [r["sol_ms"] for r in selected if r["category"] == "Tr ERG"]
        zero = [r["sol_ms"] for r in selected if r["category"] == "Tr zero"]
        entries.append({"recording": rec, "erg_n": len(erg), "zero_n": len(zero),
                        "erg_mean_ms": mean(erg), "zero_mean_ms": mean(zero),
                        "erg_median_ms": statistics.median(erg) if erg else None,
                        "zero_median_ms": statistics.median(zero) if zero else None,
                        "mean_erg_minus_zero_ms": mean(erg)-mean(zero) if erg and zero else None,
                        "median_erg_minus_zero_ms": statistics.median(erg)-statistics.median(zero) if erg and zero else None})
    available = [p for p in entries if p["mean_erg_minus_zero_ms"] is not None]
    differences = [p["mean_erg_minus_zero_ms"] for p in available]
    return {"participants": entries, "paired_n": len(available),
            "equal_participant_mean_difference_ms": mean(differences),
            "median_participant_mean_difference_ms": statistics.median(differences) if differences else None,
            "erg_longer_participants": sum(v > 0 for v in differences),
            "minimum_cell_checks": [{"minimum_n_each": minimum,
                                     "participants": sum(p["erg_n"] >= minimum and p["zero_n"] >= minimum for p in available),
                                     "mean_difference_ms": mean([p["mean_erg_minus_zero_ms"] for p in available
                                                                 if p["erg_n"] >= minimum and p["zero_n"] >= minimum])}
                                    for minimum in (1, 5, 10, 15, 20, 25, 30)]}


def order_summary(rows):
    people, blocks = [], []
    for rec in sorted({r["recording"] for r in rows}):
        selected = [r for r in rows if r["recording"] == rec]
        for category in ("All", "Itr", "Transitive"):
            current = [r for r in selected if category == "All" or (r["category"] == "Itr") == (category == "Itr")]
            first = [r["sol_ms"] for r in current if r["trial_number"] <= 20]
            last = [r["sol_ms"] for r in current if r["trial_number"] >= 101]
            delta = mean(first)-mean(last) if first and last else None
            slope = statistics.linear_regression([r["trial_number"] for r in current], [r["sol_ms"] for r in current]).slope if len(current) >= 2 else None
            people.append({"recording": rec, "selection": category, "early_n": len(first), "late_n": len(last),
                           "early_mean_ms": mean(first), "late_mean_ms": mean(last),
                           "speedup_ms": delta, "speedup_percent": percent(delta, mean(first)) if delta is not None else None,
                           "linear_slope_ms_per_100_trials": slope*100 if slope is not None else None})
        for block in range(1, 7):
            current = [r for r in selected if (r["trial_number"]-1)//20 + 1 == block]
            for category in ("All", *CATEGORIES):
                cell = [r for r in current if category == "All" or r["category"] == category]
                blocks.append({"recording": rec, "block": block, "category": category,
                               "n": len(cell), "mean_ms": mean([r["sol_ms"] for r in cell])})
    overall = {}
    for category in ("All", "Itr", "Transitive"):
        values = [p for p in people if p["selection"] == category and p["speedup_ms"] is not None]
        overall[category] = {"paired_participants": len(values), "faster_later": sum(p["speedup_ms"] > 0 for p in values),
                             "mean_speedup_ms": mean([p["speedup_ms"] for p in values]),
                             "median_speedup_ms": statistics.median([p["speedup_ms"] for p in values]) if values else None,
                             "mean_speedup_percent": mean([p["speedup_percent"] for p in values])}
    return {"participants": people, "blocks": blocks, "overall": overall}


def retention(rows):
    participants = sorted({r["recording"] for r in rows})
    overall, by_person = [], []
    base = selected_summary(rows)
    base_tr = base["counts"]["Tr ERG"] + base["counts"]["Tr zero"]
    for cutoff in CUTOFFS:
        selected = [r for r in rows if r["sol_ms"] >= cutoff]
        counts = selected_summary(selected)["counts"]
        checks = {minimum: 0 for minimum in (5, 10, 15, 20, 25, 30)}
        for rec in participants:
            person = [r for r in selected if r["recording"] == rec]
            c = {category: sum(r["category"] == category for r in person) for category in CATEGORIES}
            for minimum in checks:
                checks[minimum] += c["Tr ERG"] >= minimum and c["Tr zero"] >= minimum
            by_person.append({"recording": rec, "minimum_sol_ms": cutoff, "Itr": c["Itr"],
                              "Tr ERG": c["Tr ERG"], "Tr zero": c["Tr zero"]})
        kept_tr = counts["Tr ERG"] + counts["Tr zero"]
        overall.append({"minimum_sol_ms": cutoff, "retained": len(selected), **counts,
                        "retained_percent": percent(len(selected), len(rows)), "transitive_retained": kept_tr,
                        "transitive_lost": base_tr-kept_tr, "transitive_lost_percent": percent(base_tr-kept_tr, base_tr),
                        **{f"participants_with_at_least_{minimum}_each": count for minimum, count in checks.items()}})
    return overall, by_person


def erg_order(all_rows):
    blocks, switches = [], []
    for rec in sorted({r["recording"] for r in all_rows}):
        all_tr = sorted([r for r in all_rows if r["recording"] == rec and r["category"] != "Itr"], key=lambda r: r["trial_number"])
        pairs = [(a, b) for a, b in zip(all_tr, all_tr[1:]) if a["eligible"] and b["eligible"]]
        changed = sum(a["category"] != b["category"] for a, b in pairs)
        switches.append({"recording": rec, "valid_adjacent_transitive_pairs": len(pairs),
                         "case_switches": changed, "switch_percent": percent(changed, len(pairs))})
        for block in range(1, 7):
            selected = [r for r in all_tr if r["eligible"] and (r["trial_number"]-1)//20+1 == block]
            erg = sum(r["category"] == "Tr ERG" for r in selected)
            blocks.append({"recording": rec, "block": block, "n": len(selected), "erg": erg,
                           "erg_percent": percent(erg, len(selected))})
    return blocks, switches


def help_summary(rows):
    groups, pairs = [], []
    for category in ("All", *CATEGORIES):
        selected = [r for r in rows if category == "All" or r["category"] == category]
        for marked in (False, True):
            group = [r for r in selected if r["need_help"] == marked]
            groups.append({"category": category, "need_help": marked, **latency_summary([r["sol_ms"] for r in group])})
        for rec in sorted({r["recording"] for r in selected}):
            a = [r["sol_ms"] for r in selected if r["recording"] == rec and r["need_help"]]
            b = [r["sol_ms"] for r in selected if r["recording"] == rec and not r["need_help"]]
            if a and b:
                pairs.append({"category": category, "recording": rec, "help_n": len(a), "no_help_n": len(b),
                              "help_minus_no_help_ms": mean(a)-mean(b)})
    return {"groups": groups, "paired_participants": pairs}


def timing_summary(snapshot):
    cells, per_trial = [], []
    for bundle in snapshot["bundles"]:
        session = bundle["session"]
        trials = sorted([t for t in session["trials"] if t["kind"] == "main"], key=lambda t: t["number"])
        values = defaultdict(list)
        for index, trial in enumerate(trials):
            duration = 1000*(trial["end"]-trial["start"])
            gap = 1000*(trials[index+1]["start"]-trial["end"]) if index+1 < len(trials) else None
            if duration <= 0 or (gap is not None and gap < 0):
                raise ValueError(f"Invalid EEG trigger ordering: {session['recording']} {trial['id']}")
            condition = [m["time"] for m in trial["triggers"] if m["role"] == "condition"]
            item = [m["time"] for m in trial["triggers"] if m["role"] == "item"]
            row = {"recording": session["recording"], "trial_id": trial["id"], "s200_to_s202_ms": duration,
                   "s202_to_next_s200_ms": gap,
                   "s200_to_condition_code_ms": 1000*(condition[0]-trial["start"]) if len(condition) == 1 else None,
                   "s200_to_item_code_ms": 1000*(item[0]-trial["start"]) if len(item) == 1 else None}
            per_trial.append(row)
            for key in ("s200_to_s202_ms", "s202_to_next_s200_ms", "s200_to_condition_code_ms", "s200_to_item_code_ms"):
                if row[key] is not None:
                    values[key].append(row[key])
        cells.append({"recording": session["recording"], "experiment_list": session["list"],
                      "recording_duration_minutes": session["duration"]/60,
                      "main_task_span_minutes": (trials[-1]["end"]-trials[0]["start"])/60,
                      **{key+"_median": statistics.median(val) for key, val in values.items()}})
    distributions = {key: latency_summary([row[key] for row in per_trial if row[key] is not None])
                     for key in ("s200_to_s202_ms", "s202_to_next_s200_ms", "s200_to_condition_code_ms", "s200_to_item_code_ms")}
    return {"participants": cells, "trials": per_trial, "distributions": distributions,
            "total_recorded_hours": sum(p["recording_duration_minutes"] for p in cells)/60}


def build_summary(all_rows, snapshot):
    rows = [r for r in all_rows if r["eligible"]]
    if not rows:
        raise ValueError("No eligible trials")
    paired = paired_categories(rows)
    order = order_summary(rows)
    timing, by_person = retention(rows)
    blocks, switches = erg_order(all_rows)
    people = sorted({r["recording"] for r in rows})
    fastest = sorted(people, key=lambda rec: mean([r["sol_ms"] for r in rows if r["recording"] == rec]))[:2]
    scenarios = [("All eligible", rows), ("Without Need help", [r for r in rows if not r["need_help"]]),
                 ("Without fastest two", [r for r in rows if r["recording"] not in fastest]),
                 ("Without both", [r for r in rows if not r["need_help"] and r["recording"] not in fastest]),
                 ("SOL at least 1200 ms", [r for r in rows if r["sol_ms"] >= 1200])]
    sensitivities = []
    for name, values in scenarios:
        categories = {c: latency_summary([r["sol_ms"] for r in values if r["category"] == c]) for c in CATEGORIES}
        a, b = categories["Tr ERG"]["mean_ms"], categories["Tr zero"]["mean_ms"]
        paired_selection = paired_categories(values)
        sensitivities.append({"scenario": name, **selected_summary(values), "category_sol": categories,
                              "pooled_erg_minus_zero_ms": a-b if a is not None and b is not None else None,
                              "paired_participants": paired_selection["paired_n"],
                              "equal_person_erg_minus_zero_ms": paired_selection["equal_participant_mean_difference_ms"]})
    quality = []
    for group in ("Itr", "Transitive"):
        selected = [r for r in all_rows if (r["category"] == "Itr") == (group == "Itr")]
        quality.append({"transitivity": group, "scheduled": len(selected), "eligible": sum(r["eligible"] for r in selected),
                        "unsuitable": sum(r["unsuitable"] for r in selected),
                        "need_help_all": sum(r["need_help"] for r in selected),
                        "need_help_eligible": sum(r["need_help"] and r["eligible"] for r in selected),
                        "eligible_percent": percent(sum(r["eligible"] for r in selected), len(selected))})
    categories = []
    for category in CATEGORIES:
        selected = [r for r in rows if r["category"] == category]
        participant_means = [mean([r["sol_ms"] for r in selected if r["recording"] == rec]) for rec in people]
        categories.append({"category": category, **selected_summary(selected),
                           "equal_participant_mean_ms": mean([v for v in participant_means if v is not None]),
                           "fraction_of_eligible_percent": percent(len(selected), len(rows)),
                           "need_help_percent": percent(sum(r["need_help"] for r in selected), len(selected))})
    projections = []
    for t in timing:
        for loss in (0, .1, .2):
            erg_yield = t["Tr ERG"]/len(people)*(1-loss)
            zero_yield = t["Tr zero"]/len(people)*(1-loss)
            projections.append({"minimum_sol_ms": t["minimum_sol_ms"], "additional_eeg_rejection_fraction": loss,
                                "provisional_target_each": 800,
                                "projected_total_participants": math.ceil(max(800/erg_yield, 800/zero_yield)) if erg_yield and zero_yield else None})
    return {"snapshot_at_utc": snapshot["generated_at_utc"], "report_timezone": "Europe/Zurich",
            "eligible": selected_summary(rows), "categories": categories, "quality_by_transitivity": quality,
            "paired_erg_zero": paired, "trial_order": order, "retention": timing,
            "retention_by_participant": by_person, "erg_blocks": blocks, "erg_switches": switches,
            "fastest_two_by_all_eligible_mean": fastest, "sensitivity": sensitivities,
            "help": help_summary(rows), "trigger_timing": timing_summary(snapshot), "yield_projections": projections}


def make_figures(all_rows, summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.text import Text
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False, "axes.axisbelow": True})
    rows = [r for r in all_rows if r["eligible"]]
    people = sorted({r["recording"] for r in rows})
    figures = []
    standard = "Eligible main trials; Unsuitable excluded; Need help included. No EEG artifact rejection."
    def decorate(fig, title, subtitle, note=standard):
        fig.text(.07, .955, title, fontsize=23, fontweight="bold", va="top")
        fig.text(.07, .905, subtitle, fontsize=11, color=MUTED, va="top")
        fig.text(.07, .045, note, fontsize=9, color=MUTED, va="bottom", linespacing=1.5)
        fig.text(.97, .018, report_date(summary["snapshot_at_utc"]), fontsize=9, color=MUTED, ha="right")
    def finish(fig, name):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        w, h = fig.canvas.get_width_height()
        for label in fig.findobj(Text):
            if label.get_visible() and label.get_text():
                box = label.get_window_extent(renderer)
                if box.x0 < -1 or box.x1 > w+1 or box.y0 < -1 or box.y1 > h+1:
                    raise ValueError(f"Clipped label in {name}: {label.get_text()}")
        fig.savefig(output/name, dpi=220, facecolor="white")
        plt.close(fig)
        figures.append(name)
    def axes_grid(ax, axis="x"):
        ax.grid(axis=axis, color="#e7edef", linewidth=.8)
        ax.tick_params(length=0, pad=8)
        for dim in ("x", "y"):
            lo, hi = sorted(getattr(ax, "get_"+dim+"lim")())
            getattr(ax, "set_"+dim+"ticks")([v for v in getattr(ax, "get_"+dim+"ticks")() if lo <= v <= hi])
    tall = max(8.5, 3+.37*len(people))

    paired = sorted([p for p in summary["paired_erg_zero"]["participants"] if p["mean_erg_minus_zero_ms"] is not None],
                    key=lambda p: p["mean_erg_minus_zero_ms"])
    fig, ax = plt.subplots(figsize=(14, tall))
    fig.subplots_adjust(left=.12, right=.80, top=.83, bottom=.17)
    delta = [p["mean_erg_minus_zero_ms"] for p in paired]
    ax.barh(range(len(paired)), delta, color=["#0072b2" if v >= 0 else "#d55e00" for v in delta], height=.6)
    bound = max(200, math.ceil(max(abs(v) for v in delta)/100)*100)
    ax.set(xlim=(-bound*1.12, bound*1.12), xlabel="Mean SOL difference: ERG minus non-ERG (ms)")
    ax.set_yticks(range(len(paired)), [p["recording"] for p in paired]); ax.invert_yaxis()
    ax.axvline(0, color=INK, lw=1)
    for y, p in enumerate(paired):
        ax.text(1.03, y, f"{p['mean_erg_minus_zero_ms']:+.0f} ms    {p['erg_n']}/{p['zero_n']}", transform=ax.get_yaxis_transform(), va="center", fontsize=11)
    axes_grid(ax)
    decorate(fig, "ERG and non-ERG latency within each participant", "Right: longer with ERG; left: shorter with ERG. Labels give difference and ERG/non-ERG trial counts.",
             standard+"\nDescriptive paired means; pictures and order are not matched. Small condition cells can be unstable.")
    finish(fig, "13_paired_erg_zero_sol.png")

    order = [p for p in summary["trial_order"]["participants"] if p["selection"] == "All"]
    fig, ax = plt.subplots(figsize=(14, tall))
    fig.subplots_adjust(left=.12, right=.80, top=.80, bottom=.17)
    for y, p in enumerate(order):
        ax.plot([p["early_mean_ms"], p["late_mean_ms"]], [y, y], color="#b7c5ca", lw=2)
        ax.scatter(p["early_mean_ms"], y, color="#0072b2", s=48, zorder=3, label="Trials 1-20" if y == 0 else None)
        ax.scatter(p["late_mean_ms"], y, color="#d55e00", s=48, marker="D", zorder=3, label="Trials 101-120" if y == 0 else None)
        ax.text(1.03, y, f"{p['speedup_ms']:+.0f} ms   {p['early_n']}/{p['late_n']}", transform=ax.get_yaxis_transform(), va="center", fontsize=11)
    ax.set_yticks(range(len(order)), [p["recording"] for p in order]); ax.invert_yaxis()
    ax.set(xlabel="Mean speech-onset latency (ms)")
    ax.legend(frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.02))
    axes_grid(ax)
    decorate(fig, "Speed change from the first to last 20 trials", "Labels: early minus late mean (positive = faster later), and eligible early/late counts.",
             standard+"\nUses scheduled positions, not first/last 20 eligible responses. Pictures and category mix are not matched.")
    finish(fig, "14_early_late_speedup.png")

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.subplots_adjust(left=.09, right=.95, top=.81, bottom=.22)
    block_data = summary["trial_order"]["blocks"]
    for rec in people:
        cell = [p for p in block_data if p["recording"] == rec and p["category"] == "All"]
        ax.plot(range(1, 7), [p["mean_ms"] for p in cell], color="#c9d2d5", lw=.9, alpha=.6)
    for category in CATEGORIES:
        block_means = [mean([p["mean_ms"] for p in block_data if p["block"] == block and p["category"] == category and p["n"]]) for block in range(1, 7)]
        ax.plot(range(1, 7), block_means, marker="o", color=COLORS[category], lw=2.5, label=DISPLAY[category])
    ax.set_xticks(range(1, 7), [f"{i}-{i+19}" for i in range(1, 121, 20)])
    ax.set(xlabel="Scheduled trial positions", ylabel="Mean SOL (ms)")
    ax.legend(frameon=False, ncol=3); axes_grid(ax, "y")
    decorate(fig, "Speech onset across the task", "Coloured lines: equal-weight participant means in each category/block. Grey: each participant, all eligible trials.",
             standard+"\nNonempty participant cells contribute equally; cell sizes and pictures differ. Lines are descriptive, not confidence bands.")
    finish(fig, "15_sol_by_trial_block.png")

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.subplots_adjust(left=.09, right=.95, top=.81, bottom=.22)
    blocks = summary["erg_blocks"]
    for rec in people:
        cell = [p for p in blocks if p["recording"] == rec]
        ax.plot(range(1, 7), [p["erg_percent"] for p in cell], color="#bcc8ce", lw=1, alpha=.8)
    equal = [mean([p["erg_percent"] for p in blocks if p["block"] == b and p["n"]]) for b in range(1, 7)]
    pooled = [percent(sum(p["erg"] for p in blocks if p["block"] == b), sum(p["n"] for p in blocks if p["block"] == b)) for b in range(1, 7)]
    ax.plot(range(1, 7), equal, color="#0072b2", marker="o", lw=2.7, label="Equal participant weight")
    ax.plot(range(1, 7), pooled, color=INK, ls="--", marker="s", lw=1.7, label="Pooled trials")
    ax.axhline(50, color="#aebec5", ls=":")
    ax.set_xticks(range(1, 7), [f"{i}-{i+19}" for i in range(1, 121, 20)])
    ax.set(xlabel="Scheduled trial positions", ylabel="Transitive responses marked ERG (%)", ylim=(0, 100))
    ax.legend(frameon=False, ncol=2); axes_grid(ax, "y")
    decorate(fig, "ERG use across the task", "Grey lines: individual participants. ERG = manual flag; non-ERG = not marked ERG.",
             standard+"\nEligible transitive trials only. Different pictures and unequal trial counts can influence block rates.")
    finish(fig, "16_erg_by_trial_block.png")

    fig, axes = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={"width_ratios": [1.3, 1]})
    fig.subplots_adjust(left=.08, right=.96, top=.81, bottom=.22, wspace=.25)
    retained = summary["retention"]
    for category in ("Tr ERG", "Tr zero"):
        axes[0].plot([r["minimum_sol_ms"] for r in retained], [r[category] for r in retained], marker="o", lw=2.2,
                     color=TRANSITIVE_COUNT_COLORS[category], label=DISPLAY[category])
    axes[0].set(xlabel="Minimum SOL retained (ms)", ylabel="Eligible transitive trials retained", xlim=(0, 2000))
    axes[0].legend(frameon=False); axes_grid(axes[0], "y")
    focus = [r for r in retained if r["minimum_sol_ms"] in (1000, 1100, 1200, 1400)]
    bars = axes[1].bar(range(len(focus)), [r["transitive_lost_percent"] for r in focus], color="#b75c50", width=.6)
    axes[1].bar_label(bars, labels=[f"{r['transitive_lost_percent']:.1f}%" for r in focus], padding=6)
    axes[1].set_xticks(range(len(focus)), [str(r["minimum_sol_ms"]) for r in focus])
    axes[1].set(xlabel="Minimum SOL retained (ms)", ylabel="Eligible transitive trials lost (%)", ylim=(0, 100))
    axes_grid(axes[1], "y")
    decorate(fig, "Transitive trial retention at speech-onset cutoffs", "All participants; thresholds include trials exactly at the cutoff.",
             standard+"\nTiming eligibility only. A nominal pre-speech gap does not establish artifact-free EEG or safe time-frequency support.")
    finish(fig, "17_timing_cutoff_retention.png")

    fig, axes = plt.subplots(1, 2, figsize=(13, tall))
    fig.subplots_adjust(left=.12, right=.94, top=.81, bottom=.17, wspace=.38)
    for ax, cutoff, title in zip(axes, (0, 1200), ("All eligible transitive trials", "SOL at least 1200 ms")):
        matrix = np.asarray([[next(p for p in summary["retention_by_participant"] if p["recording"] == rec and p["minimum_sol_ms"] == cutoff)[c]
                              for c in ("Tr ERG", "Tr zero")] for rec in people])
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=60, aspect="auto")
        for (y, x), value in np.ndenumerate(matrix):
            ax.text(x, y, str(value), ha="center", va="center", color="white" if value >= 35 else INK, fontsize=12)
        ax.set_yticks(range(len(people)), people)
        ax.set_xticks((0, 1), ("Tr ERG", "Tr \u2205"))
        ax.tick_params(length=0, pad=8); ax.set_title(title, fontsize=13, pad=14)
    decorate(fig, "Transitive counts before and after a 1200 ms cutoff", "Each cell gives the retained trial count. Shared colour scale: 0 to 60 trials.",
             standard+"\nParticipant condition imbalance remains after a timing cutoff. No additional cleaning or cell-size exclusion is applied.")
    finish(fig, "18_participant_timing_cells.png")

    fig, (ax, lat) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(left=.19, right=.96, top=.78, bottom=.22, wspace=.20)
    scenarios = summary["sensitivity"]
    left = np.zeros(len(scenarios))
    for category in CATEGORIES:
        values = np.asarray([r["counts"][category] for r in scenarios])
        bars = ax.barh(range(len(scenarios)), values, left=left, height=.55,
                       color=COLORS["Itr"] if category == "Itr" else TRANSITIVE_COUNT_COLORS[category], label=DISPLAY[category])
        ax.bar_label(bars, label_type="center", labels=[str(v) for v in values], color="white", fontsize=11)
        left += values
    ax.set_yticks(range(len(scenarios)), [r["scenario"] for r in scenarios]); ax.invert_yaxis()
    ax.set(xlabel="Eligible responses in each scenario")
    ax.legend(frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.02), fontsize=11)
    axes_grid(ax)
    for shift, key, label, colour, marker in ((-.08, "mean_ms", "Mean", "#0072b2", "o"), (.08, "median_ms", "Median", "#d55e00", "D")):
        lat.scatter([r[key] for r in scenarios], np.arange(len(scenarios))+shift, label=label, color=colour, marker=marker, s=55)
    lat.set_yticks(range(len(scenarios)), []); lat.invert_yaxis(); lat.set(xlabel="Speech-onset latency (ms)")
    lat.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.02)); axes_grid(lat)
    decorate(fig, "Descriptive sensitivity summaries", "Fastest two by mean SOL over all eligible categories: " + ", ".join(summary["fastest_two_by_all_eligible_mean"]),
             "The main analysis includes everybody and Need help. These are alternative descriptive selections, not recommended exclusions.\n"
             "The 1200 ms selection mechanically removes fast responses; its higher mean is not a treatment effect.")
    finish(fig, "19_sensitivity_summary.png")

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.subplots_adjust(left=.19, right=.96, top=.81, bottom=.23)
    sets, labels, colours = [], [], []
    for category in CATEGORIES:
        for marked in (False, True):
            values = [r["sol_ms"] for r in rows if r["category"] == category and r["need_help"] == marked]
            sets.append(values); labels.append(f"{DISPLAY[category]} / {'Need help' if marked else 'No help flag'} (n={len(values)})")
            colours.append("#b48930" if marked else COLORS[category])
    boxes = ax.boxplot(sets, orientation="horizontal", widths=.5, patch_artist=True, showfliers=False,
                       medianprops={"color": INK, "linewidth": 1.8})
    for y, values, box, colour in zip(range(1, 7), sets, boxes["boxes"], colours):
        box.set(facecolor=colour, alpha=.35)
        if values:
            ax.scatter(mean(values), y, color="#b34b42", marker="D", s=42, zorder=3)
    ax.set_yticks(range(1, 7), labels); ax.invert_yaxis()
    ax.set(xlabel="Speech-onset latency from S200 (ms)"); axes_grid(ax)
    decorate(fig, "Latency and Need help flags", "Boxes: middle 50%; black line: median; red diamond: mean. Outlying trials remain in all calculations.",
             standard+"\nNeed help is a transcription/review flag, not a diagnosed cause of slow speech. Pooled groups differ in participants and pictures.")
    finish(fig, "20_need_help_latency.png")

    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    fig.subplots_adjust(left=.08, right=.96, top=.81, bottom=.23, wspace=.23)
    for ax, key, label, colour in ((axes[0], "s200_to_s202_ms", "S200 to S202 (ms)", "#087f78"),
                                    (axes[1], "s202_to_next_s200_ms", "S202 to next S200 (ms)", "#b48930")):
        values = [p[key] for p in summary["trigger_timing"]["trials"] if p[key] is not None]
        bins = np.geomspace(min(values)*.99, max(values)*1.01, 60) if min(values) > 0 else 40
        ax.hist(values, bins=bins, color=colour, alpha=.75, edgecolor="white")
        if min(values) > 0:
            ax.set_xscale("log")
            label += " / log scale"
        ax.axvline(statistics.median(values), color=INK, ls="--", label=f"Median {statistics.median(values):,.0f} ms")
        ax.set(xlabel=label, ylabel="Main trials / inter-trial gaps")
        ax.legend(frameon=False); axes_grid(ax, "y")
    decorate(fig, "EEG trigger timing across the task", "All scheduled main trials, including Unsuitable. Last trial of each recording has no following-trial gap.",
             "Times come from the EEG clock. These intervals describe recorded markers, not independently measured physical screen latencies.\n"
             "Log-spaced bins preserve the long intervals rather than removing them. No original markers were changed.")
    finish(fig, "21_trigger_interval_timing.png")
    return figures


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def table(columns, rows):
    lines = ["| " + " | ".join(label for key, label in columns) + " |", "|"+"---|"*len(columns)]
    for row in rows:
        values = []
        for key, label in columns:
            value = row.get(key)
            if key == "category" and isinstance(value, str):
                value = DISPLAY.get(value, value)
            values.append("n.a." if value is None else f"{value:.1f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def report(summary, figures):
    s = summary; e = s["eligible"]; paired = s["paired_erg_zero"]
    lines = ["# Extended Descriptive Report", "", "Snapshot date (Europe/Zurich): " + report_date(s["snapshot_at_utc"]),
             "UTC source timestamp: " + s["snapshot_at_utc"], "",
             "## Scope and Definitions", "",
             "Main trials with saved nonblank transcription, exactly one valid speech onset and no Unsuitable flag are eligible. "
             "Need help is included. SOL is acoustic onset minus EEG S200. No EEG artifact rejection or timing/participant "
             "exclusion is applied unless a specific sensitivity row says otherwise. There is no subtraction of a PsychoPy clock offset.", "",
             "ERG means the manual flag; non-ERG means not marked ERG, including missing saved decisions. "
             "Noun and indefinite-marker coding is provisional, not a validated parser. No indefinite marker is not labelled definite. "
             "This report is descriptive and exploratory: no significance tests, automatic preferred model, causal claims or multiple-comparison fishing.", "",
             "## Recording Coverage and Quality", "",
             f"{e['participants']} contributing participants, {e['n']} eligible responses. "
             f"Total recorded EEG duration, including practice and other periods: {s['trigger_timing']['total_recorded_hours']:.2f} hours.", "",
             table((("transitivity", "Type"), ("scheduled", "Scheduled"), ("eligible", "Eligible"), ("eligible_percent", "Eligible (%)"),
                    ("unsuitable", "Unsuitable"), ("need_help_all", "Need help (all)"), ("need_help_eligible", "Need help (eligible)")), s["quality_by_transitivity"]), "",
             "## Category Latencies", "",
             table((("category", "Category"), ("n", "n"), ("mean_ms", "Mean ms"), ("median_ms", "Median ms"),
                    ("sd_ms", "SD ms"), ("q1_ms", "Q1 ms"), ("q3_ms", "Q3 ms"),
                    ("equal_participant_mean_ms", "Equal-person mean ms"), ("need_help_percent", "Need help (%)")), s["categories"]), "",
             "Pooled means weight trials equally. Equal-person means first average within each participant and category. "
             "Neither controls pictures or trial order; SD describes trial variability, not uncertainty of a group mean.", "",
             "## ERG versus Non-ERG Within Participants", "",
             f"Equal-weight mean of {paired['paired_n']} participant mean differences (ERG minus non-ERG): "
             f"{paired['equal_participant_mean_difference_ms']:.1f} ms. Median participant difference: "
             f"{paired['median_participant_mean_difference_ms']:.1f} ms. ERG is slower in {paired['erg_longer_participants']}/{paired['paired_n']} participants.", "",
             table((("recording", "Participant"), ("erg_n", "ERG n"), ("zero_n", "Non-ERG n"),
                    ("erg_mean_ms", "ERG mean ms"), ("zero_mean_ms", "Non-ERG mean ms"),
                    ("mean_erg_minus_zero_ms", "Mean difference ms"), ("median_erg_minus_zero_ms", "Median difference ms")), paired["participants"]), "",
             "Small condition cells are shown, not silently excluded. The following checks restrict both cells to the stated minimum; "
             "they are descriptive sensitivity summaries, not validated minimum sample-size recommendations.", "",
             table((("minimum_n_each", "Minimum trials each"), ("participants", "Participants"), ("mean_difference_ms", "Mean difference ms")), paired["minimum_cell_checks"]), "",
             "## Speed Change Across the Task", "",
             "Early means use eligible trials at scheduled positions 1-20; late means use positions 101-120. "
             "Positive early-minus-late values mean speeding up. These are not picture-matched comparisons.", "",
             table((("selection", "Selection"), ("paired_participants", "Participants"), ("faster_later", "Faster later"),
                    ("mean_speedup_ms", "Mean speedup ms"), ("median_speedup_ms", "Median speedup ms"), ("mean_speedup_percent", "Mean speedup (%)")),
                   [{"selection": key, **value} for key, value in s["trial_order"]["overall"].items()]), "",
             table((("recording", "Participant"), ("early_n", "Early n"), ("late_n", "Late n"),
                    ("early_mean_ms", "Early mean ms"), ("late_mean_ms", "Late mean ms"),
                    ("speedup_ms", "Speedup ms"), ("speedup_percent", "Speedup (%)"),
                    ("linear_slope_ms_per_100_trials", "Slope ms / 100 trials")),
                   [p for p in s["trial_order"]["participants"] if p["selection"] == "All"]), "",
             "## Timing Cutoffs", "",
             table((("minimum_sol_ms", "Minimum SOL ms"), ("Itr", "Itr"), ("Tr ERG", "Tr ERG"), ("Tr zero", "Tr non-ERG"),
                    ("transitive_retained", "Transitive retained"), ("transitive_lost_percent", "Transitive lost (%)"),
                    ("participants_with_at_least_10_each", "People with 10 each"), ("participants_with_at_least_20_each", "People with 20 each")), s["retention"]), "",
             "All thresholds are inclusive (SOL >= cutoff). Counts alone do not establish artifact-free EEG. "
             "A fixed acoustic buffer does not account for earlier EMG, filtering or time-frequency kernels reaching into later data. "
             "The present report does not choose an EEG analysis window or buffer.", "",
             "## Sensitivity Selections", "",
             "The fastest two were selected post hoc by their mean across all eligible categories: " + ", ".join(s["fastest_two_by_all_eligible_mean"])+". "
             "This is a descriptive sensitivity check, not an exclusion recommendation. Thresholding SOL mechanically raises its conditional mean.", "",
             table((("scenario", "Selection"), ("n", "n"), ("participants", "People"), ("mean_ms", "Mean ms"), ("median_ms", "Median ms"),
                    ("Itr", "Itr"), ("Tr ERG", "Tr ERG"), ("Tr zero", "Tr non-ERG")), [{**p, **p["counts"]} for p in s["sensitivity"]]), "",
             table((("scenario", "Selection"), ("pooled_erg_minus_zero_ms", "Pooled ERG minus non-ERG ms"),
                    ("paired_participants", "Paired people"), ("equal_person_erg_minus_zero_ms", "Equal-person difference ms")), s["sensitivity"]), "",
             "## Need Help and Latency", "",
             table((("category", "Category"), ("need_help", "Need help flag"), ("n", "n"), ("mean_ms", "Mean ms"), ("median_ms", "Median ms")), s["help"]["groups"]), "",
             "Need help marks transcription/review uncertainty. These groups differ in pictures and participants; no cause of longer/shorter speech is inferred. "
             "The CSV also provides paired within-participant descriptive differences where both review groups occur.", "",
             "## ERG Switching", "",
             "A valid pair consists of two consecutive scheduled transitive trials with both eligible; intervening intransitives are ignored. "
             "An excluded transitive breaks a pair. Switching is merely observed category change, not a test of randomness or switching cost.", "",
             table((("recording", "Participant"), ("valid_adjacent_transitive_pairs", "Valid pairs"), ("case_switches", "Changes"), ("switch_percent", "Changes (%)")), s["erg_switches"]), "",
             "## Trigger Intervals", "",
             table((("interval", "Interval"), ("n", "n"), ("mean_ms", "Mean ms"), ("median_ms", "Median ms"),
                    ("min_ms", "Minimum ms"), ("max_ms", "Maximum ms")), [{"interval": key, **value} for key, value in s["trigger_timing"]["distributions"].items()]), "",
             "These marker intervals are all on the EEG clock. The gap distribution includes long pauses/breaks: its median and quartiles "
             "describe ordinary transitions better than its mean. Long intervals are retained, not diagnosed as missing markers or behavioural errors. "
             "They do not measure physical picture/display latency or a clock offset. "
             "The final trial of each participant is excluded only from the next-trial-gap statistic.", "",
             "## Provisional Yield Projection", "",
             "For the previously discussed planning target of 800 eligible ERG plus 800 eligible non-ERG trials, the following projects "
             "total participants using average observed yield. Assumes the same population, protocol and condition/rejection distribution. "
             "Additional EEG rejection is applied equally to existing and future trials. These are expected-yield calculations, not a power analysis, "
             "a guaranteed yield, or evidence that 800 trials suffice for inference.", "",
             table((("minimum_sol_ms", "Minimum SOL ms"), ("additional_eeg_rejection_fraction", "Further EEG rejection fraction"),
                    ("projected_total_participants", "Projected total people")), [p for p in s["yield_projections"] if p["minimum_sol_ms"] in (0, 1000, 1200, 1400)]), "",
             "## Additional Tables", "",
             "The CSVs include participant-level category counts, timing-cell sizes, trial blocks, Need help contrasts, "
             "item-by-list summaries and coding cases needing review. The item table separates experiment lists and stimulus/image versions "
             "rather than assuming that an S-number names the same picture across lists. Token counts are not used as validated linguistic lengths.", "",
             "## Figures", ""]
    lines += [f"![{name}]({name})" for name in figures]
    return "\n".join(lines)+"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    args = parser.parse_args(); output = args.source_dir.resolve()
    snapshot = json.loads((output/"source_snapshot.json").read_text(encoding="utf-8"))
    rows = json.loads((output/"all_main_trials.json").read_text(encoding="utf-8"))
    summary = build_summary(rows, snapshot)
    figures = make_figures(rows, summary, output)
    summary["figures"] = figures
    summary["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary["snapshot_sha256"] = hashlib.sha256((output/"source_snapshot.json").read_bytes()).hexdigest()
    tables = {"paired_condition_latency.csv": summary["paired_erg_zero"]["participants"],
              "trial_order_by_participant.csv": summary["trial_order"]["participants"],
              "trial_block_sol.csv": summary["trial_order"]["blocks"],
              "timing_retention_full.csv": summary["retention"], "timing_by_participant.csv": summary["retention_by_participant"],
              "erg_by_trial_block.csv": summary["erg_blocks"], "erg_switches.csv": summary["erg_switches"],
              "need_help_latency.csv": summary["help"]["groups"], "need_help_paired.csv": summary["help"]["paired_participants"],
              "recording_timing.csv": summary["trigger_timing"]["participants"], "trigger_interval_trials.csv": summary["trigger_timing"]["trials"],
              "yield_projection.csv": summary["yield_projections"]}
    tables["sensitivity_category_sol.csv"] = [{"scenario": p["scenario"], "category": c, **data}
                                               for p in summary["sensitivity"] for c, data in p["category_sol"].items()]
    for name, values in tables.items(): write_csv(output/name, values)
    trial_index = {(b["session"]["session_id"], t["id"]): t for b in snapshot["bundles"] for t in b["session"]["trials"]}
    item_groups = defaultdict(list)
    for row in rows:
        if row["eligible"]:
            trial = trial_index[(row["session_id"], row["trial_id"])]
            key = (row["experiment_list"], row["item_trigger"], row["condition"], trial.get("image_set"), trial.get("stimulus_set"), trial.get("scene"))
            item_groups[key].append(row)
    items = []
    for key, values in sorted(item_groups.items()):
        items.append({**dict(zip(("experiment_list", "item_trigger", "condition", "image_set", "stimulus_set", "scene"), key)),
                      **latency_summary([r["sol_ms"] for r in values]), "participants": len({r["recording"] for r in values}),
                      "erg": sum(r["category"] == "Tr ERG" for r in values), "need_help": sum(r["need_help"] for r in values)})
    write_csv(output/"item_list_summaries.csv", items)
    coding = json.loads((output/"trial_linguistic_coding.json").read_text(encoding="utf-8"))
    review = [{**r, "coding_notes": "; ".join(r["coding_notes"])} for r in coding
              if r["noun_group"] == "Unresolved noun" or r["indefiniteness"] == "Unresolved subject"
              or any(note.startswith("uncertain") or note == "visible_case_ending_but_not_flagged_erg" for note in r["coding_notes"])]
    write_csv(output/"linguistic_coding_review.csv", review)
    summary["linguistic_review_trials"] = len(review)
    (output/"extended_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    (output/"EXTENDED_REPORT.md").write_text(report(summary, figures), encoding="utf-8")
    print(json.dumps({"eligible": summary["eligible"], "paired_erg_zero": {k:v for k,v in summary["paired_erg_zero"].items() if k != "participants"},
                      "trial_order": summary["trial_order"]["overall"], "fastest_two": summary["fastest_two_by_all_eligible_mean"],
                      "linguistic_review_trials": len(review), "figures": figures}, indent=2), flush=True)


if __name__ == "__main__":
    main()
