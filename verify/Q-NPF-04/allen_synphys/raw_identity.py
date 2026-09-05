"""대상 세포·전극·NWB 채널 대응을 읽기 전용으로 조사한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from raw_metadata import CachedRanges

HERE = Path(__file__).resolve().parent


def plain(value):
    if isinstance(value, bytes): return value.decode("utf-8", errors="replace")
    if isinstance(value, np.ndarray): return [plain(v) for v in value.tolist()]
    if isinstance(value, np.generic): return plain(value.item())
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    return value


def inspect(node):
    result = {"path": node.name, "attrs": {k: plain(v) for k,v in node.attrs.items()}}
    if isinstance(node, h5py.Dataset):
        result.update(shape=list(node.shape), dtype=str(node.dtype))
        if node.size <= 20: result["value"] = plain(node[()])
    else:
        result["children"] = list(node)
    return result


def main():
    out = HERE / "raw_identity_result.json"
    if out.exists(): raise RuntimeError("기존 identity 영수증 보존")
    with CachedRanges() as r:
        with h5py.File(r,"r") as f:
            acq = f["acquisition/timeseries"]
            stim = f["stimulus/presentation"]
            result = {"acquisition_names": list(acq), "stimulus_names": list(stim), "examples": [], "general": {}}
            for name in list(acq)[:3]:
                node=acq[name]
                result["examples"].append({"node":inspect(node),"fields":{k:inspect(node[k]) for k in node}})
            for name in list(stim)[:3]:
                node=stim[name]
                result["examples"].append({"node":inspect(node),"fields":{k:inspect(node[k]) for k in node}})
            for path in ["general/intracellular_ephys", "general/labnotebook", "general/subject"]:
                node=f[path]
                result["general"][path] = {"node":inspect(node),"fields":{k:inspect(node[k]) for k in node}}
        result["new_bytes"] = r.downloaded_this_session
        result["total_cached_bytes"] = sum(b["bytes"] for b in r.manifest["blocks"].values())
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ('acquisition_names','stimulus_names')},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
