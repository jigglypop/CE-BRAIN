"""Schema gate for the DANDI 001612 photostimulation candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect_nwb(path: Path) -> dict[str, object]:
    import h5py

    with h5py.File(path, "r") as nwb:
        processing = nwb.get("processing/ophys")
        fluorescence = []
        roi_counts = []
        frame_counts = []
        if processing is not None:
            for name, group in processing.items():
                if name.startswith("Fluorescence_"):
                    fluorescence.append(name)
                    traces = group.get("ROITrace/data")
                    if traces is not None and len(traces.shape) == 2:
                        frame_counts.append(int(traces.shape[0]))
                        roi_counts.append(int(traces.shape[1]))

        presentation = nwb.get("stimulus/presentation")
        stimulus_series = sorted(presentation.keys()) if presentation is not None else []
        intervals = sorted(nwb["intervals"].keys()) if "intervals" in nwb else []
        names: list[str] = []
        nwb.visit(names.append)
        explicit_target_paths = sorted(
            name
            for name in names
            if "target" in name.lower() or "photostim" in name.lower()
        )
        eligible = bool(
            fluorescence
            and stimulus_series
            and explicit_target_paths
            and intervals
        )
        return {
            "status": (
                "STAGE3_MULTISOURCE_APPARATUS_ELIGIBLE"
                if eligible
                else "STAGE3_DANDI001612_TARGET_TIMING_NOT_IDENTIFIABLE"
            ),
            "fluorescence_planes": len(fluorescence),
            "receiver_rois": sum(roi_counts),
            "frame_counts": sorted(set(frame_counts)),
            "stimulus_series": stimulus_series,
            "interval_tables": intervals,
            "explicit_target_paths": explicit_target_paths,
            "claim_ceiling": "apparatus schema only",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("nwb", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect_nwb(args.nwb)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
