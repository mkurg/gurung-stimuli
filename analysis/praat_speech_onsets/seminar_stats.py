"""Make reproducible descriptive seminar figures from saved Praat work."""

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

CATEGORIES = ("Itr", "Tr ERG", "Tr zero")
DISPLAY = {"Itr": "Itr", "Tr ERG": "Tr ERG", "Tr zero": "Tr \u2205"}
COLORS = {"Itr": "#82769b", "Tr ERG": "#087f78", "Tr zero": "#377fb3"}
TRANSITIVE_COUNT_COLORS = {"Tr ERG": "#0072b2", "Tr zero": "#d55e00"}
INK, MUTED = "#202c33", "#66747c"


def get_json(base, path, session_id=None):
    query = "?" + urlencode({"session": session_id}) if session_id else ""
    with urlopen(base.rstrip("/") + path + query, timeout=90) as response:
        return json.load(response)


def flag_signature(session):
    return {key: session.get(key, {}) for key in ("suitability", "ergative", "need_help")}


def collect(base, expected_participants=None):
    for attempt in range(2):
        listing = get_json(base, "/api/sessions")
        if not listing["sessions"]:
            raise ValueError("No recordings are loaded in the reference interface.")
        if expected_participants is not None and len(listing["sessions"]) != expected_participants:
            raise ValueError(f"Expected {expected_participants} recordings, found {len(listing['sessions'])}.")
        bundles = []
        for entry in listing["sessions"]:
            session = get_json(base, "/api/session", entry["session_id"])
            annotations = get_json(base, "/api/annotations", entry["session_id"])
            if annotations["state"] != "ready":
                raise ValueError(f"{entry['recording']}: {annotations.get('message')}")
            bundles.append({"session": session, "annotations": annotations})
        consistent = True
        for bundle in bundles:
            sid = bundle["session"]["session_id"]
            now = get_json(base, "/api/session", sid)
            grid = get_json(base, "/api/annotations", sid)
            if flag_signature(now) != flag_signature(bundle["session"]) or grid.get("sha256") != bundle["annotations"]["sha256"]:
                consistent = False
                break
        if consistent:
            return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "base_url": base, "bundles": bundles,
                    "viewer_counts": get_json(base, "/api/library-counts")}
        print("Annotations or flags changed during collection; retrying the snapshot.", flush=True)
    raise ValueError("Data kept changing during collection. Save Praat and rerun.")


def trial_rows(snapshot):
    result = []
    identities = set()
    for bundle in snapshot["bundles"]:
        session, grid = bundle["session"], bundle["annotations"]
        for trial in session["trials"]:
            if trial["kind"] != "main":
                continue
            tid = trial["id"]
            identity = (session["session_id"], tid)
            if identity in identities:
                raise ValueError(f"Duplicate trial: {identity}")
            identities.add(identity)
            annotation = grid["trials"][tid]
            unsuitable = bool(session.get("suitability", {}).get(tid, {}).get("unsuitable", False))
            need_help = bool(session.get("need_help", {}).get(tid, {}).get("marked", False))
            erg = session.get("ergative", {}).get(tid, {})
            if trial["condition"].startswith("it_"):
                category = "Itr"
            elif trial["condition"].startswith("tr_"):
                category = "Tr ERG" if erg.get("marked", False) else "Tr zero"
            else:
                raise ValueError(f"Unexpected condition: {trial['condition']}")
            transcribed = bool(annotation.get("transcription", "").strip())
            valid = (annotation.get("status") == "ok" and annotation.get("onset_count") == 1
                     and annotation.get("speech_onset_eeg_s") is not None)
            latency = None
            if valid:
                latency = 1000 * (annotation["speech_onset_eeg_s"] - annotation["s200_eeg_s"])
                if not math.isfinite(latency) or latency < 0 or not math.isclose(latency, annotation["latency_ms"], abs_tol=1e-6):
                    raise ValueError(f"Invalid SOL: {session['recording']} / {tid}")
            eligible = not unsuitable and transcribed and valid
            result.append({"recording": session["recording"], "participant": session["participant"],
                           "session_id": session["session_id"], "experiment_list": session["list"],
                           "trial_id": tid, "trial_number": trial["number"], "condition": trial["condition"],
                           "item_trigger": trial["item"], "category": category,
                           "ergative_flag_saved": bool(erg), "unsuitable": unsuitable, "need_help": need_help,
                           "transcribed": transcribed, "valid_onset": valid, "eligible": eligible,
                           "annotation_status": annotation["status"], "onset_count": annotation.get("onset_count", 0),
                           "transcription": annotation.get("transcription", ""),
                           "s200_eeg_s": annotation.get("s200_eeg_s"),
                           "speech_onset_eeg_s": annotation.get("speech_onset_eeg_s"), "sol_ms": latency,
                           "textgrid_sha256": grid["sha256"]})
    return result


