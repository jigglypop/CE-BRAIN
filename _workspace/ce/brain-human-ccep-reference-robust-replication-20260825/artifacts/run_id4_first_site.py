"""CLI entry point for the raw-free parallel first-site development endpoint."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import id4_development_index_acquire as acquire
import id4_development_site as site


def main() -> None:
    root = Path(__file__).parent
    plan = json.loads((root / "development-index-plan-sub-1-v4.json").read_text(encoding="utf-8"))
    result = site.run_first_sub1_site(
        acquire.CurlTransport(), plan, workers=6,
        progress=lambda count, total, channel: print(f"PROGRESS {count}/{total} {channel}", flush=True),
    )
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = root / "development-first-site-sub-1.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    temporary.replace(output)
    print("RESULT_JSON", flush=True)
    print(json.dumps(result, sort_keys=True), flush=True)
    print(f"result={output}", flush=True)
    print(f"result_sha256={hashlib.sha256(serialized.encode('utf-8')).hexdigest()}", flush=True)


if __name__ == "__main__":
    main()
