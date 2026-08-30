"""Preregistered Stage 3F native-grid opto-fMRI source-RDM analysis."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import struct
import time

import numpy as np
import requests
from scipy.stats import spearmanr


DOI = "10.5281/zenodo.15718273"
ARCHIVE_URL = "https://zenodo.org/records/15718273/files/Opto-fMRI.Egg?download=1"
SITES = ("MOp", "MOs", "SSp-bfd", "VISp", "RSP", "VISarl")
DEVELOPMENT = {
    "Thy1": ("Thy1-sub05", "Thy1-sub08", "Thy1-sub09", "Thy1-sub10", "Thy1-sub07", "Thy1-sub06"),
    "VGAT": ("VGAT-sub07", "VGAT-sub08", "VGAT-sub05", "VGAT-sub02", "VGAT-sub03", "VGAT-sub09"),
}


def select_development_entries(manifest: list[dict[str, object]]) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for subjects in DEVELOPMENT.values():
        for subject in subjects:
            for site in SITES:
                prefix = f"{subject}/func_{site}/"
                rows = [
                    row
                    for row in manifest
                    if str(row["filename"]).startswith(prefix)
                    and str(row["filename"]).endswith(".nii.gz")
                ]
                rows.sort(key=lambda row: int(PurePosixPath(str(row["filename"])).name.removesuffix(".nii.gz")))
                if len(rows) < 5:
                    raise ValueError(f"fewer than five trials: {subject} {site}")
                selected.extend(rows[:5])
    return selected


def _download_one(entry: dict[str, object], root: Path, retries: int = 8) -> dict[str, object]:
    relative = PurePosixPath(str(entry["filename"])).as_posix()
    destination = root.joinpath(*PurePosixPath(relative).parts)
    expected = int(entry["file_length"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == expected:
        return {"filename": relative, "size": expected, "cached": True}
    part = destination.with_suffix(destination.suffix + ".part")
    start = int(entry["data_offset"])
    end = start + expected - 1
    for attempt in range(1, retries + 1):
        try:
            with requests.get(
                ARCHIVE_URL,
                headers={"Range": f"bytes={start}-{end}"},
                stream=True,
                timeout=(15, 120),
            ) as response:
                if response.status_code == 429:
                    delay = float(response.headers.get("Retry-After", attempt))
                    time.sleep(max(delay, attempt))
                    continue
                response.raise_for_status()
                if response.status_code != 206:
                    raise RuntimeError(f"range request returned {response.status_code}")
                digest = hashlib.sha256()
                written = 0
                with part.open("wb") as output:
                    for chunk in response.iter_content(1 << 20):
                        if chunk:
                            output.write(chunk)
                            digest.update(chunk)
                            written += len(chunk)
                if written != expected:
                    raise IOError(f"short range: {written} != {expected}")
                part.replace(destination)
                return {
                    "filename": relative,
                    "size": expected,
                    "sha256": digest.hexdigest(),
                    "cached": False,
                }
        except (requests.RequestException, OSError, RuntimeError):
            if attempt == retries:
                raise
            time.sleep(float(attempt))
    raise RuntimeError(f"unreachable download failure: {relative}")


def download_development(
    manifest_path: Path,
    output_root: Path,
    workers: int = 4,
) -> list[dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = select_development_entries(manifest)
    records: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_download_one, entry, output_root): entry for entry in entries}
        for index, future in enumerate(as_completed(futures), 1):
            record = future.result()
            records.append(record)
            print(f"[{index}/{len(entries)}] {record['filename']}", flush=True)
    records.sort(key=lambda row: str(row["filename"]))
    return records


def load_nifti(path: Path) -> np.ndarray:
    with gzip.open(path, "rb") as stream:
        payload = stream.read()
    if len(payload) < 352:
        raise ValueError(f"truncated NIfTI: {path}")
    endian = "<" if struct.unpack_from("<I", payload, 0)[0] == 348 else ">"
    if struct.unpack_from(f"{endian}I", payload, 0)[0] != 348:
        raise ValueError(f"invalid NIfTI header: {path}")
    dims = struct.unpack_from(f"{endian}8h", payload, 40)
    shape = tuple(int(value) for value in dims[1 : dims[0] + 1])
    datatype = struct.unpack_from(f"{endian}h", payload, 70)[0]
    dtype_map = {2: "u1", 4: "i2", 8: "i4", 16: "f4", 64: "f8"}
    if datatype not in dtype_map:
        raise ValueError(f"unsupported NIfTI datatype {datatype}: {path}")
    offset = int(struct.unpack_from(f"{endian}f", payload, 108)[0])
    dtype = np.dtype(endian + dtype_map[datatype])
    count = math.prod(shape)
    data = np.frombuffer(payload, dtype=dtype, count=count, offset=offset).reshape(shape, order="F")
    slope = struct.unpack_from(f"{endian}f", payload, 112)[0] or 1.0
    intercept = struct.unpack_from(f"{endian}f", payload, 116)[0]
    return np.asarray(data, dtype=np.float32) * slope + intercept


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    left -= left.mean()
    right -= right.mean()
    denom = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denom) if denom else 0.0


def response_rdms(odd: np.ndarray, even: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pairs = list(itertools.combinations(range(len(SITES)), 2))
    odd_rdm = np.array([1.0 - _pearson(odd[i], odd[j]) for i, j in pairs])
    even_rdm = np.array([1.0 - _pearson(even[i], even[j]) for i, j in pairs])
    cross = np.array(
        [
            1.0 - 0.5 * (_pearson(odd[i], even[j]) + _pearson(even[i], odd[j]))
            for i, j in pairs
        ]
    )
    return odd_rdm, even_rdm, cross


def subject_rdm(subject: str, root: Path) -> dict[str, object]:
    odd_maps: list[np.ndarray] = []
    even_maps: list[np.ndarray] = []
    baseline_maps: list[np.ndarray] = []
    raw_by_site: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    for site in SITES:
        files = sorted(
            (root / subject / f"func_{site}").glob("*.nii.gz"),
            key=lambda path: int(path.name.removesuffix(".nii.gz")),
        )[:5]
        if len(files) != 5:
            raise ValueError(f"expected five downloaded trials: {subject} {site}")
        rows = []
        for path in files:
            data = load_nifti(path)
            if data.shape != (96, 48, 18, 120):
                raise ValueError(f"unexpected shape {data.shape}: {path}")
            baseline = data[..., :40].mean(axis=3)
            response = data[..., 40:80].mean(axis=3)
            baseline_maps.append(baseline)
            rows.append((baseline, response))
        raw_by_site[site] = rows

    subject_baseline = np.mean(baseline_maps, axis=0)
    positive = subject_baseline[subject_baseline > 0]
    if not len(positive):
        raise ValueError(f"no positive baseline voxels: {subject}")
    threshold = 0.20 * float(np.percentile(positive, 95))
    mask = subject_baseline > threshold
    for site in SITES:
        maps = []
        for baseline, response in raw_by_site[site]:
            percent = -100.0 * (response[mask] - baseline[mask]) / baseline[mask]
            maps.append(np.asarray(percent, dtype=np.float32))
        odd_maps.append(np.mean([maps[0], maps[2], maps[4]], axis=0))
        even_maps.append(np.mean([maps[1], maps[3]], axis=0))
    odd = np.stack(odd_maps)
    even = np.stack(even_maps)
    odd_rdm, even_rdm, cross = response_rdms(odd, even)
    reliability = float(spearmanr(odd_rdm, even_rdm).statistic)
    return {
        "subject": subject,
        "genotype": subject.split("-", 1)[0],
        "mask_voxels": int(mask.sum()),
        "repeat_reliability": reliability,
        "odd_rdm": odd_rdm.tolist(),
        "even_rdm": even_rdm.tolist(),
        "cross_half_rdm": cross.tolist(),
    }


def exact_signflip_p(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    observed = float(values.mean())
    exceed = 0
    total = 1 << len(values)
    for bits in range(total):
        signs = np.array([1.0 if bits & (1 << index) else -1.0 for index in range(len(values))])
        exceed += float(np.mean(values * signs)) >= observed - 1e-12
    return exceed / total


def _loo_scores(vectors: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    within = np.empty(len(vectors))
    cross = np.empty(len(vectors))
    for index in range(len(vectors)):
        same = vectors[(labels == labels[index]) & (np.arange(len(vectors)) != index)]
        other = vectors[labels != labels[index]]
        within[index] = spearmanr(vectors[index], same.mean(axis=0)).statistic
        cross[index] = spearmanr(vectors[index], other.mean(axis=0)).statistic
    return within, cross


def analyze_subject_rdms(subjects: list[dict[str, object]]) -> dict[str, object]:
    labels = np.array([str(row["genotype"]) for row in subjects])
    vectors = np.array([row["cross_half_rdm"] for row in subjects], dtype=float)
    reliabilities = np.array([row["repeat_reliability"] for row in subjects], dtype=float)
    within, cross = _loo_scores(vectors, labels)
    reliability_gate = {}
    within_gate = {}
    for genotype in ("Thy1", "VGAT"):
        rel = reliabilities[labels == genotype]
        scores = within[labels == genotype]
        reliability_gate[genotype] = {
            "median": float(np.median(rel)),
            "signflip_p": exact_signflip_p(rel),
            "passed": bool(np.median(rel) >= 0.30 and exact_signflip_p(rel) <= 0.05),
        }
        within_gate[genotype] = {
            "scores": scores.tolist(),
            "median": float(np.median(scores)),
            "signflip_p": exact_signflip_p(scores),
            "passed": bool(np.median(scores) >= 0.30 and exact_signflip_p(scores) <= 0.05),
        }

    cross_p = exact_signflip_p(cross)
    common = bool(
        all(row["passed"] for row in reliability_gate.values())
        and all(row["passed"] for row in within_gate.values())
        and np.median(cross) >= 0.30
        and cross_p <= 0.05
    )
    observed_d = float(np.mean(within - cross))
    combinations = list(itertools.combinations(range(len(vectors)), len(vectors) // 2))
    exceed = 0
    for first in combinations:
        permuted = np.full(len(vectors), "B", dtype="U1")
        permuted[list(first)] = "A"
        perm_within, perm_cross = _loo_scores(vectors, permuted)
        exceed += float(np.mean(perm_within - perm_cross)) >= observed_d - 1e-12
    switch_p = exceed / len(combinations)
    switching = bool(
        not common
        and all(row["passed"] for row in reliability_gate.values())
        and all(row["passed"] for row in within_gate.values())
        and observed_d >= 0.20
        and switch_p <= 0.05
    )
    if common:
        status = "COMMON_SOURCE_RELATION_GEOMETRY_CANDIDATE"
    elif switching:
        status = "STATE_SWITCHING_SOURCE_RELATION_GEOMETRY_CANDIDATE"
    else:
        status = "STATE_RELATION_GEOMETRY_NOT_ESTABLISHED"
    return {
        "status": status,
        "reliability_gate": reliability_gate,
        "within_condition_gate": within_gate,
        "cross_condition_scores": cross.tolist(),
        "cross_condition_median": float(np.median(cross)),
        "cross_condition_signflip_p": cross_p,
        "within_minus_cross_mean": observed_d,
        "switching_permutation_p": switch_p,
        "claim_ceiling": "native-grid source-response relationship geometry",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    download = sub.add_parser("download")
    download.add_argument("--manifest", type=Path, required=True)
    download.add_argument("--output-root", type=Path, required=True)
    download.add_argument("--receipt", type=Path, required=True)
    download.add_argument("--workers", type=int, default=4)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--input-root", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "download":
        records = download_development(args.manifest, args.output_root, args.workers)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        return

    subject_rows = []
    for genotype in ("Thy1", "VGAT"):
        for subject in DEVELOPMENT[genotype]:
            print(f"analyzing {subject}", flush=True)
            subject_rows.append(subject_rdm(subject, args.input_root))
    result = analyze_subject_rdms(subject_rows)
    result["subjects"] = subject_rows
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
