"""CLI entry point for the raw-free parallel first-site development endpoint."""
from __future__ import annotations

import json
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
    print("RESULT_JSON", flush=True)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
