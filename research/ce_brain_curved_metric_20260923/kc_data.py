"""Bergmann et al. 2026 KC calcium table: parsing, cohort means and published evaluation units."""
from __future__ import annotations
import csv
import hashlib
from itertools import combinations
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CSV_PATH = ROOT / "data" / "external" / "bergmann_2026_kc" / "all KC values.csv"
CSV_SHA256 = "5733b69eda14e5c557e784e96da917091877dc86a3a4a9c6026eae2520c8765a"
CSV_BYTES = 17682
PUBLICATION = ROOT / "research" / "ce_brain_publication_20260919"
REGIONS = ("Calyx", "gamma", "beta", "betaprime", "alpha", "alphaprime")
GROUPS = (("22c", "ctrl"), ("22c", "TRPA"), ("31c", "ctrl"), ("31c", "TRPA"))
N_POS = 7


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def load_table(path: Path = CSV_PATH) -> dict:
    content = path.read_bytes()
    if len(content) != CSV_BYTES or hashlib.sha256(content).hexdigest() != CSV_SHA256:
        raise ValueError(f"CSV identity mismatch: {path}")
    rows = list(csv.reader(content.decode("utf-8-sig").splitlines()))
    body = rows[3:]
    while body and all(cell.strip() == "" for cell in body[-1][1:]):
        body = body[:-1]
    if len(body) % N_POS:
        raise ValueError("CSV body is not made of 7-row blocks")
    table = {}
    for r, region in enumerate(REGIONS):
        for g, group in enumerate(GROUPS):
            col = 1 + 4 * r + g
            vectors, slots = [], []
            for k in range(len(body) // N_POS):
                chunk = body[k * N_POS:(k + 1) * N_POS]
                cells = [row[col].strip() if col < len(row) else "" for row in chunk]
                if all(c == "" for c in cells):
                    continue
                if any(c == "" for c in cells):
                    raise ValueError(f"Partial vector {region} {group} slot {k + 1}")
                vectors.append([float(c) for c in cells])
                slots.append(k + 1)
            table[(region, group)] = {"values": np.array(vectors), "slots": np.array(slots)}
    return table


def quality(table: dict) -> dict:
    values = [t["values"] for t in table.values()]
    return {"measurements": int(sum(v.size for v in values)),
            "complete_vectors": int(sum(v.shape[0] for v in values)),
            "retained_negative_values": int(sum((v < 0).sum() for v in values)),
            "count_by_region_group": [[int(table[(r, g)]["values"].shape[0]) for g in GROUPS]
                                      for r in REGIONS]}


def cohort(table: dict, temp: str = "31c", select: dict | None = None) -> dict:
    """Per (position, region) means and SEMs; select maps (region, group) -> row mask."""
    out = {}
    for name, group in (("x", (temp, "ctrl")), ("y", (temp, "TRPA"))):
        mean = np.zeros((N_POS, len(REGIONS)))
        sem = np.zeros_like(mean)
        count = np.zeros(len(REGIONS), dtype=int)
        for c, region in enumerate(REGIONS):
            v = table[(region, group)]["values"]
            if select is not None:
                v = v[select[(region, group)]]
            mean[:, c] = v.mean(axis=0)
            sem[:, c] = v.std(axis=0, ddof=1) / np.sqrt(v.shape[0])
            count[c] = v.shape[0]
        out[name] = mean
        out[f"sem_{name}"] = sem
        out[f"n_{name}"] = count
    return out


def slot_parity_masks(table: dict, temp: str = "31c") -> list[dict]:
    masks = [{}, {}]
    for region in REGIONS:
        for kind in ("ctrl", "TRPA"):
            key = (region, (temp, kind))
            slots = table[key]["slots"]
            masks[0][key] = slots % 2 == 1
            masks[1][key] = slots % 2 == 0
    return masks


def _subset(means: dict, positions) -> dict:
    return {k: means[k][list(positions)] for k in ("x", "y", "sem_x", "sem_y")}


def panel_tasks(table: dict, panel: str) -> list[dict]:
    """Published evaluation units; each task trains on `train` and predicts y at `held` from test x."""
    if panel in ("leave1", "leave2"):
        full = cohort(table)
        pairs = [(full, full)]
        k = 1 if panel == "leave1" else 2
    elif panel in ("slot0", "slot1"):
        halves = [cohort(table, select=m) for m in slot_parity_masks(table)]
        pairs = [(halves[0], halves[1])] if panel == "slot0" else [(halves[1], halves[0])]
        k = 1
    else:
        raise ValueError(panel)
    tasks = []
    for train_means, test_means in pairs:
        for held in combinations(range(N_POS), k):
            keep = [p for p in range(N_POS) if p not in held]
            tasks.append({"train": _subset(train_means, keep), "held": list(held),
                          "test_x": test_means["x"][list(held)], "test_y": test_means["y"][list(held)]})
    return tasks


FRESH_SEEDS = tuple(range(2026091900, 2026091932))


def fresh_split_masks(table: dict, seed: int) -> dict:
    """Published fresh split: one default_rng permutation per region x group column in table order."""
    rng = np.random.default_rng(seed)
    masks = {}
    for region in REGIONS:
        for group in GROUPS:
            n = table[(region, group)]["values"].shape[0]
            first = np.zeros(n, dtype=bool)
            first[rng.permutation(n)[:n // 2]] = True
            masks[(region, group)] = first
    return masks


def fresh_tasks(table: dict, seed: int) -> list[dict]:
    masks = fresh_split_masks(table, seed)
    keys = [(r, ("31c", g)) for r in REGIONS for g in ("ctrl", "TRPA")]
    train_means = cohort(table, select={k: masks[k] for k in keys})
    test_means = cohort(table, select={k: ~masks[k] for k in keys})
    tasks = []
    for h in range(N_POS):
        keep = [p for p in range(N_POS) if p != h]
        tasks.append({"train": _subset(train_means, keep), "held": [h],
                      "test_x": test_means["x"][[h]], "test_y": test_means["y"][[h]]})
    return tasks


def read_selected_predictions() -> list[dict]:
    with (PUBLICATION / "selected_predictions.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def verify_targets(table: dict) -> dict:
    means = cohort(table)
    rows = read_selected_predictions()
    err_x = err_y = 0.0
    for row in rows:
        p = int(row["position"]) - 1
        c = REGIONS.index(row["region"])
        err_x = max(err_x, abs(means["x"][p, c] - float(row["input"])))
        err_y = max(err_y, abs(means["y"][p, c] - float(row["target"])))
    return {"rows": len(rows), "max_input_error": err_x, "max_target_error": err_y}


if __name__ == "__main__":
    t = load_table()
    print(quality(t))
    print(verify_targets(t))
    for key, item in t.items():
        print(key, item["values"].shape[0], item["slots"].tolist())
