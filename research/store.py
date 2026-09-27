"""세션 형식: 모든 생물 기록을 한 모양의 비압축 npz로 읽는다.

- 스파이크: `spikes`(f64, 단위마다 오름차순)와 단위별 끝 색인 `ends`(i64). 단위 열은 `unit_<이름>`.
- 구간: `<이름>_start`, `<이름>_stop`, 있으면 `<이름>_label`.
- 시계열: `<이름>_t`와 `<이름>`.
옛 압축 추출본은 처음 읽을 때 원장 sha256을 이름으로 한 비압축 사본을 data/cache에 만든다. 새 자료는
`extract`가 NWB(DANDI 원격이면 HTTP 범위 읽기)에서 필요한 부분만 이 형식으로 옮기고 원장에 등록한다.
세기는 Rust 핵심(cefast)이 맡는다.
"""

from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path

import cefast
import h5py
import numpy as np
import remfile
import requests

from research import harness

DATA = harness.ROOT / "data/external"
CACHE = harness.ROOT / "data/cache"
API = "https://api.dandiarchive.org/api"
ALIASES = {  # dandi-000939-extract의 옛 이름 → NWB 이름
    "spike_times": "spikes", "spike_times_index": "ends",
    "is_head_direction": "unit_is_head_direction", "is_excitatory": "unit_is_excitatory",
    "is_fast_spiking": "unit_is_fast_spiking",
    "ss_start": "sleep_states_start", "ss_stop": "sleep_states_stop", "ss_state": "sleep_states_label",
    "ep_start": "epochs_start", "ep_stop": "epochs_stop", "ep_tag": "epochs_label",
    "hd_t": "head_t", "hd": "head",
}


class Session:
    """One recording in the session format."""

    def __init__(self, arrays):
        self.arrays = arrays
        self.spikes = np.ascontiguousarray(arrays["spikes"], np.float64)
        self.ends = np.ascontiguousarray(arrays["ends"], np.int64)

    def __getitem__(self, key):
        return self.arrays[key]

    def __contains__(self, key):
        return key in self.arrays

    def intervals(self, name, label=None):
        """Start and stop times of an interval table, optionally only the rows with one label."""
        start, stop = self[f"{name}_start"], self[f"{name}_stop"]
        keep = slice(None) if label is None else self[f"{name}_label"] == label
        return start[keep].astype(np.float64), stop[keep].astype(np.float64)

    def series(self, name):
        return self[f"{name}_t"], self[name]

    def units(self, keep):
        """The same session restricted to the units where keep is true."""
        keep = np.asarray(keep, bool)
        parts = [p for p, k in zip(np.split(self.spikes, self.ends[:-1]), keep) if k]
        arrays = {k: v[keep] if k.startswith("unit_") else v for k, v in self.arrays.items()}
        arrays["spikes"] = np.concatenate(parts) if parts else np.empty(0)
        arrays["ends"] = np.cumsum([len(p) for p in parts], dtype=np.int64)
        return Session(arrays)

    def within(self, starts, stops):
        """The same session with only the spikes inside the non-overlapping intervals [starts, stops)."""
        order = np.argsort(starts)
        starts, stops = np.asarray(starts, np.float64)[order], np.asarray(stops, np.float64)[order]
        parts = []
        for p in np.split(self.spikes, self.ends[:-1]):
            i = np.searchsorted(starts, p, side="right") - 1
            parts.append(p[(i >= 0) & (p < stops[i.clip(0)])])
        return Session({**self.arrays, "spikes": np.concatenate(parts) if parts else np.empty(0),
                        "ends": np.cumsum([len(p) for p in parts], dtype=np.int64)})

    def counts(self, edges):
        """Spike counts (units × bins) in contiguous bins [edges[k], edges[k+1])."""
        return cefast.bin_counts(self.spikes, self.ends, np.asarray(edges, np.float64))

    def window_counts(self, starts, stops):
        """Spike counts (units × windows) in arbitrary windows [starts, stops)."""
        return cefast.window_counts(self.spikes, self.ends, np.asarray(starts, np.float64),
                                    np.asarray(stops, np.float64))


def load(row):
    """Session of one ledger file, through an uncompressed cache when the file is compressed."""
    with np.load(harness.path(row)) as z:
        if not any(info.compress_type for info in z.zip.infolist()) and "spikes" in z.files:
            return Session({k: z[k] for k in z.files})
        cache = CACHE / f"{row['sha256']}.npz"
        if not cache.is_file():
            CACHE.mkdir(parents=True, exist_ok=True)
            partial = cache.with_suffix(".part.npz")
            np.savez(partial, **{ALIASES.get(k, k): z[k] for k in z.files})
            partial.replace(cache)
    with np.load(cache) as z:
        return Session({k: z[k] for k in z.files})