def latency_summary(values):
    if not values:
        return dict(n=0, **{key: None for key in ("mean_ms", "median_ms", "sd_ms", "q1_ms", "q3_ms", "min_ms", "max_ms")})
    ordered = sorted(values)
    def percentile(p):
        position = (len(ordered) - 1) * p
        lower = int(math.floor(position))
        upper = int(math.ceil(position))
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return {"n": len(values), "mean_ms": statistics.mean(values), "median_ms": statistics.median(values),
            "sd_ms": statistics.stdev(values) if len(values) > 1 else None,
            "q1_ms": percentile(.25), "q3_ms": percentile(.75), "min_ms": min(values), "max_ms": max(values)}


def summarize(rows, snapshot):
    participants = []
    for recording in sorted({row["recording"] for row in rows}):
        all_rows = [row for row in rows if row["recording"] == recording]
        usable = [row for row in all_rows if row["eligible"]]
        entry = {"recording": recording, "main_trials": len(all_rows),
                 "transcribed": sum(row["transcribed"] for row in all_rows),
                 "valid_onset": sum(row["valid_onset"] for row in all_rows),
                 "eligible": len(usable), "unsuitable": sum(row["unsuitable"] for row in all_rows),
                 "pending_not_unsuitable": sum(not row["unsuitable"] and not row["eligible"] for row in all_rows),
                 "need_help_all_main": sum(row["need_help"] for row in all_rows),
                 "need_help_eligible": sum(row["need_help"] for row in usable),
                 "need_help_unsuitable": sum(row["need_help"] and row["unsuitable"] for row in all_rows),
                 "missing_transcription": sum(not row["transcribed"] for row in all_rows),
                 "missing_onset": sum(row["annotation_status"] == "missing_onset" for row in all_rows),
                 "multiple_onsets": sum(row["annotation_status"] == "multiple_onsets" for row in all_rows),
                 "eligible_category_counts": {c: sum(row["category"] == c for row in usable) for c in CATEGORIES},
                 "all_main_category_counts": {c: sum(row["category"] == c for row in all_rows) for c in CATEGORIES},
                 "tr_zero_no_saved_flag": sum(row["category"] == "Tr zero" and not row["ergative_flag_saved"] for row in usable),
                 "sol": latency_summary([row["sol_ms"] for row in usable])}
        assert entry["eligible"] + entry["unsuitable"] + entry["pending_not_unsuitable"] == len(all_rows)
        assert sum(entry["eligible_category_counts"].values()) == len(usable)
        participants.append(entry)
    eligible = [row for row in rows if row["eligible"]]
    category_counts = {c: sum(row["category"] == c for row in eligible) for c in CATEGORIES}
    counts = snapshot["viewer_counts"]
    if not isinstance(counts.get("counts"), dict) or counts.get("recordings") != len(participants):
        raise ValueError(f"Viewer counts unavailable: {counts}")
    expected = {"itr": category_counts["Itr"], "tr_erg": category_counts["Tr ERG"], "tr_zero": category_counts["Tr zero"]}
    if counts["counts"] != expected:
        raise ValueError(f"Statistics do not match the live viewer: {expected} vs {counts['counts']}")
    total_keys = ("main_trials", "transcribed", "valid_onset", "eligible", "unsuitable", "pending_not_unsuitable",
                  "need_help_all_main", "need_help_eligible", "need_help_unsuitable", "missing_transcription", "missing_onset", "multiple_onsets")
    totals = {key: sum(p[key] for p in participants) for key in total_keys}
    totals.update(participants=len(participants), eligible_category_counts=category_counts,
                  sol=latency_summary([row["sol_ms"] for row in eligible]),
                  unweighted_participant_mean_sol_ms=statistics.mean(p["sol"]["mean_ms"] for p in participants if p["sol"]["n"]))
    per_category = {c: latency_summary([row["sol_ms"] for row in eligible if row["category"] == c]) for c in CATEGORIES}
    cutoffs = []
    for cutoff in (1000, 1100, 1200, 1250, 1400):
        retained = [row for row in eligible if row["sol_ms"] >= cutoff]
        cutoffs.append({"cutoff_ms": cutoff, "retained": len(retained), "below": len(eligible) - len(retained),
                        "retained_percent": 100 * len(retained) / len(eligible),
                        "category_counts": {c: sum(row["category"] == c for row in retained) for c in CATEGORIES}})
    return {"generated_at_utc": snapshot["generated_at_utc"], "totals": totals,
            "participants": participants, "per_category_sol": per_category, "timing_cutoffs": cutoffs,
            "onset_issues": [{key: row[key] for key in ("recording", "trial_id", "item_trigger", "onset_count", "unsuitable")}
                             for row in rows if row["annotation_status"] == "multiple_onsets"],
            "source_annotations": [{"recording": b["session"]["recording"], "session_id": b["session"]["session_id"],
                                    "path": b["annotations"]["path"], "sha256": b["annotations"]["sha256"],
                                    "saved_at_utc": b["annotations"]["saved_at_utc"],
                                    "unassigned_onsets": len(b["annotations"]["unassigned_onsets"]),
                                    "unassigned_transcriptions": len(b["annotations"]["unassigned_transcriptions"])}
                                   for b in snapshot["bundles"]]}


