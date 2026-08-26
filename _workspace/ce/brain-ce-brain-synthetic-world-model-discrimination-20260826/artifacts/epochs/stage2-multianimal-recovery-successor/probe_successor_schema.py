"""Stream only NWB metadata needed to admit a Stage 2 successor asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fsspec
import h5py
import numpy as np


def decode(value: object) -> object:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.generic):
        return value.item()
    return value


def summarize_column(group: h5py.Group, name: str) -> dict[str, object]:
    if name not in group:
        return {"missing": True}
    values = np.asarray([decode(value) for value in group[name][...]])
    unique, counts = np.unique(values, return_counts=True)
    return {
        "count": int(values.size),
        "unique_counts": {
            str(decode(value)): int(count)
            for value, count in zip(unique, counts, strict=True)
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report: dict[str, object] = {
        "schema": "ce.stage2.successor-schema-probe.v1",
        "asset_id": args.asset_id,
        "path": args.path,
        "sha256": args.sha256,
        "url": args.url,
    }
    with fsspec.open(
        args.url,
        "rb",
        block_size=8 * 1024 * 1024,
        cache_type="blockcache",
    ) as stream:
        with h5py.File(stream, "r") as nwb:
            report["root_keys"] = sorted(nwb.keys())
            acquisition = nwb.get("acquisition")
            report["acquisition_keys"] = (
                sorted(acquisition.keys()) if isinstance(acquisition, h5py.Group) else []
            )
            eeg = nwb.get("acquisition/ElectricalSeriesEEG")
            if isinstance(eeg, h5py.Group) and "data" in eeg and "timestamps" in eeg:
                data = eeg["data"]
                timestamps = np.asarray(eeg["timestamps"][...], dtype=np.float64)
                deltas = np.diff(timestamps)
                median_delta = float(np.median(deltas))
                gap_indices = np.flatnonzero(deltas > 1.5 * median_delta)
                ordinary = np.delete(deltas, gap_indices)
                report["eeg"] = {
                    "data_shape": list(data.shape),
                    "data_dtype": str(data.dtype),
                    "conversion_volts_per_count": float(
                        data.attrs.get("conversion", np.nan)
                    ),
                    "timestamp_count": int(timestamps.size),
                    "timestamps_finite": bool(np.all(np.isfinite(timestamps))),
                    "timestamps_strictly_increasing": bool(np.all(deltas > 0)),
                    "sampling_rate_hz": 1.0 / median_delta,
                    "gap_indices": gap_indices.tolist(),
                    "gap_ratios": (deltas[gap_indices] / median_delta).tolist(),
                    "max_ordinary_relative_jitter": float(
                        np.max(np.abs(ordinary / median_delta - 1.0))
                    ),
                }
                if "electrodes" in eeg:
                    region = eeg["electrodes"]
                    table_ref = region.attrs.get("table")
                    report["series_electrode_rows"] = np.asarray(
                        region[...], dtype=np.int64
                    ).tolist()
                    report["series_electrode_table"] = (
                        nwb[table_ref].name if table_ref is not None else None
                    )
            electrodes = nwb.get("general/extracellular_ephys/electrodes")
            report["electrode_columns"] = (
                sorted(electrodes.keys()) if isinstance(electrodes, h5py.Group) else []
            )
            report["electrode_count"] = (
                int(electrodes["id"].shape[0])
                if isinstance(electrodes, h5py.Group) and "id" in electrodes
                else 0
            )
            if isinstance(electrodes, h5py.Group) and "is_data_valid" in electrodes:
                valid_rows = np.flatnonzero(
                    np.asarray(electrodes["is_data_valid"][...], dtype=bool)
                )
                report["valid_electrode_rows"] = valid_rows.tolist()
            trials = nwb.get("intervals/trials")
            if not isinstance(trials, h5py.Group):
                report["trials"] = {"missing": True}
            else:
                report["trial_columns"] = sorted(trials.keys())
                report["trial_count"] = int(trials["id"].shape[0])
                report["behavioral_epoch"] = summarize_column(
                    trials, "behavioral_epoch"
                )
                report["estim_current"] = summarize_column(trials, "estim_current")
                report["estim_target_region"] = summarize_column(
                    trials, "estim_target_region"
                )
                report["is_valid"] = summarize_column(trials, "is_valid")
                report["stimulus_description"] = summarize_column(
                    trials, "stimulus_description"
                )
                ids = np.asarray(trials["id"][...], dtype=np.int64)
                states = np.asarray(
                    [decode(value) for value in trials["behavioral_epoch"][...]]
                )
                valid = np.asarray(trials["is_valid"][...], dtype=bool)
                report["registered_split_counts"] = {
                    f"{state}/{split}": int(
                        np.sum(valid & (states == state) & ((ids % 2) == parity))
                    )
                    for state in ("awake", "isoflurane", "recovery")
                    for split, parity in (("development", 0), ("confirmation", 1))
                }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