def read_nwb(source, series=None, tables=None):
    """Session arrays of one NWB file: units, interval tables and the named time series.

    source is a local path or URL; series and tables map a name to an HDF5 path. Interval tables default
    to everything under /intervals.
    """
    remote = str(source).startswith("http")
    handle = (remfile.File(requests.head(source, allow_redirects=True, timeout=60).url, _max_threads=8) if remote
              else open(source, "rb"))
    with h5py.File(handle, "r") as f:
        arrays = {}  # 작은 표와 시계열을 먼저 읽어, 없으면 스파이크를 받기 전에 멈춘다
        paths = tables or {k: f"intervals/{k}" for k in f.get("intervals", {})}
        for name, path in paths.items():
            arrays.update(table(f[resolve(f, path)], name))
        for name, path in (series or {}).items():
            arrays[f"{name}_t"], arrays[name] = timeseries(f[resolve(f, path)])
        if "units" in f:
            arrays.update(units(f["units"]))
    return arrays


def resolve(f, path):
    """The first group matching a path with * wildcards (names differ between sessions), else KeyError."""
    if "*" not in path:
        return path
    root = path[:path.index("*")].rsplit("/", 1)[0]  # 원격 파일이므로 고정된 앞부분 아래만 순회한다
    found = []
    f[root].visit(lambda name: found.append(f"{root}/{name}") if fnmatch(f"{root}/{name}", path) else None)
    found = [name for name in found if isinstance(f[name], h5py.Group)]
    if not found:
        raise KeyError(path)
    return found[0]


def units(group):
    """Spikes sorted within each unit, their end index, and every plain per-unit column."""
    spikes, ends = group["spike_times"][:], group["spike_times_index"][:].astype(np.int64)
    owner = np.repeat(np.arange(len(ends)), np.diff(np.r_[0, ends]))
    arrays = {"spikes": spikes[np.lexsort((spikes, owner))].astype(np.float64), "ends": ends}
    for name in plain(group, len(ends)):
        arrays[f"unit_{name}"] = column(group[name])
    return arrays


def table(group, name):
    """Start, stop and a label: the first text column, else the ragged tags joined."""
    arrays = {f"{name}_start": group["start_time"][:], f"{name}_stop": group["stop_time"][:]}
    text = [k for k in plain(group, len(group["start_time"])) if h5py.check_string_dtype(group[k].dtype)]
    if text:
        arrays[f"{name}_label"] = column(group[text[0]])
    elif "tags" in group and "tags_index" in group:
        tags, ends = column(group["tags"]), group["tags_index"][:]
        arrays[f"{name}_label"] = np.array([",".join(tags[a:b]) for a, b in zip(np.r_[0, ends[:-1]], ends)])
    return arrays


def plain(group, rows):
    """Names of the one-value-per-row number or text columns of a dynamic table."""
    return [k for k, v in group.items()
            if isinstance(v, h5py.Dataset) and v.shape == (rows,) and not k.endswith("_index")
            and f"{k}_index" not in group and k not in ("spike_times", "start_time", "stop_time")
            and (v.dtype.kind in "biuf" or h5py.check_string_dtype(v.dtype))]


def timeseries(group):
    """Timestamps and scaled data of an NWB TimeSeries."""
    data = group["data"]
    value = data[:]
    conversion, offset = data.attrs.get("conversion", 1.0), data.attrs.get("offset", 0.0)
    if conversion != 1.0 or offset != 0.0:
        value = value * conversion + offset
    if "timestamps" in group:
        return group["timestamps"][:].astype(np.float64), value
    start = group["starting_time"]
    return start[()] + np.arange(len(value)) / start.attrs["rate"], value


def column(item):
    return np.array(item.asstr()[:], dtype=str) if h5py.check_string_dtype(item.dtype) else item[:]


def dandi_assets(dandiset, version):
    """(path, asset id, bytes) of every asset in a DANDI dandiset version."""
    url, assets = f"{API}/dandisets/{dandiset}/versions/{version}/assets/?page_size=1000", []
    while url:
        page = requests.get(url, timeout=60).json()
        assets += [(a["path"], a["asset_id"], a["size"]) for a in page["results"]]
        url = page["next"]
    return assets


def dandi_genotype(dandiset, version, asset_id):
    """Genotype of the subject of one DANDI asset, from its metadata."""
    meta = requests.get(f"{API}/dandisets/{dandiset}/versions/{version}/assets/{asset_id}/", timeout=60).json()
    return (meta.get("wasAttributedTo") or [{}])[0].get("genotype")


def dandi_url(asset_id):
    return f"{API}/assets/{asset_id}/download/"


def extract(dataset, version, asset, source, reason, series=None, tables=None):
    """Copy one NWB file into the session format under data/external/<dataset>/ and register it."""
    arrays = read_nwb(source, series, tables)
    arrays["meta"] = np.array(json.dumps({"source": source, "series": series, "tables": tables}))
    file = DATA / dataset / f"{Path(asset).stem}.npz"
    file.parent.mkdir(parents=True, exist_ok=True)
    np.savez(file, **arrays)
    return harness.register(dataset, version, file.name, file, source, reason)
