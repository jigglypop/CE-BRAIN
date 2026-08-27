"""Development analysis: model-free population autocorrelation and bin-width filtering.

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Every timescale estimate in chapters 11-16 came from the eigenvalues of a
ridge-regularised operator, so it inherits the shrinkage.  This script avoids
fitting entirely: it bins spikes at 10 ms, computes each unit's count
autocorrelation, averages across units weighted by firing rate, and reports the
resulting curve together with its local maxima.

It also evaluates the boxcar transfer function sin(pi f T)/(pi f T) of a
counting window of width T at the theta frequency measured from this session's
local field potential, which is what makes the 100 ms choice of chapters 11-16
consequential.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import h5py
import numpy as np
import requests

DANDISET = "001701"
VERSION = "0.260120.0303"
ASSET_ID = "3f3d0b16-9b3e-42ac-a5e6-327829df1116"
EXPECTED_SIZE = 12_967_760
EXPECTED_SHA256 = "5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3"

BIN_SECONDS = 0.01
MAX_LAG = 100
MIN_TRAIN_RATE_HZ = 0.1
BIN_WIDTHS_TO_EVALUATE = (0.002, 0.01, 0.025, 0.05, 0.1, 0.2)
THETA_BAND = (6.0, 10.0)

HERE = Path(__file__).resolve().parent


def jsonable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def resolve_asset() -> tuple[Path, dict, bool]:
    cached = os.environ.get("CE_DANDI_001701_CACHE")
    if cached:
        path = Path(cached)
        if path.exists() and path.stat().st_size == EXPECTED_SIZE:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == EXPECTED_SHA256:
                return path, {"source": "verified_cache", "sha256": digest, "bytes": path.stat().st_size}, False
    api = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/{ASSET_ID}/"
    meta = requests.get(api, timeout=60)
    meta.raise_for_status()
    url = meta.json()["contentUrl"][0]
    handle, name = tempfile.mkstemp(suffix=".nwb")
    os.close(handle)
    path = Path(name)
    digest = hashlib.sha256()
    received = 0
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with path.open("wb") as sink:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    sink.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
    actual = digest.hexdigest()
    if received != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"receipt mismatch: bytes={received}, sha256={actual}")
    return path, {"source": "download", "sha256": actual, "bytes": received, "asset_api": api}, True


def welch(signal: np.ndarray, fs: float, nperseg: int) -> tuple[np.ndarray, np.ndarray]:
    window = np.hanning(nperseg)
    step = nperseg // 2
    power = np.zeros(nperseg // 2 + 1)
    segments = 0
    for lo in range(0, signal.size - nperseg + 1, step):
        block = (signal[lo : lo + nperseg] - signal[lo : lo + nperseg].mean()) * window
        power += np.abs(np.fft.rfft(block)) ** 2
        segments += 1
    power /= segments * (window ** 2).sum() * fs
    return np.fft.rfftfreq(nperseg, 1 / fs), power


def boxcar_response(frequency: float, width: float) -> float:
    x = math.pi * frequency * width
    return abs(math.sin(x) / x) if x else 1.0


def main() -> None:
    path, receipt, temporary = resolve_asset()
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            fs = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            trace = lfp["data"][:, 0].astype(np.float64)
            stop = start + trace.size / fs
            spike_times = nwb["units/spike_times"][:]
            spike_index = nwb["units/spike_times_index"][:]

        frequency, power = welch(trace, fs, 2048)
        band = (frequency >= THETA_BAND[0]) & (frequency <= THETA_BAND[1])
        theta_peak = float(frequency[band][np.argmax(power[band])])

        n_bins = int(math.floor((stop - start) / BIN_SECONDS))
        boundary = start + int(0.5 * n_bins) * BIN_SECONDS
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)
        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size), dtype=np.float32)
        prefix = np.empty(spike_index.size)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            times = spike_times[a:b]
            counts[:, unit] = np.histogram(times, bins=edges)[0]
            prefix[unit] = np.searchsorted(times, boundary)
        counts = counts[:, (prefix / (boundary - start)) >= MIN_TRAIN_RATE_HZ].astype(np.float64)

        centred = counts - counts.mean(axis=0)
        variance = np.maximum((centred * centred).mean(axis=0), 1e-12)
        weight = counts.mean(axis=0)
        weight = weight / weight.sum()
        autocorrelation = np.array([
            float((weight * ((centred[:-k] * centred[k:]).mean(axis=0) / variance)).sum())
            for k in range(1, MAX_LAG + 1)
        ])
        lags_ms = (np.arange(1, MAX_LAG + 1) * BIN_SECONDS * 1000).tolist()
        peaks = [
            i for i in range(1, MAX_LAG - 1)
            if autocorrelation[i] > autocorrelation[i - 1] and autocorrelation[i] > autocorrelation[i + 1] and autocorrelation[i] > 0.02
        ]
        peak_lags = [(i + 1) * BIN_SECONDS * 1000 for i in peaks]
        spacing = np.diff(peak_lags).tolist()

        report = {
            "track": "DEVELOPMENT_ONLY",
            "bin_seconds": BIN_SECONDS,
            "retained_units": int(counts.shape[1]),
            "lfp_theta_peak_hz": theta_peak,
            "lags_ms": lags_ms,
            "population_autocorrelation": autocorrelation.tolist(),
            "argmax_lag_ms": lags_ms[int(np.argmax(autocorrelation))],
            "local_maxima_lags_ms": peak_lags,
            "local_maximum_spacing_ms": spacing,
            "implied_frequencies_hz": [1000.0 / s for s in spacing if s > 0],
            "boxcar_response_at_theta": {
                f"{width:g}s": {
                    "amplitude_kept": boxcar_response(theta_peak, width),
                    "power_kept": boxcar_response(theta_peak, width) ** 2,
                    "first_null_hz": 1.0 / width,
                }
                for width in BIN_WIDTHS_TO_EVALUATE
            },
            "theta_period_ms": 1000.0 / theta_peak,
            "claim_ceiling": "Development measurement on a consumed asset; not a result about the recording family.",
            "source_receipt": receipt,
        }
        (HERE / "development-autocorrelation.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(f"theta peak {theta_peak:.2f} Hz, period {1000 / theta_peak:.1f} ms")
        print(f"autocorrelation argmax at lag {report['argmax_lag_ms']:.0f} ms")
        print(f"local maxima at {peak_lags[:6]} ms, spacing {spacing[:5]} ms")
        for width, entry in report["boxcar_response_at_theta"].items():
            print(f"  bin {width}: amplitude kept {100 * entry['amplitude_kept']:.2f}%, first null {entry['first_null_hz']:.1f} Hz")
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
