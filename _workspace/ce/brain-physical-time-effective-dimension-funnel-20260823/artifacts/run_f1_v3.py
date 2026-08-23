"""BA-SRM8 F1 v3: prefix-only preprocessing, no behavior/model access."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np

from funnel_core_v2 import ROOT, causal_q, manifest, sha


OUT = ROOT / "f1-receipt-v3.json"
F0 = ROOT / "f0-receipt-v2.json"
F1V2 = ROOT / "f1-receipt-v2.json"
CLASSIFICATION = ROOT / "f0f1-classification-receipt.json"
EXPECTED = {
    "f0_v2": "4a71893a420c054bf39ac8661e21e7c71655ffeb53fe04c9d6f2e211f06ffb33",
    "f1_v2": "3ba86b48892991406f593b5ffd0c818faa65ec8b5bdb0fad5acd924a8aa63c26",
    "classification": "3f7b3e5869ed2abe2a057eabccf76442819ef88f23685b77e2b83a1580bbf0c1",
    "core": "e685568ad4836dab1f301f69afa2e9c9a4d8fcecd7a1a64fb2bdba830a5ebc65",
    "manifest": "58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(value: object) -> None:
    data = canonical(value)
    with OUT.open("wb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    if OUT.read_bytes() != data: raise ValueError("receipt persistence mismatch")


def raw_synth(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed); n, count = 8, 192
    clock = np.cumsum(np.r_[0., rng.uniform(.75, 1.35, count - 1)])
    phase = np.linspace(0, 6*np.pi, count)
    latent = np.vstack([np.sin(phase), np.cos(.7*phase), np.sin(1.7*phase), rng.normal(size=count)])
    load = rng.normal(size=(n,4)); envelope = np.vstack([.15+1.4/(1+np.exp(-3*np.sin(phase-shift))) for shift in np.linspace(0,2,4)])
    drive = load @ (latent * envelope); clean = np.zeros_like(drive)
    for t in range(1,count):
        decay = math.exp(-(clock[t]-clock[t-1])/3); clean[:,t] = decay*clean[:,t-1] + (1-decay)*drive[:,t]
    prefix = clean[:, :int(.6*count)]
    noise_sd = float(np.sqrt(np.mean(prefix*prefix)) / 4.)
    noisy = clean + rng.normal(0., noise_sd, clean.shape)
    mask = (rng.random(clean.shape) >= .10).astype(float)
    return clean, noisy, mask, clock


def preprocess(raw: np.ndarray, mask: np.ndarray, prefix_end: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n, count = raw.shape
    if raw.shape != mask.shape or not np.isfinite(raw).all(): raise ValueError("raw/mask invalid")
    z = np.zeros_like(raw); mu = np.empty(n); scale = np.empty(n); d = np.empty(n)
    for i in range(n):
        selected = raw[i, :prefix_end][mask[i, :prefix_end] == 1]
        if selected.size < 2: raise ValueError("prefix observed sample shortage")
        mu[i] = selected.mean(); scale[i] = selected.std()
        if not math.isfinite(scale[i]) or scale[i] <= 1e-12: raise ValueError("prefix scale invalid")
        d[i] = math.sqrt(float(mask[i, :prefix_end].mean()))
        z[i] = (raw[i] - mu[i]) / scale[i]
    z[(mask == 0) | ~np.isfinite(z)] = 0.
    return z, d, mu, scale


def average_rank(x: np.ndarray) -> np.ndarray:
    order=np.argsort(x,kind="stable"); ranks=np.empty(x.size); i=0
    while i<x.size:
        j=i+1
        while j<x.size and x[order[j]]==x[order[i]]: j+=1
        ranks[order[i:j]]=(i+j-1)/2; i=j
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 3 or np.ptp(x) == 0 or np.ptp(y) == 0: return float("nan")
    return float(np.corrcoef(average_rank(x),average_rank(y))[0,1])


def check_hashes(manifest_hash: str) -> dict[str, str]:
    values = {"f0_v2": digest(F0), "f1_v2": digest(F1V2), "classification": digest(CLASSIFICATION), "core": sha(ROOT/"funnel_core_v2.py"), "manifest": manifest_hash, "runner": sha(Path(__file__))}
    for key, expected in EXPECTED.items():
        if values[key] != expected: raise ValueError(key + " hash mismatch")
    return values


def main() -> None:
    man, manifest_hash = manifest(); hashes = check_hashes(manifest_hash)
    classified = json.loads(CLASSIFICATION.read_text(encoding="utf-8")); abstain = set(classified["mapped_ids"])
    if len(abstain) != 12: raise ValueError("classification mapping count invalid")
    prefix_end, calibration_end = int(.6*192), math.ceil(.7*192)
    perturb_checks = []
    for seed in range(20260823, 20260827):
        clean, noisy, mask, clock = raw_synth(seed)
        z, d, mu, scale = preprocess(clean, mask, prefix_end)
        changed = clean.copy(); changed[:, prefix_end:] += 101.
        z2, d2, mu2, scale2 = preprocess(changed, mask, prefix_end)
        if not (np.array_equal(mu,mu2) and np.array_equal(scale,scale2) and np.array_equal(d,d2) and np.array_equal(z[:,:prefix_end],z2[:,:prefix_end])):
            raise ValueError("future perturbation changed prefix preprocessing")
        perturb_checks.append({"seed":seed,"prefix_D_equal":True,"prefix_mu_sigma_equal":True,"prefix_z_equal":True})
    rows=[]
    for candidate in man["candidates"]:
        if candidate["id"] in abstain:
            rows.append({"id":candidate["id"],"metrics":{},"reason":"ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF","runtime_seconds":0.,"status":"ABSTAIN"}); continue
        start=time.perf_counter(); per=[]
        for seed in range(20260823, 20260827):
            clean, noisy, mask, clock = raw_synth(seed)
            z_clean,d_clean,_,_ = preprocess(clean,mask,prefix_end)
            z_noisy,d_noisy,_,_ = preprocess(noisy,mask,prefix_end)
            if not np.array_equal(d_clean,d_noisy): raise ValueError("same D invariant failed")
            truth=causal_q(candidate,z_clean,mask,clock,d_clean,calibration_end)["Q"]
            estimate=causal_q(candidate,z_noisy,mask,clock,d_noisy,calibration_end)["Q"]
            common=np.isfinite(truth)&np.isfinite(estimate)
            if common.sum()<100: per.append({"eligible_anchors":int(common.sum()),"status":"ABSTAIN_COMMON_ANCHORS"}); continue
            s=spearman(truth[common],estimate[common])
            if not math.isfinite(s): per.append({"eligible_anchors":int(common.sum()),"status":"ABSTAIN_CONSTANT_TRUTH"}); continue
            per.append({"eligible_anchors":int(common.sum()),"nmae_Q":float(np.mean(abs(estimate[common]-truth[common]))),"spearman":s,"status":"PASS"})
        elapsed=time.perf_counter()-start; usable=[x for x in per if x["status"]=="PASS"]
        if len(usable)!=4:
            rows.append({"id":candidate["id"],"metrics":{"per_seed":per},"reason":"F1_ABSTAIN","runtime_seconds":elapsed,"status":"ABSTAIN"}); continue
        nmae=float(np.median([x["nmae_Q"] for x in usable])); sp=float(np.median([x["spearman"] for x in usable]))
        status="PASS" if sp>=.75 and nmae<=.25 else "INVALID_KILL"
        rows.append({"id":candidate["id"],"metrics":{"median_nmae_Q":nmae,"median_spearman":sp,"per_seed":per},"reason":None if status=="PASS" else "F1_ABSOLUTE_GATE","runtime_seconds":elapsed,"status":status})
    survivors=sorted([x for x in rows if x["status"]=="PASS"],key=lambda x:(x["metrics"]["median_nmae_Q"],-x["metrics"]["median_spearman"],x["runtime_seconds"],x["id"]))
    promoted=[x["id"] for x in survivors[:32]]
    for row in rows:
        if row["id"] in promoted: row["status"]="PROMOTE"
        elif row["status"]=="PASS": row["status"]="DROPPED_BUDGET"; row["reason"]="F1 promotion cap 32"
    old_promoted=json.loads(F1V2.read_text(encoding="utf-8"))["promoted_ids"]
    receipt={"apparatus":{"N":8,"T":192,"calcium":"causal exponential decay tau=3 clock units; raw clean returned","noise":"Gaussian, clean first-60%-prefix pooled RMS / 4","missingness":"MCAR 10 percent; same mask/clock/candidate/D for truth and estimate","preprocessing":"per-channel observed finite original indices < floor(0.6*T); separate clean/noisy mu/sigma; frozen application all T; masked/nonfinite z=0","seeds":[20260823,20260824,20260825,20260826]},"behavior_loaded":False,"candidate_count":48,"candidates":rows,"direct_future_perturbation_preprocessing_check":perturb_checks,"f1_v2_promotion_invalid":True,"f1_v2_superseded_reason":"full_T_preprocessing_leakage_only","input_hashes":hashes,"model_fit":False,"promotion_changed_from_f1_v2":promoted!=old_promoted,"promoted_ids":promoted,"runtime_seconds":sum(x["runtime_seconds"] for x in rows),"schema":"BA-SRM8-F1-v3"}
    write(receipt); print(json.dumps({"promoted":len(promoted),"promotion_changed":promoted!=old_promoted},sort_keys=True))


if __name__=="__main__": main()
