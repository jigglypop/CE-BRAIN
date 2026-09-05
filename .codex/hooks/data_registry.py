"""로컬 데이터 원장: 이력 보존 등록과 네트워크 없는 검색."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "ledger/data_registry.jsonl"


def read_records(ledger):
    if not ledger.exists():
        return []
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def local_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def register(ledger, dataset, version, asset, path, source, reason, location_only=False):
    path = path.resolve()
    if not path.exists():
        raise ValueError("보유 경로가 없습니다. 없는 파일을 수집 완료로 등록할 수 없습니다.")
    if not location_only and (not path.is_file() or path.name.endswith((".partial", ".part"))):
        raise ValueError("폴더·미완료 파일은 --location-only로 등록하세요.")
    before = path.stat()
    sha = None if location_only else digest(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("등록 중 파일이 변경됐습니다. 수집 완료 뒤 다시 등록하세요.")
    try:
        stored_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        stored_path = path.as_posix()
    records = read_records(ledger)
    identity = (dataset, version, asset)
    matches = [r for r in records if (r["dataset"], r["version"], r["asset"]) == identity]
    if sha and any(r["sha256"] and r["sha256"] != sha for r in matches):
        raise ValueError("같은 자료·판본·파일에 다른 해시가 있습니다. 손상 여부나 판본을 확인하세요.")
    record = dict(dataset=dataset, version=version, asset=asset, path=stored_path,
                  source=source, reason=reason, sha256=sha,
                  status="location_only" if location_only else "verified_file",
                  bytes=after.st_size if path.is_file() else None,
                  mtime_ns=after.st_mtime_ns if path.is_file() else None)
    if any(all(r.get(k) == v for k, v in record.items()) for r in matches):
        return record, False
    record["recorded_at"] = datetime.now(timezone.utc).isoformat()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    # 원장 작성은 주 에이전트 한 명이 직렬 수행한다. 이전 기록은 덮어쓰지 않는다.
    with ledger.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record, True


def find(ledger, query, verify=False):
    latest = {}
    for record in read_records(ledger):
        key = tuple(record[k] for k in ("dataset", "version", "asset", "path"))
        latest[key] = record
    results = []
    for record in latest.values():
        if query.casefold() not in json.dumps(record, ensure_ascii=False).casefold():
            continue
        result = dict(record)
        path = local_path(record["path"])
        if not path.exists():
            state = "missing"
        elif path.name.endswith((".partial", ".part")):
            state = "partial"
        elif record["status"] == "location_only":
            state = "location_only"
        elif not path.is_file():
            state = "changed"
        elif verify:
            state = "hash_match" if digest(path) == record["sha256"] else "changed"
        else:
            stat = path.stat()
            state = "unchanged_metadata" if (stat.st_size, stat.st_mtime_ns) == (record["bytes"], record["mtime_ns"]) else "changed"
        result["local_state"] = state
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help="원장 경로")
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("find", help="보유 자료 검색, 기본은 해시 재계산 없음")
    search.add_argument("query")
    search.add_argument("--verify", action="store_true", help="검색된 등록 파일의 해시 재검증")
    add = commands.add_parser("register", help="파일 검증 등록 또는 보유 위치 등록")
    for name in ("dataset", "version", "asset", "source", "reason"):
        add.add_argument("--" + name, required=True)
    add.add_argument("--path", type=Path, required=True)
    add.add_argument("--location-only", action="store_true", help="폴더·미완료 파일의 위치만 기록")
    args = parser.parse_args()
    try:
        if args.command == "find":
            result = find(args.ledger, args.query, args.verify)
        else:
            record, added = register(args.ledger, args.dataset, args.version, args.asset,
                                     local_path(args.path), args.source, args.reason, args.location_only)
            result = {"added": added, "record": record}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
