"""한 NWB의 필요한 바이트만 보유 캐시에 읽는다. 전체 파일 다운로드가 아니다."""
import hashlib
import io
import json
import urllib.request
from pathlib import Path

import h5py

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
URL = "https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-1574292898.139.nwb"
CACHE = ROOT / "data/external/allen_synphys_r21/raw_ranges/1574292898.139"
BLOCK = 65536
LIMIT = 64 * 1024 * 1024


class CachedRanges(io.RawIOBase):
    def __init__(self):
        super().__init__()
        with urllib.request.urlopen(urllib.request.Request(URL, method="HEAD"), timeout=30) as response:
            self.remote = {"url": URL, "bytes": int(response.headers["Content-Length"]),
                           "etag": response.headers["ETag"], "last_modified": response.headers["Last-Modified"]}
        CACHE.mkdir(parents=True, exist_ok=True)
        self.manifest_path = CACHE / "manifest.json"
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if self.manifest["remote"] != self.remote:
                raise RuntimeError("원격 판본 변경. 기존 부분 캐시와 섞지 않습니다.")
        else:
            self.manifest = {"remote": self.remote, "block_size": BLOCK, "scope": "partial byte-range cache; not complete NWB", "blocks": {}}
        self.pos = 0
        self.downloaded_this_session = 0

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else (self.pos if whence == 1 else self.remote["bytes"]) + offset
        if whence not in (0, 1, 2) or position < 0:
            raise ValueError("invalid seek")
        self.pos = position
        return position

    def block(self, start):
        end = min(start + BLOCK, self.remote["bytes"]) - 1
        path = CACHE / f"{start:012d}.bin"
        previous = self.manifest["blocks"].get(str(start))
        if path.exists() and previous:
            raw = path.read_bytes()
            assert len(raw) == previous["bytes"] and hashlib.sha256(raw).hexdigest() == previous["sha256"]
            return raw
        if sum(b["bytes"] for b in self.manifest["blocks"].values()) + end - start + 1 > LIMIT:
            raise RuntimeError("64MiB 부분 수집 상한 도달. 캐시를 보존합니다.")
        req = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}", "If-Match": self.remote["etag"]})
        with urllib.request.urlopen(req, timeout=30) as response:
            assert response.status == 206
            assert response.headers["Content-Range"] == f"bytes {start}-{end}/{self.remote['bytes']}"
            assert response.headers["ETag"] == self.remote["etag"]
            raw = response.read(end-start+2)
        assert len(raw) == end-start+1
        with path.open("xb") as f: f.write(raw)
        self.manifest["blocks"][str(start)] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        temp = self.manifest_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
        temp.replace(self.manifest_path)
        self.downloaded_this_session += len(raw)
        return raw

    def read(self, size=-1):
        available = max(0, self.remote["bytes"] - self.pos)
        size = available if size < 0 else min(size, available)
        if size > LIMIT:
            raise RuntimeError("요청 범위가 부분 수집 상한보다 큽니다.")
        result = bytearray()
        while len(result) < size:
            start = (self.pos // BLOCK) * BLOCK
            raw = self.block(start)
            offset = self.pos - start
            piece = raw[offset:offset + size-len(result)]
            result.extend(piece)
            self.pos += len(piece)
        return bytes(result)

    def readinto(self, buffer):
        raw = self.read(len(buffer))
        buffer[:len(raw)] = raw
        return len(raw)


def describe(node):
    if isinstance(node, h5py.Dataset):
        result = {"path": node.name, "shape": list(node.shape), "dtype": str(node.dtype)}
        if node.size < 10 and node.dtype.kind in "OSU":
            result["value"] = str(node[()])
        return result
    return {"path": node.name, "children": list(node)[:30], "child_count": len(node)}


def main():
    output = HERE / "raw_metadata_result.json"
    if output.exists():
        raise RuntimeError("메타데이터 영수증이 이미 있습니다.")
    with CachedRanges() as remote:
        with h5py.File(remote, "r") as f:
            result = {"remote": remote.remote, "root": {key: describe(f[key]) for key in f}, "acquisition_examples": []}
            acquisition = f.get("acquisition/timeseries", f.get("acquisition"))
            if acquisition is not None:
                for key in list(acquisition)[:5]:
                    node = acquisition[key]
                    entry = describe(node)
                    if isinstance(node, h5py.Group):
                        entry["fields"] = {k: describe(node[k]) for k in node}
                    result["acquisition_examples"].append(entry)
        result["downloaded_this_session"] = remote.downloaded_this_session
        result["cached_bytes_total"] = sum(b["bytes"] for b in remote.manifest["blocks"].values())
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