def make_figures(rows, summary, output, only=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import gaussian_kde
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
                         "axes.spines.bottom": False, "axes.axisbelow": True})
    eligible = [row for row in rows if row["eligible"]]
    participants = summary["participants"]
    contributors = sum(p["eligible"] > 0 for p in participants)
    if not eligible:
        raise ValueError("No eligible saved responses are available for plotting.")
    values = np.asarray([row["sol_ms"] for row in eligible], dtype=float)
    title_date = datetime.fromisoformat(summary["generated_at_utc"]).strftime("%d %B %Y").lstrip("0")
    figures = []
    note = "Main trials; Unsuitable excluded; saved transcription and one valid onset required. Need help included."
    def decorate(fig, title, subtitle, footer=note):
        fig.patch.set_facecolor("white")
        fig.text(.075, .94, title, fontsize=24, fontweight="bold", va="top")
        fig.text(.075, .89, subtitle, fontsize=12, color=MUTED, va="top")
        fig.text(.075, .055, footer, fontsize=10, color=MUTED, va="bottom", linespacing=1.5)
        fig.text(.975, .023, title_date, fontsize=9, color=MUTED, ha="right")
    def finish(fig, name):
        if only is not None and name != only:
            plt.close(fig)
            return
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        import matplotlib.text
        width, height = fig.canvas.get_width_height()
        for artist in fig.findobj(matplotlib.text.Text):
            if artist.get_visible() and artist.get_text():
                box = artist.get_window_extent(renderer)
                if box.x0 < -1 or box.x1 > width + 1 or box.y0 < -1 or box.y1 > height + 1:
                    raise ValueError(f"Clipped label in {name}: {artist.get_text()}")
        fig.savefig(output / name, dpi=220, facecolor="white")
        plt.close(fig)
        figures.append(name)
    def grid(ax, axis="x"):
        for name in ("x", "y"):
            low, high = sorted(getattr(ax, f"get_{name}lim")())
            ticks = getattr(ax, f"get_{name}ticks")()
            kept = [tick for tick in ticks if low <= tick <= high]
            if len(kept) != len(ticks):
                getattr(ax, f"set_{name}ticks")(kept)
        ax.grid(axis=axis, color="#e7edef", linewidth=.8)
        ax.tick_params(length=0, pad=9)

    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    fig.subplots_adjust(left=.075, right=.965, top=.815, bottom=.19)
    bins = np.arange(0, math.ceil(values.max() / 100) * 100 + 200, 100)
    ax.hist(values, bins=bins, color="#b9dbd4", edgecolor="white", linewidth=1,
            label="Observed trials (100 ms bins)")
    xs = np.linspace(0, bins[-1], 1600)
    ax.plot(xs, gaussian_kde(values)(xs) * len(values) * 100, color="#087f78", lw=2.7,
            label="Smoothed observed distribution")
    stats = summary["totals"]["sol"]
    ax.axvline(stats["mean_ms"], color="#b34b42", ls="--", lw=1.7, label=f"Mean {stats['mean_ms']:,.0f} ms")
    ax.axvline(stats["median_ms"], color=INK, ls=":", lw=1.7, label=f"Median {stats['median_ms']:,.0f} ms")
    ax.set(xlabel="Speech-onset latency from S200 (ms)", ylabel="Number of trials", xlim=(0, bins[-1]))
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    grid(ax, "y")
    decorate(fig, "Speech-onset latency", f"{contributors} contributing participants / {len(participants)} loaded recordings; n = {len(values):,}; SD = {stats['sd_ms']:,.0f} ms",
             note + "\nAll observed latencies retained. The distribution is not assumed to be Gaussian.")
    finish(fig, "01_sol_distribution.png")
    if only == "01_sol_distribution.png":
        return figures

    fig, ax = plt.subplots(figsize=(13.5, 8.2))
    fig.subplots_adjust(left=.145, right=.965, top=.82, bottom=.19)
    sets = [np.asarray([row["sol_ms"] for row in eligible if row["recording"] == p["recording"]]) for p in participants]
    boxes = ax.boxplot(sets, orientation="horizontal", patch_artist=True, widths=.43, showfliers=False,
                       medianprops={"color": INK, "linewidth": 2}, whiskerprops={"color": "#a2b2b8"},
                       capprops={"color": "#a2b2b8"}, boxprops={"facecolor": "#daebe7", "edgecolor": "#87b8ac"})
    random = np.random.default_rng(514)
    for i, v in enumerate(sets, 1):
        ax.scatter(v, i + random.uniform(-.14, .14, len(v)), s=8, alpha=.23, color="#4b7770", zorder=2)
        if len(v):
            ax.scatter(np.mean(v), i, marker="D", s=35, color="#b34b42", edgecolors="white", linewidths=.6, zorder=4)
    ax.set_yticks(np.arange(1, len(participants) + 1), [f"{p['recording']}  (n={p['eligible']})" for p in participants])
    ax.invert_yaxis()
    ax.set(xlabel="Speech-onset latency from S200 (ms)", xlim=(0, values.max() * 1.055))
    grid(ax)
    decorate(fig, "Speech-onset latency by participant", "Boxes: middle 50%; black line: median; red diamond: mean; points: individual trials",
             note + "\nAll participants included. No SOL cutoff or EEG artifact rejection applied.")
    finish(fig, "02_sol_by_participant.png")

    fig, ax = plt.subplots(figsize=(13.5, 8.2))
    fig.subplots_adjust(left=.11, right=.965, top=.82, bottom=.19)
    positions = np.arange(len(participants))
    for shift, category in ((-.19, "Tr ERG"), (.19, "Tr zero")):
        counts = [p["eligible_category_counts"][category] for p in participants]
        bars = ax.barh(positions + shift, counts, height=.33, color=TRANSITIVE_COUNT_COLORS[category], label=DISPLAY[category])
        ax.bar_label(bars, labels=[str(n) for n in counts], padding=6, fontsize=13, color=INK)
    ax.set_yticks(positions, [p["recording"] for p in participants])
    ax.invert_yaxis()
    ax.set(xlabel="Number of eligible transitive trials", xlim=(0, 64))
    ax.legend(frameon=False, loc="lower right", fontsize=13)
    grid(ax)
    totals = summary["totals"]["eligible_category_counts"]
    decorate(fig, "Transitive responses by participant", f"Tr ERG: {totals['Tr ERG']} trials; Tr \u2205: {totals['Tr zero']} trials; {len(participants)} loaded recordings",
             note + "\nTr \u2205 means not marked Ergative in the viewer; absence of a saved decision is not a confirmed no-ERG judgment.")
    finish(fig, "03_transitive_counts.png")

    fig, (ax, help_ax) = plt.subplots(1, 2, figsize=(13.5, 8.2), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=.11, right=.965, top=.755, bottom=.20, wspace=.13)
    left = np.zeros(len(participants))
    for key, label, color in (("eligible", "Eligible", "#087f78"), ("unsuitable", "Unsuitable", "#c05b52"),
                              ("pending_not_unsuitable", "Pending annotations", "#d8e0e3")):
        counts = np.asarray([p[key] for p in participants])
        bars = ax.barh(positions, counts, left=left, height=.61, color=color, label=label)
        for bar, count in zip(bars, counts):
            if count >= 7:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2, str(count),
                        ha="center", va="center", fontsize=11, color="white" if key != "pending_not_unsuitable" else INK)
        left += counts
    ax.set_yticks(positions, [p["recording"] for p in participants])
    ax.invert_yaxis()
    ax.set(xlim=(0, 123), xlabel="Main trials (120 per participant)")
    fig.text(.11, .835, "Annotation and suitability status", fontsize=14, va="top")
    ax.legend(frameon=False, fontsize=10, loc="upper left", bbox_to_anchor=(.11, .802),
              bbox_transform=fig.transFigure, ncol=3)
    grid(ax)
    for shift, key, label, color in ((-.19, "need_help_all_main", "All main trials", "#b48930"),
                                    (.19, "need_help_eligible", "Eligible subset", "#dec799")):
        counts = [p[key] for p in participants]
        bars = help_ax.barh(positions + shift, counts, height=.33, color=color, label=label)
        help_ax.bar_label(bars, padding=4, fontsize=11, color=INK)
    help_ax.set_yticks(positions, [])
    help_ax.invert_yaxis()
    help_ax.set(xlim=(0, max(5, max(p["need_help_all_main"] for p in participants) * 1.22)), xlabel="Need help flags")
    fig.text(.644, .835, "Need help", fontsize=14, va="top")
    help_ax.legend(frameon=False, fontsize=10, loc="upper left", bbox_to_anchor=(.644, .802),
                   bbox_transform=fig.transFigure, ncol=2)
    grid(help_ax)
    t = summary["totals"]
    decorate(fig, "Annotation progress and review flags", f"{t['eligible']} eligible / {t['main_trials']} main trials; {t['unsuitable']} Unsuitable; {t['need_help_all_main']} Need help flags",
             "Eligible requires saved transcription and one valid onset, and excludes Unsuitable. Pending excludes Unsuitable.\n"
             "Need help can overlap either category and is not an exclusion; the eligible subset is part of the all-trial total.")
    finish(fig, "04_progress_and_review.png")

    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    fig.subplots_adjust(left=.17, right=.965, top=.81, bottom=.20)
    sets = [np.asarray([r["sol_ms"] for r in eligible if r["category"] == c]) for c in CATEGORIES]
    boxes = ax.boxplot(sets, orientation="horizontal", patch_artist=True, widths=.43, showfliers=False,
                       medianprops={"color": INK, "linewidth": 2}, whiskerprops={"color": "#a2b2b8"},
                       capprops={"color": "#a2b2b8"})
    for i, (v, c, box) in enumerate(zip(sets, CATEGORIES, boxes["boxes"]), 1):
        box.set(facecolor=COLORS[c], alpha=.24, edgecolor=COLORS[c])
        ax.scatter(v, i + random.uniform(-.11, .11, len(v)), s=8, color=COLORS[c], alpha=.2)
        ax.scatter(np.mean(v), i, color="#b34b42", marker="D", s=55, edgecolors="white", linewidths=.7, zorder=4)
    ax.set_yticks(np.arange(1, 4), [f"{DISPLAY[c]}  (n={len(v)})" for c, v in zip(CATEGORIES, sets)])
    ax.invert_yaxis()
    ax.set(xlim=(0, values.max() * 1.055), xlabel="Speech-onset latency from S200 (ms)")
    grid(ax)
    decorate(fig, "Speech-onset latency by response category", "Pooled trials; boxes: middle 50%; black line: median; red diamond: mean",
             note + "\nDescriptive only: category comparisons are not adjusted for participant, picture, trial order or condition imbalance.")
    finish(fig, "05_sol_by_category.png")

    totals = summary["totals"]
    counts = totals["eligible_category_counts"]
    n = totals["eligible"]
    help_count = totals["need_help_eligible"]
    if sum(counts.values()) != n or not 0 <= help_count <= n:
        raise ValueError("Overview counts use inconsistent eligible-trial denominators.")
    help_percent = 100 * help_count / n
    fig = plt.figure(figsize=(13.5, 7.6))
    ax = fig.add_axes([.09, .23, .53, .54])
    bar_colors = [COLORS["Itr"], TRANSITIVE_COUNT_COLORS["Tr ERG"], TRANSITIVE_COUNT_COLORS["Tr zero"]]
    bars = ax.bar(np.arange(3), [counts[c] for c in CATEGORIES], color=bar_colors, width=.58)
    for bar, category in zip(bars, CATEGORIES):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 13,
                f"{counts[category]:,}", ha="center", va="bottom", fontsize=23, fontweight="bold")
    ax.set_xticks(np.arange(3), [DISPLAY[c] for c in CATEGORIES], fontsize=16)
    ax.set(ylabel="Number of eligible responses", ylim=(0, max(counts.values()) * 1.22))
    grid(ax, "y")
    fig.text(.805, .78, "Need help among eligible responses", ha="center", fontsize=15)
    donut = fig.add_axes([.682, .355, .25, .37])
    donut.pie([help_count, n - help_count], startangle=90, counterclock=False,
              colors=["#b48930", "#e4eaed"],
              wedgeprops={"width": .20, "edgecolor": "white", "linewidth": 2})
    donut.text(0, .12, f"{help_percent:.1f}%", fontsize=34, fontweight="bold", ha="center", va="center")
    donut.text(0, -.26, "Need help", fontsize=14, color=MUTED, ha="center", va="center")
    fig.text(.805, .29, f"{help_count:,} of {n:,} eligible responses", fontsize=15, ha="center")
    fig.text(.805, .25, f"{n-help_count:,} without a Need help flag", fontsize=12, color=MUTED, ha="center")
    decorate(fig, f"{n:,} eligible responses", f"All {totals['participants']} participants; category counts and review status",
             note + "\nNeed help is a flag within these responses, not a separate category. Tr \u2205 means not marked Ergative.")
    finish(fig, "06_eligible_overview.png")
    return figures


