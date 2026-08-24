"""BA-OBS-DISC1: staged discovery of an observed human CCEP response kernel.

There are deliberately no tuning arguments.  D0 is the only structural-model
selection stage.  D1/D2/D3 can only refit that structure on already consumed
stages and predict the next sealed pair set.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import sys
import tempfile
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, lsq_linear
from scipy.stats import rankdata


RUN = Path(__file__).resolve().parents[1]
DATA = Path("data/external/ba_obs_disc1_ds003708")
OLD_DATA = Path("data/external/ba_obs_id3_ds003708")
BASE = DATA / "derivatives/preprocessed/sub-01/ses-ieeg01/ieeg"
OLD_BASE = OLD_DATA / "derivatives/preprocessed/sub-01/ses-ieeg01/ieeg"
PREDECESSOR = RUN.parent / "brain-human-ccep-restricted-active-response-20260824"

FS, NCH, NWIN = 2048, 89, 1537
SIZE = 2_899_637_088
ETAG = "9832a1868bff527620c3cec91df4bb81-3"
VERSION = "ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4"
URL = (
    "https://s3.amazonaws.com/openneuro.org/ds003708/derivatives/preprocessed/"
    "sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg"
    f"?versionId={VERSION}"
)
FLOOR = 1e-6
SITES = (
    "LPS2-LPS3", "LTG10-LTG11", "LTG11-LTG12", "LTG13-LTG14",
    "LTG15-LTG16", "LTG17-LTG18", "LTG19-LTG20", "LTG1-LTG2",
    "LTG20-LTG21", "LTG22-LTG23", "LTG23-LTG24", "LTG25-LTG26",
    "LTG26-LTG27", "LTG27-LTG28", "LTG28-LTG29", "LTG29-LTG30",
    "LTG2-LTG3", "LTG30-LTG31", "LTG31-LTG32", "LTG3-LTG4",
    "LTG4-LTG5", "LTG5-LTG6", "LTG6-LTG7", "LTG9-LTG10",
)
LOCK = {
    "events.tsv": "f4767c8d6f25a641e706d5bee7dfc928b9ca4501c54bf33b67e96dc5562a9aab",
    "channels.tsv": "baf23675a6dd235a7a37549ec16ddcd9e0cebd5b7fa26348b0dcb0f5f82a1318",
    "electrodes.tsv": "6606045c8881d7ed1ef15990c9160e2884bec8789b59aeb9bd5dba709a4b6aec",
    "ieeg.vhdr": "5551a8ca58fe16f489956981ab6437ae65c041891273c08fbea13dfab70cef4a",
    "ieeg.vmrk": "a2e09a018d1359aaf1e8d0bdb65586ec0e4f9611ab9455497d83b3b7b7cfca24",
    "README": "24b59bb2a00971fe9e56a0cef2e9a1368fc86a0a9637e4f395c368e8bae7c908",
}
REL = {
    "events.tsv": "sub-01_ses-ieeg01_task-ccep_run-01_events.tsv",
    "channels.tsv": "sub-01_ses-ieeg01_task-ccep_run-01_channels.tsv",
    "electrodes.tsv": "sub-01_ses-ieeg01_space-MNI152NLin6Sym_electrodes.tsv",
    "ieeg.vhdr": "sub-01_ses-ieeg01_task-ccep_run-01_ieeg.vhdr",
    "ieeg.vmrk": "sub-01_ses-ieeg01_task-ccep_run-01_ieeg.vmrk",
}
EXPECTED_SPLIT_HASH = {
    "D0": "0fbddb902c6fa5cfa3e50aed4ba4e4f4f3b1f64c1241cc75a3bbb88775fbdb13",
    "D1": "c172ca78a7b36776cf8f79879a846af61945717afce1f30cf77efe0b88406751",
    "D2": "4c82cc45b0b2b51e4e8882a94cd9812811886b650045d4ada86d214bf4b1a5a6",
    "D3": "340b36c86fe61dd35d55f5cc31057b6db1aa183cceaafd5f19d3a6d92d11b2c3",
}
EXPECTED_MANIFEST_HASH = "16bcdeb0c86b5fb7894ad6c766d1ef390e36b040e47d70b0d38ec953e04edb42"
PC1 = np.array([0.2520471813, -0.7312327918, -0.6338539441])
OFF = np.arange(-1024, 513)
MS = OFF * 1000.0 / FS
BM = (OFF >= -1024) & (OFF <= -11)
BINS = ((10.0, 18.0), (18.0, 30.0), (30.0, 50.0), (50.0, 80.0), (80.0, 120.0))
PRE_BINS = ((-250.0, -242.0), (-242.0, -230.0), (-230.0, -210.0),
            (-210.0, -180.0), (-180.0, -140.0))
TIMES = np.array([14.0, 24.0, 40.0, 65.0, 100.0]) / 50.0


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(obj, *, sort_keys: bool = True) -> bytes:
    return json.dumps(obj, sort_keys=sort_keys, separators=(",", ":")).encode()


def code_sha() -> str:
    return sha(Path(__file__).read_bytes())


def rng(*parts) -> np.random.Generator:
    seed = int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:16], "little")
    return np.random.default_rng(seed)


def dump(name: str, obj: dict) -> str:
    path = RUN / "artifacts" / name
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return sha(path.read_bytes())


def load(name: str) -> dict:
    return json.loads((RUN / "artifacts" / name).read_text(encoding="utf-8"))


def require(name: str, status: str = "PASS", current_code: bool = True) -> dict:
    result = load(name)
    if result.get("status") != status:
        raise RuntimeError(f"DOWNSTREAM_BARRIER:{name}:{result.get('status')}")
    if current_code and result.get("code_sha256") not in (None, code_sha()):
        raise RuntimeError(f"CODE_IDENTITY_STOP:{name}")
    return result


def _copy_metadata() -> dict[str, Path]:
    for key, rel in REL.items():
        src, dst = OLD_BASE / rel, BASE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
    readme = DATA / "derivatives/preprocessed/README"
    readme.parent.mkdir(parents=True, exist_ok=True)
    if not readme.exists():
        readme.write_bytes((OLD_DATA / "derivatives/preprocessed/README").read_bytes())
    return {key: (readme if key == "README" else BASE / REL[key]) for key in LOCK}


def metadata() -> dict:
    files = _copy_metadata()
    bad = [key for key, path in files.items() if not path.exists() or sha(path.read_bytes()) != LOCK[key]]
    if bad:
        raise RuntimeError("SOURCE_IDENTITY_STOP:metadata:" + ",".join(bad))
    events = list(csv.DictReader(files["events.tsv"].open(encoding="utf-8"), delimiter="\t"))
    markers = [line for line in files["ieeg.vmrk"].read_text(encoding="utf-8").splitlines()
               if re.match(r"^Mk\d+=", line)]
    if len(events) != 425 or len(markers) != 425:
        raise RuntimeError("SOURCE_METADATA_ALIGNMENT_STOP:marker_event_count")
    positions = np.array([int(line.split(",")[2]) - 1 for line in markers])
    starts = np.array([int(float(row["sample_start"])) for row in events])
    delta = positions - starts
    if (delta == -1).sum() != 201 or (delta == 0).sum() != 224 or not np.all((delta == -1) | (delta == 0)):
        raise RuntimeError("SOURCE_METADATA_ALIGNMENT_STOP:anchor")

    electrode_rows = list(csv.DictReader(files["electrodes.tsv"].open(encoding="utf-8"), delimiter="\t"))
    xyz = {}
    for row in electrode_rows:
        try:
            xyz[row["name"]] = np.array([float(row["x"]), float(row["y"]), float(row["z"])])
        except ValueError:
            pass
    centers = {site: (xyz[site.split("-")[0]] + xyz[site.split("-")[1]]) / 2 for site in SITES}

    calibration = []
    for i, a in enumerate(SITES):
        for b in SITES[i + 1:]:
            if set(a.split("-")) & set(b.split("-")):
                continue
            distance = float(np.linalg.norm(centers[a] - centers[b]))
            if distance < 15.0:
                continue
            old_byte = hashlib.sha256(f"ds003708-v1.0.2|{a}|{b}".encode()).digest()[0]
            if old_byte <= 152:
                calibration.append({"a": a, "b": b, "distance": distance})
    if len(calibration) != 151:
        raise RuntimeError("SOURCE_METADATA_ALIGNMENT_STOP:calibration_count")

    ranked = sorted(calibration, key=lambda p: (p["distance"], p["a"], p["b"]))
    strata = [ranked[:38], ranked[38:76], ranked[76:114], ranked[114:151]]
    for i, group in enumerate(strata):
        strata[i] = sorted(
            group,
            key=lambda p: hashlib.sha256(
                f"BA-OBS-DISC1::ds003708-v1.0.2::{p['a']}::{p['b']}".encode()
            ).digest(),
        )
    quota = {
        "D0": [6, 6, 6, 6],
        "D1": [12, 12, 12, 12],
        "D2": [10, 10, 10, 9],
        "D3": [10, 10, 10, 10],
    }
    cursors = [0, 0, 0, 0]
    stages = {stage: [] for stage in quota}
    for stage, counts in quota.items():
        for stratum, count in enumerate(counts):
            start = cursors[stratum]
            for local_rank, original in enumerate(strata[stratum][start:start + count]):
                pair = dict(original)
                pair.update(
                    stage=stage,
                    stratum=stratum,
                    stage_stratum_rank=local_rank,
                    key=pair["a"] + "|" + pair["b"],
                )
                stages[stage].append(pair)
            cursors[stratum] += count
    if tuple(len(stages[k]) for k in ("D0", "D1", "D2", "D3")) != (24, 48, 39, 40):
        raise RuntimeError("SPLIT_STOP:counts")
    split_lists = {stage: [[p["a"], p["b"]] for p in pairs] for stage, pairs in stages.items()}
    split_hashes = {stage: sha(canonical(pairs, sort_keys=False)) for stage, pairs in split_lists.items()}
    if split_hashes != EXPECTED_SPLIT_HASH:
        raise RuntimeError("SPLIT_STOP:canonical_hash:" + json.dumps(split_hashes, sort_keys=True))
    manifest = {
        "method": "distance-quartile-then-salted-hash",
        "stratum_sizes": [38, 38, 38, 37],
        "quota": quota,
        "splits": split_lists,
    }
    manifest_hash = sha(canonical(manifest, sort_keys=True))
    if manifest_hash != EXPECTED_MANIFEST_HASH:
        raise RuntimeError("SPLIT_STOP:manifest_hash:" + manifest_hash)

    halves = {site: [0, 0] for site in SITES}
    seen = {site: 0 for site in SITES}
    eligible = []
    for event_id, row in enumerate(events):
        source = row["electrical_stimulation_site"]
        if row["status"] == "good" and row["electrical_stimulation_current"] == "6.0 mA" and source in seen:
            half = seen[source] % 2
            halves[source][half] += 1
            seen[source] += 1
            eligible.append((event_id, row))
    if len(eligible) != 255 or any(min(counts) < 5 or max(counts) > 9 for counts in halves.values()):
        raise RuntimeError("SOURCE_METADATA_ALIGNMENT_STOP:eligible_halves")
    return {
        "files": files,
        "events": events,
        "markers": markers,
        "centers": centers,
        "stages": stages,
        "halves": halves,
        "eligible": eligible,
        "split_hashes": split_hashes,
        "manifest": manifest,
        "manifest_hash": manifest_hash,
    }


def split_receipt() -> dict:
    meta = metadata()
    distance = {}
    for stage, pairs in meta["stages"].items():
        values = np.array([p["distance"] for p in pairs])
        distance[stage] = {"min": float(values.min()), "median": float(np.median(values)), "max": float(values.max())}
    result = {
        "status": "PASS",
        "code_sha256": code_sha(),
        "stage_counts": {k: len(v) for k, v in meta["stages"].items()},
        "stage_sha256": meta["split_hashes"],
        "manifest_sha256": meta["manifest_hash"],
        "distance_mm": distance,
        "halves": meta["halves"],
    }
    dump("split-receipt.json", result)
    return result


def _predecessor_range_hashes() -> dict[int, str]:
    path = PREDECESSOR / "artifacts/real-development-receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    result = {int(row["event"]): row["sha256"] for row in receipt["ranges"]}
    if len(result) != 255:
        raise RuntimeError("SOURCE_IDENTITY_STOP:predecessor_range_manifest")
    return result


def _source_head() -> dict:
    request = urllib.request.Request(URL, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        headers = {k.lower(): v.strip('"') for k, v in response.headers.items()}
    expected = {"content-length": str(SIZE), "etag": ETAG, "x-amz-version-id": VERSION}
    if {key: headers.get(key) for key in expected} != expected:
        raise RuntimeError("SOURCE_IDENTITY_STOP:HEAD")
    return expected


def _verify_range(payload: bytes, start: int, end: int, event_id: int, expected_hash: str) -> str:
    if len(payload) != end - start + 1:
        raise RuntimeError(f"SOURCE_IDENTITY_STOP:range_length:{event_id}")
    digest = sha(payload)
    if digest != expected_hash:
        raise RuntimeError(f"SOURCE_IDENTITY_STOP:range_hash:{event_id}")
    decoded = np.frombuffer(payload, dtype="<f4")
    if decoded.size != NWIN * NCH or not np.all(np.isfinite(decoded)):
        raise RuntimeError(f"SOURCE_IDENTITY_STOP:range_decode:{event_id}")
    return digest


def source_cache() -> dict:
    fixture = require("fixture-receipt.json")
    split = split_receipt()
    meta = metadata()
    head = _source_head()
    old_hashes = _predecessor_range_hashes()
    anchors = [int(line.split(",")[2]) - 1 for line in meta["markers"]]
    cache_dir = DATA / "epoch-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    def acquire(item):
        event_id, event = item
        anchor = anchors[event_id]
        start = (anchor - 1024) * NCH * 4
        end = (anchor + 513) * NCH * 4 - 1
        path = cache_dir / f"{event_id:03d}.bin"
        transport = "CACHE_VERIFIED"
        if path.exists():
            payload = path.read_bytes()
        else:
            request = urllib.request.Request(
                URL,
                headers={"Range": f"bytes={start}-{end}", "If-Match": f'"{ETAG}"'},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
                headers = {k.lower(): v.strip('"') for k, v in response.headers.items()}
                if (
                    response.status != 206
                    or headers.get("content-range") != f"bytes {start}-{end}/{SIZE}"
                    or headers.get("etag") != ETAG
                    or headers.get("x-amz-version-id") != VERSION
                ):
                    raise RuntimeError(f"SOURCE_IDENTITY_STOP:range_headers:{event_id}")
            path.write_bytes(payload)
            transport = "HTTP_206_VERSION_LOCKED"
        digest = _verify_range(payload, start, end, event_id, old_hashes[event_id])
        return {
            "event": event_id,
            "source": event["electrical_stimulation_site"],
            "start": start,
            "end": end,
            "count": len(payload),
            "sha256": digest,
            "content_range": f"bytes {start}-{end}/{SIZE}",
            "etag": ETAG,
            "version_id": VERSION,
            "cache_file": path.name,
            "transport": transport,
        }

    with ThreadPoolExecutor(max_workers=12) as executor:
        rows = sorted(executor.map(acquire, meta["eligible"]), key=lambda row: row["event"])
    essential = [{k: row[k] for k in ("event", "start", "end", "count", "sha256")} for row in rows]
    result = {
        "status": "PASS",
        "code_sha256": code_sha(),
        "fixture_receipt_sha256": sha((RUN / "artifacts/fixture-receipt.json").read_bytes()),
        "split_receipt_sha256": sha((RUN / "artifacts/split-receipt.json").read_bytes()),
        "source_head": head,
        "eligible_epochs": len(rows),
        "ranges": rows,
        "range_manifest_sha256": sha(canonical(essential)),
        "endpoint_values_computed": False,
    }
    if fixture["code_sha256"] != result["code_sha256"] or split["code_sha256"] != result["code_sha256"]:
        raise RuntimeError("CODE_IDENTITY_STOP:source_cache_inputs")
    dump("source-cache-receipt.json", result)
    return result


def cached_store() -> dict[str, list[np.ndarray]]:
    receipt = require("source-cache-receipt.json")
    meta = metadata()
    event_by_id = meta["events"]
    store = {site: [[], []] for site in SITES}
    seen = {site: 0 for site in SITES}
    for row in sorted(receipt["ranges"], key=lambda item: item["event"]):
        payload = (DATA / "epoch-cache" / row["cache_file"]).read_bytes()
        _verify_range(payload, row["start"], row["end"], row["event"], row["sha256"])
        if row["content_range"] != f"bytes {row['start']}-{row['end']}/{SIZE}":
            raise RuntimeError("SOURCE_IDENTITY_STOP:cache_content_range")
        source = event_by_id[row["event"]]["electrical_stimulation_site"]
        half = seen[source] % 2
        seen[source] += 1
        epoch = np.frombuffer(payload, dtype="<f4").reshape(NWIN, NCH).T.astype(np.float64) * 0.1
        store[source][half].append(epoch)
    if any(len(store[s][h]) != meta["halves"][s][h] for s in SITES for h in (0, 1)):
        raise RuntimeError("APPARATUS_OR_EVOCATION_STOP:trial_allocation")
    return {site: [np.asarray(parts[0]), np.asarray(parts[1])] for site, parts in store.items()}


def _mask(interval: tuple[float, float], last_inclusive: bool = False) -> np.ndarray:
    lo, hi = interval
    return (MS >= lo) & (MS <= hi if last_inclusive else MS < hi)


def endpoints(stage: str) -> list[dict]:
    store = cached_store()
    meta = metadata()
    channels = list(csv.DictReader(meta["files"]["channels.tsv"].open(encoding="utf-8"), delimiter="\t"))
    channel_index = {row["name"]: i for i, row in enumerate(channels)}
    post_masks = [_mask(interval, i == len(BINS) - 1) for i, interval in enumerate(BINS)]
    pre_masks = [_mask(interval) for interval in PRE_BINS]
    output = []
    for pair in meta["stages"][stage]:
        for direction, (target, source) in enumerate(((pair["a"], pair["b"]), (pair["b"], pair["a"]))):
            indices = [channel_index[name] for name in target.split("-")]
            for half in (0, 1):
                trials = store[source][half].copy()
                trials -= trials[:, :, BM].mean(axis=2, keepdims=True)
                contact_trials = trials[:, indices, :]
                contact_scale = np.std(contact_trials[:, :, BM], axis=(0, 2), ddof=0)
                bipolar_trials = contact_trials[:, 0, :] - contact_trials[:, 1, :]
                bipolar_scale = float(np.std(bipolar_trials[:, BM], ddof=0))
                if (
                    not np.all(np.isfinite(contact_scale))
                    or np.any(contact_scale <= 0)
                    or not np.isfinite(bipolar_scale)
                    or bipolar_scale <= 0
                ):
                    raise RuntimeError("APPARATUS_OR_EVOCATION_STOP:baseline_scale")
                contact_mean = contact_trials.mean(axis=0) / contact_scale[:, None]
                bipolar_mean = bipolar_trials.mean(axis=0) / bipolar_scale
                values = {"mean": [], "bip": [], "pre_mean": [], "pre_bip": []}
                for mask in post_masks:
                    values["mean"].append(float(np.sqrt(np.mean(contact_mean[:, mask] ** 2))))
                    values["bip"].append(float(np.sqrt(np.mean(bipolar_mean[mask] ** 2))))
                for mask in pre_masks:
                    values["pre_mean"].append(float(np.sqrt(np.mean(contact_mean[:, mask] ** 2))))
                    values["pre_bip"].append(float(np.sqrt(np.mean(bipolar_mean[mask] ** 2))))
                flat = np.array(sum(values.values(), []), dtype=float)
                if flat.size != 20 or not np.all(np.isfinite(flat)) or np.any(flat < 0):
                    raise RuntimeError("APPARATUS_OR_EVOCATION_STOP:endpoint")
                output.append({
                    "stage": stage,
                    "pair": pair["key"],
                    "fold": pair["stage_stratum_rank"] if stage == "D0" else None,
                    "direction": direction,
                    "target": target,
                    "source": source,
                    "half": half,
                    "distance": pair["distance"],
                    "dx": (meta["centers"][target] - meta["centers"][source]).tolist(),
                    "values": values,
                })
    expected = len(meta["stages"][stage]) * 4
    if len(output) != expected:
        raise RuntimeError("APPARATUS_OR_EVOCATION_STOP:endpoint_count")
    return output


def apparatus_gate(endpoint_rows: list[dict]) -> tuple[dict, bool]:
    result = {}
    passed = True
    for mode in ("mean", "bip"):
        keyed = {}
        post, pre = [], []
        for row in endpoint_rows:
            key = (row["pair"], row["direction"])
            keyed.setdefault(key, {})[row["half"]] = row["values"][mode]
            post.extend(row["values"][mode])
            pre.extend(row["values"]["pre_" + mode])
        if len(keyed) != 48 or any(set(halves) != {0, 1} for halves in keyed.values()):
            raise RuntimeError("APPARATUS_OR_EVOCATION_STOP:directed_half_map")
        a = np.array([value for key in sorted(keyed) for value in keyed[key][0]])
        b = np.array([value for key in sorted(keyed) for value in keyed[key][1]])
        rho = float(np.corrcoef(rankdata(a, method="average"), rankdata(b, method="average"))[0, 1])
        ratio = float(np.median(post) / max(np.median(pre), FLOOR))
        ok = bool(np.isfinite(rho) and rho >= 0.40 and ratio >= 1.25)
        result[mode] = {
            "pooled_cross_half_spearman": rho,
            "post_over_prestim": ratio,
            "defined_directed_edges": len(keyed),
            "post_values": len(post),
            "passed": ok,
        }
        passed &= ok
    return result, passed


NAMES = (
    "B0", "CABLE", "H-Q1", "H-Q2", "H-Q3", "H-Q4", "H-Q8", "H-Q16",
    "H-QFREE", "H-PQFREE", "H-DELAY", "H-ANISO", "H-DIR-PC",
    "H-ANISO-DIR", "BIEXP",
)
FIXED_Q = {"H-Q1": 1.0, "H-Q2": 2.0, "H-Q3": 3.0, "H-Q4": 4.0,
           "H-Q8": 8.0, "H-Q16": 16.0}
CONVEX = {"B0", "CABLE", *FIXED_Q, "H-QFREE", "H-DIR-PC"}
NONLINEAR = set(NAMES) - CONVEX


def huber_values(residual: np.ndarray) -> np.ndarray:
    absolute = np.abs(residual)
    return np.where(absolute <= 0.5, 0.5 * residual * residual, 0.5 * (absolute - 0.25))


def mean_huber(residual: np.ndarray) -> float:
    return float(np.mean(huber_values(np.asarray(residual, dtype=float))))


def rowify(endpoint_rows: list[dict], mode: str) -> list[dict]:
    rows = []
    for endpoint in endpoint_rows:
        for bin_id, value in enumerate(endpoint["values"][mode]):
            rows.append({
                key: endpoint[key]
                for key in ("stage", "pair", "fold", "direction", "target", "source", "half",
                            "distance", "dx")
            } | {"bin": bin_id, "z": math.log(value + FLOOR)})
    return rows


def _geometry(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t = np.array([TIMES[row["bin"]] for row in rows], dtype=float)
    r = np.array([row["distance"] / 50.0 for row in rows], dtype=float)
    dx = np.array([row["dx"] for row in rows], dtype=float) / 50.0
    axis = dx @ PC1
    return t, r, dx, axis


def model_npar(name: str) -> int:
    if name == "B0": return 3
    if name == "CABLE": return 4
    if name in FIXED_Q: return 3
    if name == "H-QFREE": return 4
    if name in ("H-PQFREE", "H-DELAY", "H-DIR-PC", "BIEXP"): return 5
    if name == "H-ANISO": return 6
    if name == "H-ANISO-DIR": return 7
    raise KeyError(name)


def _spec(name: str, rows: list[dict]) -> dict | None:
    wide = 50.0
    positive = 50.0
    if name == "B0":
        return {"names": ["beta0", "beta_logt", "beta_t"], "lo": [-30, -wide, -wide],
                "hi": [30, wide, wide], "structural": []}
    if name == "CABLE":
        return {"names": ["beta0", "beta_logt", "beta_t", "a"],
                "lo": [-30, -wide, -wide, 0], "hi": [30, wide, wide, positive], "structural": [3]}
    if name in FIXED_Q:
        return {"names": ["beta0", "kappa", "lambda"], "lo": [-30, 0, 0],
                "hi": [30, positive, positive], "structural": [1, 2]}
    if name == "H-QFREE":
        return {"names": ["beta0", "q", "kappa", "lambda"], "lo": [-30, 0, 0, 0],
                "hi": [30, 20, positive, positive], "structural": [1, 2, 3]}
    if name == "H-PQFREE":
        return {"names": ["beta0", "q", "kappa", "lambda", "p"],
                "lo": [-30, 0, 0, 0, 0.5], "hi": [30, 20, positive, positive, 4],
                "structural": [1, 2, 3, 4]}
    if name in ("H-DELAY", "BIEXP"):
        t, r, _, _ = _geometry(rows)
        positive_r = r > 0
        delta_hi = min(0.2, float(np.min(t[positive_r] / r[positive_r])) * (1 - 1e-6))
        if not np.isfinite(delta_hi) or delta_hi <= 1e-5:
            return None
        if name == "H-DELAY":
            return {"names": ["beta0", "q", "kappa", "lambda", "delta"],
                    "lo": [-30, 0, 0, 0, 0], "hi": [30, 20, positive, positive, delta_hi],
                    "structural": [1, 2, 3, 4]}
        return {"names": ["log_A", "a", "delta", "theta_r", "theta_fraction"],
                "lo": [-30, 0, 0, 0.01, 0.001], "hi": [30, positive, delta_hi, 3.9, 0.999],
                "structural": [1, 2, 3, 4]}
    if name == "H-ANISO":
        return {"names": ["beta0", "q", "kappa", "lambda", "g_x", "g_y"],
                "lo": [-30, 0, 0, 0, -1.5, -1.5], "hi": [30, 20, positive, positive, 1.5, 1.5],
                "structural": [1, 2, 3, 4, 5]}
    if name == "H-DIR-PC":
        return {"names": ["beta0", "q", "kappa", "lambda", "gamma"],
                "lo": [-30, 0, 0, 0, -2], "hi": [30, 20, positive, positive, 2],
                "structural": [1, 2, 3, 4]}
    if name == "H-ANISO-DIR":
        return {"names": ["beta0", "q", "kappa", "lambda", "g_x", "g_y", "gamma"],
                "lo": [-30, 0, 0, 0, -1.5, -1.5, -2],
                "hi": [30, 20, positive, positive, 1.5, 1.5, 2],
                "structural": [1, 2, 3, 4, 5, 6]}
    raise KeyError(name)


def _predict(name: str, theta: np.ndarray, rows: list[dict]) -> np.ndarray | None:
    t, r, dx, axis = _geometry(rows)
    if name == "B0":
        return theta[0] + theta[1] * np.log(t) + theta[2] * t
    if name == "CABLE":
        return theta[0] + theta[1] * np.log(t) + theta[2] * t - theta[3] * r
    if name in FIXED_Q:
        q = FIXED_Q[name]
        return theta[0] - 0.5 * q * np.log(t) - theta[1] * r * r / t - theta[2] * t
    if name == "H-QFREE":
        return theta[0] - 0.5 * theta[1] * np.log(t) - theta[2] * r * r / t - theta[3] * t
    if name == "H-PQFREE":
        return theta[0] - 0.5 * theta[1] * np.log(t) - theta[2] * r ** theta[4] / t - theta[3] * t
    if name == "H-DELAY":
        shifted = t - theta[4] * r
        if np.any(shifted <= 0): return None
        return theta[0] - 0.5 * theta[1] * np.log(shifted) - theta[2] * r * r / shifted - theta[3] * shifted
    if name in ("H-ANISO", "H-ANISO-DIR"):
        diagonal = np.exp([theta[4], theta[5], -theta[4] - theta[5]])
        metric_r2 = np.sum(dx * dx * diagonal[None, :], axis=1)
        result = theta[0] - 0.5 * theta[1] * np.log(t) - theta[2] * metric_r2 / t - theta[3] * t
        if name == "H-ANISO-DIR": result = result + theta[6] * axis
        return result
    if name == "H-DIR-PC":
        return theta[0] - 0.5 * theta[1] * np.log(t) - theta[2] * r * r / t - theta[3] * t + theta[4] * axis
    if name == "BIEXP":
        shifted = t - theta[2] * r
        if np.any(shifted <= 0): return None
        theta_r = theta[3]
        theta_d = theta_r + theta[4] * (4.0 - theta_r)
        pulse = np.exp(-shifted / theta_d) - np.exp(-shifted / theta_r)
        if np.any(pulse <= 0): return None
        energy = FLOOR + np.exp(theta[0] - theta[1] * r) * pulse
        return np.log(energy)
    raise KeyError(name)


def _convex_design(name: str, rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    t, r, _, axis = _geometry(rows)
    offset = np.zeros(len(rows))
    if name == "B0": return np.column_stack((np.ones(len(rows)), np.log(t), t)), offset
    if name == "CABLE": return np.column_stack((np.ones(len(rows)), np.log(t), t, -r)), offset
    if name in FIXED_Q:
        offset = -0.5 * FIXED_Q[name] * np.log(t)
        return np.column_stack((np.ones(len(rows)), -r * r / t, -t)), offset
    if name == "H-QFREE":
        return np.column_stack((np.ones(len(rows)), -0.5 * np.log(t), -r * r / t, -t)), offset
    if name == "H-DIR-PC":
        return np.column_stack((np.ones(len(rows)), -0.5 * np.log(t), -r * r / t, -t, axis)), offset
    raise KeyError(name)


def _rank_condition(jacobian: np.ndarray) -> tuple[int, float]:
    singular = np.linalg.svd(jacobian, compute_uv=False)
    if singular.size == 0 or singular[0] <= 0: return 0, math.inf
    rank = int(np.sum(singular > singular[0] * 1e-8))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else math.inf
    return rank, condition


def _boundary_parameters(theta: np.ndarray, spec: dict) -> list[str]:
    lo, hi = np.asarray(spec["lo"], float), np.asarray(spec["hi"], float)
    names = spec["names"]
    boundary = []
    for index in spec["structural"]:
        span = hi[index] - lo[index]
        distance = min(theta[index] - lo[index], hi[index] - theta[index]) / span
        if distance <= 1e-4: boundary.append(names[index])
    return boundary


def _fit_convex(name: str, rows: list[dict], y: np.ndarray, spec: dict) -> dict:
    X, offset = _convex_design(name, rows)
    target = y - offset
    lo, hi = np.asarray(spec["lo"], float), np.asarray(spec["hi"], float)
    weights = np.ones(len(y))
    theta = None
    for _ in range(40):
        root = np.sqrt(weights)
        solved = lsq_linear(X * root[:, None], target * root, bounds=(lo, hi),
                            lsmr_tol="auto", max_iter=500)
        if not solved.success or not np.all(np.isfinite(solved.x)):
            return {"valid": False, "reason": "CONVEX_SOLVER_FAIL", "npar": len(lo)}
        change = math.inf if theta is None else float(np.max(np.abs(solved.x - theta)))
        theta = solved.x
        residual = y - (offset + X @ theta)
        weights = np.minimum(1.0, 0.5 / np.maximum(np.abs(residual), 1e-12))
        if change < 1e-10: break
    prediction = _predict(name, theta, rows)
    rank, condition = _rank_condition(X)
    boundary = _boundary_parameters(theta, spec)
    valid = prediction is not None and rank == len(theta) and condition <= 1e8 and not boundary
    return {
        "valid": bool(valid), "reason": "PASS" if valid else "IDENTIFIABILITY_STOP",
        "params": theta.tolist(), "param_names": spec["names"], "npar": len(theta),
        "loss": mean_huber(y - prediction) if prediction is not None else math.inf,
        "jacobian_rank": rank, "condition": condition, "boundary": boundary,
        "multistart": "CONVEX_UNIQUE",
    }


def _starts(name: str, rows: list[dict], y: np.ndarray, spec: dict) -> list[np.ndarray]:
    lo, hi = np.asarray(spec["lo"], float), np.asarray(spec["hi"], float)
    signature = sha(canonical([(r["pair"], r["half"], r["bin"]) for r in rows], sort_keys=False))
    generator = rng("BA-OBS-DISC1", "multistart", name, signature)
    starts = []
    for index in range(12):
        fraction = 0.1 + 0.8 * generator.random(len(lo))
        start = lo + fraction * (hi - lo)
        start[0] = np.clip(float(np.median(y)) + generator.normal(0, 0.5), lo[0] + 1e-5, hi[0] - 1e-5)
        if "q" in spec["names"]:
            q_index = spec["names"].index("q")
            start[q_index] = [1, 2, 3, 4, 8, 16, 0.5, 6, 10, 12, 18, 5][index]
        if "p" in spec["names"]:
            start[spec["names"].index("p")] = np.linspace(0.7, 3.8, 12)[index]
        starts.append(start)
    return starts


def _fit_nonlinear(name: str, rows: list[dict], y: np.ndarray, spec: dict) -> dict:
    lo, hi = np.asarray(spec["lo"], float), np.asarray(spec["hi"], float)
    solved = []
    for start in _starts(name, rows, y, spec):
        def residual(theta):
            prediction = _predict(name, theta, rows)
            return np.full(len(y), 1e6) if prediction is None else prediction - y
        try:
            answer = least_squares(
                residual, start, bounds=(lo, hi), loss="huber", f_scale=0.5,
                max_nfev=400, ftol=1e-9, xtol=1e-9, gtol=1e-9,
            )
        except (ValueError, FloatingPointError):
            continue
        prediction = _predict(name, answer.x, rows)
        if answer.success and prediction is not None and np.all(np.isfinite(prediction)):
            solved.append((mean_huber(y - prediction), answer, prediction))
    solved.sort(key=lambda item: item[0])
    if len(solved) < 3:
        return {"valid": False, "reason": "MULTISTART_FEWER_THAN_THREE", "npar": len(lo)}
    best3 = solved[:3]
    relative = (best3[-1][0] - best3[0][0]) / max(abs(best3[0][0]), 1e-12)
    prediction_rms = max(float(np.sqrt(np.mean((item[2] - best3[0][2]) ** 2))) for item in best3[1:])
    best = best3[0][1]
    rank, condition = _rank_condition(best.jac)
    boundary = _boundary_parameters(best.x, spec)
    valid = relative <= 1e-4 and prediction_rms <= 1e-3 and rank == len(best.x) and condition <= 1e8 and not boundary
    return {
        "valid": bool(valid), "reason": "PASS" if valid else "IDENTIFIABILITY_STOP",
        "params": best.x.tolist(), "param_names": spec["names"], "npar": len(best.x),
        "loss": best3[0][0], "jacobian_rank": rank, "condition": condition,
        "boundary": boundary, "multistart_count": len(solved),
        "best3_relative_loss_spread": relative, "best3_prediction_rms": prediction_rms,
    }


def fit_model(name: str, rows: list[dict]) -> dict:
    y = np.array([row["z"] for row in rows], dtype=float)
    if len(rows) <= model_npar(name) or not np.all(np.isfinite(y)):
        return {"valid": False, "reason": "INSUFFICIENT_OR_NONFINITE", "npar": model_npar(name)}
    spec = _spec(name, rows)
    if spec is None:
        return {"valid": False, "reason": "INFEASIBLE_DELAY_DOMAIN", "npar": model_npar(name)}
    result = _fit_convex(name, rows, y, spec) if name in CONVEX else _fit_nonlinear(name, rows, y, spec)
    result["model"] = name
    return result


def predict_fit(fit: dict, rows: list[dict]) -> np.ndarray | None:
    if not fit.get("valid"): return None
    return _predict(fit["model"], np.asarray(fit["params"], float), rows)


def d0_folds(rows: list[dict]) -> list[set[str]]:
    pair_to_fold = {}
    for row in rows:
        if row["fold"] is None: raise RuntimeError("SPLIT_STOP:D0_fold_missing")
        pair_to_fold.setdefault(row["pair"], row["fold"])
        if pair_to_fold[row["pair"]] != row["fold"]: raise RuntimeError("SPLIT_STOP:pair_fold")
    folds = [{pair for pair, fold in pair_to_fold.items() if fold == index} for index in range(6)]
    if any(len(fold) != 4 for fold in folds) or len(set().union(*folds)) != 24:
        raise RuntimeError("SPLIT_STOP:D0_fold_counts")
    return folds


def _fit_summary(fit: dict) -> dict:
    keep = ("valid", "reason", "model", "params", "param_names", "npar", "loss",
            "jacobian_rank", "condition", "boundary", "multistart", "multistart_count",
            "best3_relative_loss_spread", "best3_prediction_rms")
    return {key: fit[key] for key in keep if key in fit}


def choose(endpoint_rows: list[dict]) -> tuple[str | None, dict]:
    results = {}
    for name in NAMES:
        model_result = {"valid": True, "npar": model_npar(name)}
        for mode in ("mean", "bip"):
            rows = rowify(endpoint_rows, mode)
            folds = d0_folds(rows)
            fold_losses, diagnostics = [], []
            for fold_id, held_pairs in enumerate(folds):
                crossed = []
                for fit_half, test_half in ((0, 1), (1, 0)):
                    train = [r for r in rows if r["pair"] not in held_pairs and r["half"] == fit_half]
                    test = [r for r in rows if r["pair"] in held_pairs and r["half"] == test_half]
                    fit = fit_model(name, train)
                    prediction = predict_fit(fit, test)
                    diagnostics.append({"fold": fold_id, "fit_half": fit_half, **_fit_summary(fit)})
                    if prediction is None:
                        model_result["valid"] = False
                        break
                    crossed.append(mean_huber(np.array([r["z"] for r in test]) - prediction))
                if not model_result["valid"]: break
                fold_losses.append(float(np.mean(crossed)))
            model_result[mode] = {"fold_loss": fold_losses, "fits": diagnostics}
            if not model_result["valid"]: break
        results[name] = model_result

    if not results["B0"]["valid"] or len(results["B0"]["bip"]["fold_loss"]) != 6:
        raise RuntimeError("FIT_STOP:B0_D0")
    for name, result in results.items():
        if not result["valid"]:
            result.update(I_bip=None, I_mean=None, fold_wins_bip=0)
            continue
        for mode in ("mean", "bip"):
            baseline = float(np.mean(results["B0"][mode]["fold_loss"]))
            loss = float(np.mean(result[mode]["fold_loss"]))
            result["I_" + mode] = (
                1.0 - loss / baseline if baseline > 1e-12
                else 0.0 if loss <= 1e-12 else -math.inf
            )
        result["fold_wins_bip"] = sum(
            a < b for a, b in zip(result["bip"]["fold_loss"], results["B0"]["bip"]["fold_loss"])
        )
    survivors = [
        name for name in NAMES if name != "B0" and results[name]["valid"]
        and results[name]["I_bip"] > 0 and results[name]["fold_wins_bip"] >= 4
    ]
    if not survivors: return None, results
    best = max(results[name]["I_bip"] for name in survivors)
    near = [name for name in survivors if best - results[name]["I_bip"] <= 0.01]
    winner = min(near, key=lambda name: (model_npar(name), name))
    return winner, results


def _source_loss_delta(test: list[dict], baseline_prediction: np.ndarray,
                       winner_prediction: np.ndarray) -> tuple[list[str], np.ndarray]:
    sources = sorted({row["source"] for row in test})
    y = np.array([row["z"] for row in test])
    values = []
    for source in sources:
        indices = np.array([i for i, row in enumerate(test) if row["source"] == source])
        base = mean_huber(y[indices] - baseline_prediction[indices])
        win = mean_huber(y[indices] - winner_prediction[indices])
        values.append(base - win)
    return sources, np.asarray(values)


def _permuted_rows(test: list[dict], order: np.ndarray) -> list[dict]:
    pairs = sorted({row["pair"] for row in test})
    forward = {}
    distance = {}
    for row in test:
        if row["direction"] == 0:
            forward[row["pair"]] = np.array(row["dx"], dtype=float)
            distance[row["pair"]] = row["distance"]
    if set(forward) != set(pairs): raise RuntimeError("PERMUTATION_STOP:forward_geometry")
    donor = {pair: pairs[int(order[i])] for i, pair in enumerate(pairs)}
    output = []
    for row in test:
        source_pair = donor[row["pair"]]
        dx = forward[source_pair] if row["direction"] == 0 else -forward[source_pair]
        output.append({**row, "distance": distance[source_pair], "dx": dx.tolist()})
    return output


def stage_gate(stage: str, endpoint_rows: list[dict], training_endpoints: list[dict], winner: str) -> tuple[dict, bool]:
    output = {}
    for mode in ("mean", "bip"):
        train, test = rowify(training_endpoints, mode), rowify(endpoint_rows, mode)
        fit_winner, fit_baseline = fit_model(winner, train), fit_model("B0", train)
        winner_prediction, baseline_prediction = predict_fit(fit_winner, test), predict_fit(fit_baseline, test)
        if winner_prediction is None or baseline_prediction is None:
            output[mode] = {"fit_stop": True, "winner_fit": _fit_summary(fit_winner),
                            "baseline_fit": _fit_summary(fit_baseline)}
            continue
        sources, delta = _source_loss_delta(test, baseline_prediction, winner_prediction)
        bootstrap_rng = rng("BA-OBS-DISC1", stage, mode, "source-cluster", 4096)
        bootstrap_index = bootstrap_rng.integers(0, len(sources), size=(4096, len(sources)))
        bootstrap = delta[bootstrap_index].mean(axis=1)
        observed = float(delta.mean())

        pairs = sorted({row["pair"] for row in test})
        permutation_rng = rng("BA-OBS-DISC1", stage, mode, "geometry-permutation", 1024)
        permutation_index = np.vstack([permutation_rng.permutation(len(pairs)) for _ in range(1024)])
        permuted_delta = []
        for order in permutation_index:
            permuted = _permuted_rows(test, order)
            permuted_prediction = predict_fit(fit_winner, permuted)
            if permuted_prediction is None:
                permuted_delta.append(-math.inf)
            else:
                _, values = _source_loss_delta(test, baseline_prediction, permuted_prediction)
                permuted_delta.append(float(values.mean()))
        p_geom = (1 + sum(value >= observed for value in permuted_delta)) / 1025.0
        ci = [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))]
        passed = bool(observed > 0 and ci[0] > 0 and p_geom <= 0.05)
        output[mode] = {
            "fit_stop": False, "mean_delta": observed, "source_delta": dict(zip(sources, delta.tolist())),
            "ci95": ci, "p_geom": p_geom, "n_source": len(sources), "passed": passed,
            "winner_fit": _fit_summary(fit_winner), "baseline_fit": _fit_summary(fit_baseline),
            "bootstrap_index_sha256": sha(np.ascontiguousarray(bootstrap_index).view(np.uint8).tobytes()),
            "permutation_index_sha256": sha(np.ascontiguousarray(permutation_index).view(np.uint8).tobytes()),
        }
    bipolar_pass = bool(not output["bip"].get("fit_stop", True) and output["bip"].get("passed", False))
    return output, bipolar_pass


def d0() -> dict:
    require("fixture-receipt.json")
    source = require("source-cache-receipt.json")
    endpoint_rows = endpoints("D0")
    apparatus, apparatus_ok = apparatus_gate(endpoint_rows)
    if not apparatus_ok:
        result = {
            "status": "APPARATUS_OR_EVOCATION_STOP", "code_sha256": code_sha(),
            "source_range_manifest_sha256": source["range_manifest_sha256"],
            "apparatus_gate": apparatus, "endpoints": endpoint_rows,
            "endpoint_records": len(endpoint_rows), "structure_selected": False,
        }
        dump("d0-receipt.json", result)
        return result
    winner, candidate_cv = choose(endpoint_rows)
    status = "PASS" if winner else "D0_NO_GEOMETRIC_EQUATION_SURVIVED"
    result = {
        "status": status, "code_sha256": code_sha(), "winner": winner,
        "source_range_manifest_sha256": source["range_manifest_sha256"],
        "apparatus_gate": apparatus, "candidate_cv": candidate_cv,
        "endpoints": endpoint_rows, "endpoint_records": len(endpoint_rows),
        "structure_selected": winner is not None,
        "claim_status": "EMPIRICAL_MODEL_SELECTION_ONLY_NOT_CONFIRMATION",
    }
    dump("d0-receipt.json", result)
    return result


def barrier_allows(stage: str, statuses: dict[str, str]) -> bool:
    required = {
        "D1": ("d0-receipt.json",),
        "D2": ("d0-receipt.json", "d1-receipt.json"),
        "D3": ("d0-receipt.json", "d1-receipt.json", "d2-receipt.json"),
    }[stage]
    return all(statuses.get(name) == "PASS" for name in required)


def enforce_barrier(stage: str, statuses: dict[str, str]) -> None:
    if not barrier_allows(stage, statuses):
        raise RuntimeError("DOWNSTREAM_BARRIER:" + stage)


def sequential(stage: str, prior_files: tuple[str, ...]) -> dict:
    d0_receipt = require("d0-receipt.json")
    if stage in ("D2", "D3"): require("d1-receipt.json")
    if stage == "D3": require("d2-receipt.json")
    prerequisite_statuses = {name: load(name).get("status") for name in prior_files}
    enforce_barrier(stage, prerequisite_statuses)
    winner = d0_receipt["winner"]
    training_endpoints = []
    prior_hashes = {}
    for name in prior_files:
        receipt = load(name)
        if receipt.get("status") != "PASS": raise RuntimeError("DOWNSTREAM_BARRIER:" + name)
        if receipt.get("code_sha256") != code_sha(): raise RuntimeError("CODE_IDENTITY_STOP:" + name)
        training_endpoints.extend(receipt["endpoints"])
        prior_hashes[name] = sha((RUN / "artifacts" / name).read_bytes())
    endpoint_rows = endpoints(stage)
    metrics, passed = stage_gate(stage, endpoint_rows, training_endpoints, winner)
    # Contact-mean is a reference diagnostic; only a bipolar fit stop blocks the primary route.
    fit_stop = metrics["bip"].get("fit_stop", False)
    status = "SEQUENTIAL_FIT_STOP" if fit_stop else "PASS" if passed else "SEQUENTIAL_BIPOLAR_GATE_FAIL"
    result = {
        "status": status, "code_sha256": code_sha(), "winner": winner, "metrics": metrics,
        "endpoints": endpoint_rows, "training_endpoint_records": len(training_endpoints),
        "new_endpoint_records": len(endpoint_rows), "prior_receipt_sha256": prior_hashes,
        "structure_changed_after_D0": False,
    }
    if stage == "D3":
        mean_pass = bool(metrics.get("mean", {}).get("passed", False))
        result["final_label"] = (
            "HELD_OUT_OBSERVED_KERNEL_PREDICTION_PASS_REFERENCE_CONCORDANT"
            if passed and mean_pass else
            "HELD_OUT_OBSERVED_KERNEL_PREDICTION_PASS_REFERENCE_SENSITIVE"
            if passed else "HELD_OUT_OBSERVED_KERNEL_PREDICTION_NOT_CONFIRMED"
        )
    dump(stage.lower() + "-receipt.json", result)
    return result


def _synthetic_endpoints(seed: int, kind: str) -> list[dict]:
    generator = rng("BA-OBS-DISC1", "synthetic", seed, kind)
    output = []
    distances = np.linspace(18.0, 76.0, 24)
    for pair_id, distance in enumerate(distances):
        angle = 2 * math.pi * pair_id / 24
        forward = np.array([math.cos(angle), math.sin(angle), 0.35 * math.sin(2 * angle)])
        forward = forward / np.linalg.norm(forward) * distance
        for direction in (0, 1):
            dx = forward if direction == 0 else -forward
            for half in (0, 1):
                r = distance / 50.0
                temporal = 0.4 + 0.25 * np.log(TIMES) - 0.12 * TIMES
                if kind == "heat":
                    z_bip = 1.2 - 2.0 * np.log(TIMES) - 0.8 * r * r / TIMES - 0.4 * TIMES
                    z_mean = z_bip + 0.02
                    noise = generator.normal(0, 0.005, 5)
                elif kind == "null":
                    pair_noise = generator.normal(0, 0.18, 5)
                    half_noise = generator.normal(0, 0.12, 5)
                    z_bip = temporal + pair_noise + half_noise
                    z_mean = temporal + generator.normal(0, 0.22, 5)
                    noise = np.zeros(5)
                elif kind == "common":
                    z_bip = temporal
                    z_mean = 1.0 - 2.0 * np.log(TIMES) - 0.7 * r * r / TIMES - 0.3 * TIMES
                    noise = np.zeros(5)
                else:
                    raise KeyError(kind)
                bip = np.exp(z_bip + noise)
                mean = np.exp(z_mean + noise)
                output.append({
                    "stage": "D0", "pair": f"P{pair_id:02d}", "fold": pair_id % 6,
                    "direction": direction, "target": f"T{pair_id:02d}",
                    "source": f"S{pair_id:02d}", "half": half, "distance": float(distance),
                    "dx": dx.tolist(),
                    "values": {"mean": mean.tolist(), "bip": bip.tolist(),
                               "pre_mean": (mean / 2).tolist(), "pre_bip": (bip / 2).tolist()},
                })
    return output


def _null_selection_flag(seed: int) -> int:
    """Top-level for Windows spawn; runs the unchanged D0 selection path."""
    winner, _ = choose(_synthetic_endpoints(7301 + seed, "null"))
    return int(winner is not None)


def fixtures() -> dict:
    split = split_receipt()
    if len(NAMES) != 15: raise RuntimeError("FIXTURE_STOP:candidate_count")
    heat_winner, heat_result = choose(_synthetic_endpoints(3708, "heat"))
    if heat_winner != "H-Q4" or heat_result["H-Q4"]["I_bip"] <= 0:
        raise RuntimeError("FIXTURE_STOP:heat_recovery:" + str(heat_winner))

    with ProcessPoolExecutor(max_workers=8) as executor:
        null_flags = list(executor.map(_null_selection_flag, range(256), chunksize=1))
    false_selection = int(sum(null_flags))
    if false_selection > 7:
        raise RuntimeError(f"STATISTICAL_FALSE_POSITIVE_STOP:{false_selection}/256")

    common_winner, common_result = choose(_synthetic_endpoints(9107, "common"))
    if common_winner is not None:
        raise RuntimeError("FIXTURE_STOP:common_reference_fooled_bipolar:" + common_winner)

    diagonal = np.exp([0.4, -0.2, -0.2])
    if not np.all(diagonal > 0) or not np.isclose(np.prod(diagonal), 1.0):
        raise RuntimeError("DIMENSIONLESS_OR_SPD_STOP")
    try:
        _verify_range(b"bad", 0, 4, -1, sha(b"bad"))
        raise RuntimeError("FIXTURE_STOP:wrong_length_accepted")
    except RuntimeError as error:
        if "range_length" not in str(error): raise
    try:
        _verify_range(b"good", 0, 3, -1, sha(b"wrong"))
        raise RuntimeError("FIXTURE_STOP:wrong_hash_accepted")
    except RuntimeError as error:
        if "range_hash" not in str(error): raise
    barrier_cases = {
        "D1_without_D0": ("D1", {}),
        "D2_after_failed_D1": ("D2", {"d0-receipt.json": "PASS", "d1-receipt.json": "FAIL"}),
        "D3_after_failed_D2": ("D3", {"d0-receipt.json": "PASS", "d1-receipt.json": "PASS", "d2-receipt.json": "FAIL"}),
    }
    barriers = {}
    with tempfile.TemporaryDirectory(prefix="ba_obs_disc1_barrier_") as temporary:
        root = Path(temporary)
        for label, (stage, statuses) in barrier_cases.items():
            target = root / (stage.lower() + "-receipt.json")
            try:
                enforce_barrier(stage, statuses)
                target.write_text("should-not-exist", encoding="utf-8")
            except RuntimeError as error:
                if "DOWNSTREAM_BARRIER" not in str(error): raise
            barriers[label] = {"exception": True, "receipt_absent": not target.exists()}
        if not all(item["exception"] and item["receipt_absent"] for item in barriers.values()):
            raise RuntimeError("FIXTURE_STOP:downstream_barrier")
    result = {
        "status": "PASS", "code_sha256": code_sha(),
        "split_receipt_sha256": sha((RUN / "artifacts/split-receipt.json").read_bytes()),
        "split_manifest_sha256": split["manifest_sha256"], "candidate_count": len(NAMES),
        "heat_generating_winner": heat_winner, "heat_generating_I_bip": heat_result["H-Q4"]["I_bip"],
        "null_geometric_false_selection": false_selection, "null_n": 256, "null_gate_max": 7,
        "common_reference_primary_winner": common_winner,
        "common_reference_bipolar_I": {name: value.get("I_bip") for name, value in common_result.items()},
        "dimensionless": {"x": "t/(50 ms)", "r": "ell/(50 mm)", "exp_log_arguments": True},
        "anisotropic_G_positive_det_one": True, "wrong_length_fail_closed": True,
        "wrong_hash_fail_closed": True,
        "downstream_barrier_fixture": barriers,
    }
    dump("fixture-receipt.json", result)
    return result


def check() -> dict:
    existing = {}
    for name in ("split-receipt.json", "fixture-receipt.json", "source-cache-receipt.json",
                 "d0-receipt.json", "d1-receipt.json", "d2-receipt.json", "d3-receipt.json"):
        path = RUN / "artifacts" / name
        if path.exists():
            receipt = load(name)
            if receipt.get("code_sha256") != code_sha(): raise RuntimeError("CODE_IDENTITY_STOP:" + name)
            existing[name] = receipt.get("status")
    order = ("d0-receipt.json", "d1-receipt.json", "d2-receipt.json", "d3-receipt.json")
    for previous, following in zip(order, order[1:]):
        if following in existing and (previous not in existing or existing[previous] != "PASS"):
            raise RuntimeError("BARRIER_BROKEN:" + following)
    return {"status": "PASS", "code_sha256": code_sha(), "receipts": existing}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("fixtures", "source-cache", "d0", "d1", "d2", "d3", "check"))
    mode = parser.parse_args().mode
    routes = {
        "fixtures": fixtures,
        "source-cache": source_cache,
        "d0": d0,
        "d1": lambda: sequential("D1", ("d0-receipt.json",)),
        "d2": lambda: sequential("D2", ("d0-receipt.json", "d1-receipt.json")),
        "d3": lambda: sequential("D3", ("d0-receipt.json", "d1-receipt.json", "d2-receipt.json")),
        "check": check,
    }
    result = routes[mode]()
    result = {**result, "python": sys.version, "numpy": np.__version__, "platform": platform.platform()}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
