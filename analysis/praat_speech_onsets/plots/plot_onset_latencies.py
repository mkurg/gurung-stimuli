"""Plot current analysis-ready speech latencies from the local annotation viewer."""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde, norm


def collect_latencies(base_url):
    def get(path, session_id=None):
        query = "?" + urlencode({"session": session_id}) if session_id else ""
        with urlopen(base_url.rstrip("/") + path + query, timeout=30) as response:
            return json.load(response)

    rows, sources = [], []
    for entry in get("/api/sessions")["sessions"]:
        session_id = entry["session_id"]
        session = get("/api/session", session_id)
        grid = get("/api/annotations", session_id)
        if grid.get("state") != "ready":
            raise ValueError(f"{entry['recording']}: {grid.get('message', 'TextGrid unavailable')}")
        sources.append({key: grid[key] for key in ("session_id", "path", "sha256", "saved_at_utc")})
        for trial in session["trials"]:
            if trial["kind"] != "main":
                continue
            trial_id = trial["id"]
            annotation = grid["trials"].get(trial_id, {})
            if session.get("suitability", {}).get(trial_id, {}).get("unsuitable", False):
                continue
            if not annotation.get("transcription", "").strip():
                continue
            if (annotation.get("status") != "ok" or annotation.get("onset_count") != 1
                    or annotation.get("speech_onset_eeg_s") is None):
                continue
            onset = annotation["speech_onset_eeg_s"]
            s200 = annotation["s200_eeg_s"]
            latency = 1000 * (onset - s200)
            if not math.isfinite(latency) or latency < 0:
                raise ValueError(f"Invalid latency: {entry['recording']} / {trial_id}")
            if not math.isclose(latency, annotation["latency_ms"], abs_tol=1e-6):
                raise ValueError(f"Latency disagrees with S200: {entry['recording']} / {trial_id}")
            condition = trial["condition"]
            if condition.startswith("it_"):
                category = "Itr"
            elif condition.startswith("tr_"):
                marked = session.get("ergative", {}).get(trial_id, {}).get("marked", False)
                category = "Tr ERG" if marked else "Tr no ERG"
            else:
                raise ValueError(f"Unexpected trial condition: {condition}")
            rows.append({"recording": entry["recording"], "trial_id": trial_id,
                         "category": category, "s200_eeg_s": s200,
                         "speech_onset_eeg_s": onset, "latency_ms": latency,
                         "need_help": bool(session.get("need_help", {}).get(trial_id, {}).get("marked", False))})
    return rows, sources


def draw_distribution(values, output_dir, transitive_only=False):
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1))
    median = float(np.median(values))
    width_ms = 100
    upper = math.ceil(float(np.max(values)) / width_ms) * width_ms + width_ms
    bins = np.arange(0, upper + width_ms, width_ms)
    x = np.linspace(0, upper, 1400)
    scale = len(values) * width_ms

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "axes.labelcolor": "#283b42", "text.color": "#283b42",
                         "xtick.color": "#596b73", "ytick.color": "#596b73"})
    figure, ax = plt.subplots(figsize=(12.8, 7.5))
    figure.subplots_adjust(left=0.085, right=0.985, bottom=0.22, top=0.81)
    figure.patch.set_facecolor("white")
    ax.set_facecolor("white")
    counts, _, _ = ax.hist(values, bins=bins, color="#c6dfd5", edgecolor="white", linewidth=1,
                           label="Observed trials", zorder=2)
    density = gaussian_kde(values)
    ax.plot(x, density(x) * scale, color="#14796c", linewidth=2.8,
            label="Observed smoothed distribution", zorder=4)
    ax.plot(x, norm.pdf(x, loc=mean, scale=sd) * scale, color="#c95e4b",
            linewidth=2.4, linestyle=(0, (5, 3)), label="Fitted Gaussian", zorder=3)
    ax.axvline(mean, color="#334c58", linewidth=1.2, linestyle=":", alpha=0.8, zorder=3)
    ax.plot(values, np.full_like(values, -0.022), "|", color="#426a62", alpha=0.25,
            markersize=7, markeredgewidth=0.8, transform=ax.get_xaxis_transform(), clip_on=False)

    title = "Transitive speech-onset latency" if transitive_only else "Speech-onset latency"
    group = "Analysis-ready transitive trials" if transitive_only else "Analysis-ready main trials"
    ax.set_title(title, loc="left", fontsize=23, fontweight="bold", pad=47)
    ax.text(0, 1.045, f"{group}  |  n = {len(values):,}  |  Mean {mean:,.0f} ms"
            f"  |  Median {median:,.0f} ms  |  SD {sd:,.0f} ms", transform=ax.transAxes,
            color="#596b73", fontsize=12)
    ax.set_xlabel("Time from S200 to annotated speech onset (ms)", labelpad=18)
    ax.set_ylabel("Trials per 100 ms bin", labelpad=13)
    ax.set_xlim(0, upper)
    ax.set_ylim(0, max(float(counts.max()), float((density(x) * scale).max())) * 1.17)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e4ebee", linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("#d3dde1")
    ax.tick_params(axis="both", length=0, pad=9)
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    figure.text(0.085, 0.04,
                "Unsuitable excluded; saved transcription and one valid onset required. Need help included.\n"
                "Each small tick represents one trial. The Gaussian fit does not assume that the data are normal.",
                fontsize=10, color="#667880", ha="left", va="bottom", linespacing=1.6)

    prefix = "transitive_" if transitive_only else ""
    png = output_dir / f"{prefix}speech_onset_latency_distribution.png"
    pdf = output_dir / f"{prefix}speech_onset_latency_distribution.pdf"
    figure.savefig(png, dpi=180, facecolor="white")
    figure.savefig(pdf, facecolor="white")
    plt.close(figure)
    return {"n": len(values), "mean_ms": mean, "median_ms": median, "sd_ms": sd,
            "min_ms": float(np.min(values)), "max_ms": float(np.max(values)),
            "bin_width_ms": width_ms, "png": str(png), "pdf": str(pdf)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--transitive-only", action="store_true",
                        help="Include Tr ERG and Tr no ERG only; save a separate plot and data snapshot.")
    args = parser.parse_args()
    rows, sources = collect_latencies(args.base_url)
    if args.transitive_only:
        rows = [row for row in rows if row["category"] in ("Tr ERG", "Tr no ERG")]
    if len(rows) < 2:
        raise ValueError("At least two analysis-ready trials are needed.")
    values = np.asarray([row["latency_ms"] for row in rows], dtype=float)
    if float(np.std(values)) == 0:
        raise ValueError("The observed latencies have no variation.")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = draw_distribution(values, output_dir, transitive_only=args.transitive_only)
    summary["per_recording"] = {name: sum(row["recording"] == name for row in rows)
                                for name in sorted({row["recording"] for row in rows})}
    summary["per_category"] = {name: sum(row["category"] == name for row in rows)
                               for name in sorted({row["category"] for row in rows})}
    payload = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "trial_group": "transitive" if args.transitive_only else "all",
               "eligibility": "main; not unsuitable; nonblank saved transcription; status ok; exactly one valid onset; need help included",
               "summary": summary, "sources": sources, "trials": rows}
    prefix = "transitive_" if args.transitive_only else ""
    (output_dir / f"{prefix}speech_onset_latency_data.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