def report(summary, figures):
    t = summary["totals"]
    sol = t["sol"]
    date = datetime.fromisoformat(summary["generated_at_utc"]).strftime("%d %B %Y").lstrip("0")
    lines = ["# Lab Seminar: Descriptive Statistics", "", f"Snapshot: {date}.", "",
             "## Counting Rules", "",
             f"All {t['participants']} loaded recordings are included. Main trials only; practice and session events are excluded. "
             "SOL = annotated acoustic speech onset minus S200, in milliseconds. Eligible trials have "
             "nonblank saved transcription, exactly one valid speech onset, and are not marked Unsuitable. "
             "Need help remains included. No SOL cutoff, outlier trimming, participant exclusion, or EEG artifact rejection was applied.", "",
             "Tr ERG means marked Ergative. Tr zero (Tr \u2205) means not marked Ergative; a missing saved "
             "decision is not independent confirmation that case marking was absent.", "", "## Overall", "",
             f"- Participants: {t['participants']}; recorded main trials: {t['main_trials']}.",
             f"- Transcribed: {t['transcribed']}; valid single onset: {t['valid_onset']}; eligible: {t['eligible']}.",
             f"- Unsuitable: {t['unsuitable']}; pending annotations among non-Unsuitable trials: {t['pending_not_unsuitable']}.",
             f"- Need help: {t['need_help_all_main']} / {t['main_trials']} main trials "
             f"({100*t['need_help_all_main']/t['main_trials']:.1f}%); {t['need_help_eligible']} / {t['eligible']} eligible trials "
             f"({100*t['need_help_eligible']/t['eligible']:.1f}%). Need help and Unsuitable overlap on {t['need_help_unsuitable']} trials.",
             f"- Eligible categories: Itr {t['eligible_category_counts']['Itr']}; Tr ERG {t['eligible_category_counts']['Tr ERG']}; Tr \u2205 {t['eligible_category_counts']['Tr zero']}.",
             f"- Trial-weighted SOL: mean {sol['mean_ms']:.1f} ms; median {sol['median_ms']:.1f} ms; SD {sol['sd_ms']:.1f} ms.",
             f"- SOL middle 50%: {sol['q1_ms']:.1f}-{sol['q3_ms']:.1f} ms; range {sol['min_ms']:.1f}-{sol['max_ms']:.1f} ms.",
             f"- Equal-weight mean of participant mean SOLs: {t['unweighted_participant_mean_sol_ms']:.1f} ms.",
             "", "SD above describes trials, not uncertainty of the group mean. No inferential test or Gaussian assumption is used.",
             "", "## Participant Summary", "",
             "| Participant | Transcribed | Eligible | Itr | Tr ERG | Tr \u2205 | Unsuitable | Need help (all) | Need help (eligible) | Mean SOL (ms) | Median SOL (ms) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for p in summary["participants"]:
        c = p["eligible_category_counts"]
        mean = f"{p['sol']['mean_ms']:.0f}" if p["sol"]["n"] else "n.a."
        median = f"{p['sol']['median_ms']:.0f}" if p["sol"]["n"] else "n.a."
        lines.append(f"| {p['recording']} | {p['transcribed']}/120 | {p['eligible']} | {c['Itr']} | {c['Tr ERG']} | {c['Tr zero']} | "
                     f"{p['unsuitable']} | {p['need_help_all_main']} | {p['need_help_eligible']} | {mean} | {median} |")
    lines += ["", "## SOL by Category", "", "| Category | n | Mean (ms) | Median (ms) | SD (ms) |", "|---|---:|---:|---:|---:|"]
    for c in CATEGORIES:
        v = summary["per_category_sol"][c]
        mean = f"{v['mean_ms']:.1f}" if v["mean_ms"] is not None else "n.a."
        median = f"{v['median_ms']:.1f}" if v["median_ms"] is not None else "n.a."
        sd = f"{v['sd_ms']:.1f}" if v["sd_ms"] is not None else "n.a."
        lines.append(f"| {DISPLAY[c]} | {v['n']} | {mean} | {median} | {sd} |")
    lines += ["", "## Timing Eligibility", "", "These are timing counts only, not evidence of artifact-free EEG. "
              "For example, SOL >=1000 ms allows 600 ms plus a nominal 400 ms pre-speech gap; "
              ">=1200 ms allows 800 + 400 ms; >=1400 ms allows 800 + 600 ms. The gap still needs validation.", "",
              "| Minimum SOL (ms) | Retained | Retained (%) | Below threshold | Itr | Tr ERG | Tr \u2205 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for cutoff in summary["timing_cutoffs"]:
        c = cutoff["category_counts"]
        lines.append(f"| {cutoff['cutoff_ms']} | {cutoff['retained']} | {cutoff['retained_percent']:.1f} | {cutoff['below']} | {c['Itr']} | {c['Tr ERG']} | {c['Tr zero']} |")
    lines += ["", "## Annotation Checks", "",
              "Missing transcription and missing/multiple onset counts can overlap, and include Unsuitable trials. "
              "Unassigned speech-tier points can include deliberately added resting-state marks; they are preserved and not silently attached to trials.", "",
              "| Participant | No transcription | No onset | Multiple onsets | Unassigned points | Unassigned text intervals |",
              "|---|---:|---:|---:|---:|---:|"]
    sources = {s["recording"]: s for s in summary["source_annotations"]}
    for p in summary["participants"]:
        s = sources[p["recording"]]
        lines.append(f"| {p['recording']} | {p['missing_transcription']} | {p['missing_onset']} | {p['multiple_onsets']} | {s['unassigned_onsets']} | {s['unassigned_transcriptions']} |")
    if summary["onset_issues"]:
        lines += ["", "Trials with multiple onset marks:", ""]
        for row in summary["onset_issues"]:
            status = "already marked Unsuitable" if row["unsuitable"] else "not Unsuitable; excluded pending onset review"
            lines.append(f"- {row['recording']}, {row['trial_id']}, S {row['item_trigger']}: {row['onset_count']} onset marks; {status}.")
    lines += ["", "## Figures", ""] + [f"![{name}]({name})" for name in figures]
    lines += ["", "## Reproducibility", "", "Source: saved Praat TextGrids and recording-scoped trial decisions in the local reference interface. "
              "The source snapshot, source hashes, all-trial rows and summary JSON accompany this report. "
              "Charts describe this frozen snapshot and do not update automatically. Original annotations and flags were not edited.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--expected-participants", type=int, help="Optional check of the number of loaded recordings")
    parser.add_argument("--only", choices=("01_sol_distribution.png", "02_sol_by_participant.png", "03_transitive_counts.png",
                                         "04_progress_and_review.png", "05_sol_by_category.png", "06_eligible_overview.png"),
                        help="Render only the named PNG figure")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_path = output / "source_snapshot.json"
    if source_path.exists() and not args.snapshot:
        raise ValueError("Output already has a snapshot; choose a new directory or pass --snapshot explicitly.")
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else collect(args.base_url, args.expected_participants)
    rows = trial_rows(snapshot)
    summary = summarize(rows, snapshot)
    for filename, content in (("source_snapshot.json", snapshot), ("all_main_trials.json", rows), ("summary.json", summary)):
        (output / filename).write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    figures = make_figures(rows, summary, output, args.only)
    (output / "SEMINAR_REPORT.md").write_text(report(summary, figures), encoding="utf-8")
    print(json.dumps(summary["totals"], indent=2), flush=True)
    print("Figures: " + ", ".join(figures), flush=True)


if __name__ == "__main__":
    main()
