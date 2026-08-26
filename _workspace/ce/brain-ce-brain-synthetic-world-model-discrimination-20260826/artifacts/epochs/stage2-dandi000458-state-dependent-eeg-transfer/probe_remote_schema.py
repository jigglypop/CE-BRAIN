from __future__ import annotations

import json

import fsspec
import h5py
import numpy as np


URL = "https://dandiarchive.s3.amazonaws.com/blobs/a36/7d4/a367d440-e803-4476-aac4-31b78904f5fe"


def scalar(value: object) -> object:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (h5py.Reference, h5py.RegionReference)):
        return repr(value)
    if isinstance(value, np.ndarray):
        return [scalar(item) for item in value]
    return value


def dataset_summary(dataset: h5py.Dataset) -> dict[str, object]:
    values = dataset[...]
    if values.ndim == 1 and values.size <= 100:
        encoded = [scalar(value) for value in values]
    elif values.ndim == 1 and values.size <= 1000:
        unique, counts = np.unique(values, return_counts=True)
        encoded = {
            "count": int(values.size),
            "unique_counts": {
                str(scalar(value)): int(count) for value, count in zip(unique, counts, strict=True)
            },
        }
    else:
        encoded = {"shape": list(values.shape), "dtype": str(values.dtype)}
    return {
        "values": encoded,
        "attrs": {key: scalar(value) for key, value in dataset.attrs.items()},
    }


def main() -> None:
    targets = [
        "acquisition/ElectricalSeriesEEG/electrodes",
        "general/extracellular_ephys/electrodes/id",
        "general/extracellular_ephys/electrodes/location",
        "general/extracellular_ephys/electrodes/is_data_valid",
        "intervals/trials/estim_current",
        "intervals/trials/behavioral_epoch",
        "intervals/trials/is_valid",
        "intervals/trials/stimulus_description",
        "intervals/trials/estim_target_region",
    ]
    report: dict[str, object] = {}
    with fsspec.open(URL, "rb", block_size=8 * 1024 * 1024, cache_type="blockcache") as stream:
        with h5py.File(stream, "r") as nwb:
            report["intervals/trials/__keys__"] = sorted(nwb["intervals/trials"].keys())
            trials = nwb["intervals/trials"]
            ids = trials["id"][...]
            states = np.asarray([scalar(value) for value in trials["behavioral_epoch"][...]])
            currents = np.asarray([scalar(value) for value in trials["estim_current"][...]])
            valid = trials["is_valid"][...].astype(bool)
            report["registered_split_counts"] = {
                f"{state}/{current}/{split_name}": int(
                    np.sum(
                        (states == state)
                        & (currents == current)
                        & valid
                        & ((ids % 2) == parity)
                    )
                )
                for state in ("awake", "isoflurane")
                for current in ("20", "50", "100")
                for split_name, parity in (("development", 0), ("confirmation", 1))
            }
            for target in targets:
                if target in nwb:
                    report[target] = dataset_summary(nwb[target])
                else:
                    report[target] = {"missing": True}
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
