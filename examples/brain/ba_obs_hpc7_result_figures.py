"""Read-only figures for the frozen H6 endpoint result.

The script deliberately validates the exact result-byte hash before extracting
the already-computed descriptive endpoint summaries.  It neither recomputes
endpoints nor reads the source witness.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PREDECESSOR = Path("_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825")
RECOVERY = Path("_workspace/ce/brain-human-hippocampal-theta-endpoint-recovery-20260825")
RESULT = PREDECESSOR / "artifacts" / "raw_result.json"
OUT = RECOVERY / "artifacts"
RESULT_SHA256 = "cd3aaff53b1db1dba97f92812f529f066c870ac968bdd7a27f0b9ad4c0a8585d"
REFS = ("clinical", "bipolar")
ESTIMANDS = ("trial_mean", "mean_waveform")
WINDOWS = ("early", "late", "prestim")
SUBJECTS = {"TS": ("p16", "p17", "p18", "p19"), "PB": ("p17", "p19", "p20", "UC004", "UC005")}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result() -> dict:
    if sha256(RESULT) != RESULT_SHA256:
        raise ValueError("STOP: frozen raw_result.json SHA-256 mismatch")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if result.get("status") != "RAW_COMPLETE" or set(result.get("analysis", ())) != set(REFS):
        raise ValueError("STOP: unexpected frozen result schema")
    return result


def rows(result: dict) -> list[dict]:
    output = []
    for ref in REFS:
        for estimand in ESTIMANDS:
            for window in WINDOWS:
                endpoint = result["analysis"][ref][estimand][window]
                bootstrap = endpoint["bootstrap"]
                output.append(
                    {
                        "ref": ref,
                        "estimand": estimand,
                        "window": window,
                        "D": float(endpoint["D"]),
                        "low": float(bootstrap[0]),
                        "high": float(bootstrap[1]),
                        "Pr_positive": float(bootstrap[2]),
                        "paired": float(endpoint["paired_p17_p19"]),
                    }
                )
    return output


FONT = ImageFont.load_default()


def save_figure(image: Image.Image, path: Path) -> None:
    tmp = path.with_name(path.stem + ".tmp.png")
    image.save(tmp, format="PNG", optimize=True)
    tmp.replace(path)


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, fill: str = "black") -> None:
    draw.text((int(xy[0]), int(xy[1])), value, font=FONT, fill=fill)


def scale(value: float, lo: float, hi: float, start: float, end: float) -> float:
    return start + (value - lo) * (end - start) / (hi - lo)


def forest(summary: list[dict], path: Path) -> None:
    image = Image.new("RGB", (1960, 940), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (555, 24), "Endpoint differences with descriptive 2.5-97.5% bootstrap intervals")
    lo = min(row["low"] for row in summary)
    hi = max(row["high"] for row in summary)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad
    for panel, ref in enumerate(REFS):
        subset = [r for r in summary if r["ref"] == ref]
        left, right = 140 + panel * 925, 910 + panel * 925
        top, bottom = 130, 835
        text(draw, ((left + right) / 2 - 55, 76), ref.capitalize() + " reference")
        zero = scale(0, lo, hi, left, right)
        draw.line((zero, top, zero, bottom), fill="#666666", width=2)
        for index, row in enumerate(subset):
            y = top + 36 + index * 70
            primary = (ref, row["estimand"], row["window"]) == ("clinical", "trial_mean", "late")
            color = "#b2182b" if primary else "#2166ac"
            draw.line((scale(row["low"], lo, hi, left, right), y, scale(row["high"], lo, hi, left, right), y), fill=color, width=4)
            x = scale(row["D"], lo, hi, left, right)
            radius = 10 if primary else 7
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
            text(draw, (left, y + 12), f"{row['estimand'].replace('_', ' ')} - {row['window']}")
        for tick in range(5):
            value = lo + tick * (hi - lo) / 4
            x = scale(value, lo, hi, left, right)
            draw.line((x, bottom, x, bottom + 8), fill="black", width=1)
            text(draw, (x - 17, bottom + 12), f"{value:.0f}")
        text(draw, ((left + right) / 2 - 100, bottom + 42), "TS minus PB difference (µV)")
    text(draw, (145, 875), "Red filled point: predeclared primary")
    save_figure(image, path)


def participant_deltas(result: dict, path: Path) -> None:
    image = Image.new("RGB", (1960, 940), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (510, 24), "Participant deltas for the primary endpoint and bipolar counterpart")
    colors = {"TS": "#2166ac", "PB": "#ef8a62"}
    values_all = [value for ref in REFS for key in ("ts_deltas", "pb_deltas") for value in result["analysis"][ref]["trial_mean"]["late"][key]]
    lo, hi = min(values_all), max(values_all)
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    for panel, ref in enumerate(REFS):
        left, right, top, bottom = 180 + panel * 915, 900 + panel * 915, 130, 810
        endpoint = result["analysis"][ref]["trial_mean"]["late"]
        text(draw, ((left + right) / 2 - 85, 76), ref.capitalize() + ": trial mean, late window")
        zero = scale(0, lo, hi, bottom, top)
        draw.line((left, zero, right, zero), fill="#666666", width=2)
        for protocol, key, xpos in (("TS", "ts_deltas", 0), ("PB", "pb_deltas", 1)):
            values = endpoint[key]
            subjects = SUBJECTS[protocol]
            center = left + (right - left) * (0.30 if xpos == 0 else 0.70)
            for index, (value, subject) in enumerate(zip(values, subjects)):
                x = center + (index - (len(values) - 1) / 2) * 28
                y = scale(value, lo, hi, bottom, top)
                outline = "black" if subject in {"p17", "p19"} else colors[protocol]
                draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=colors[protocol], outline=outline, width=2)
                text(draw, (x + 10, y - 7), subject)
        for tick in range(5):
            value = lo + tick * (hi - lo) / 4
            y = scale(value, lo, hi, bottom, top)
            draw.line((left - 8, y, left, y), fill="black")
            if panel == 0:
                text(draw, (left - 55, y - 5), f"{value:.0f}")
        text(draw, (left + (right - left) * .30 - 8, bottom + 24), "TS")
        text(draw, (left + (right - left) * .70 - 8, bottom + 24), "PB")
    text(draw, (76, 440), "Post minus pre delta (µV)")
    text(draw, (1320, 870), "Blue=TS  Orange=PB  Black outline=shared p17/p19")
    save_figure(image, path)


def write_csv(summary: list[dict], path: Path) -> None:
    tmp = path.with_name(path.stem + ".tmp.csv")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("ref", "estimand", "window", "D", "low", "high", "Pr_positive", "paired"))
        writer.writeheader()
        writer.writerows(summary)
    tmp.replace(path)


def main() -> int:
    result = load_result()
    summary = rows(result)
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = (OUT / "endpoint_forest.png", OUT / "primary_participant_deltas.png", OUT / "endpoint_summary.csv")
    forest(summary, outputs[0])
    participant_deltas(result, outputs[1])
    write_csv(summary, outputs[2])
    for output in outputs:
        print(f"{output.as_posix()} sha256={sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
