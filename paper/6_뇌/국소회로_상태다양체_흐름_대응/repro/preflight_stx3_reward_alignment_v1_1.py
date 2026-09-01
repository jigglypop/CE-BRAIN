#!/usr/bin/env python3
"""Full structural preflight for the Stx3 v1.3 one-shot endpoint.

This reads and validates all 32 NWB sessions and all 16 ROI maps, but it never
calls the geometry, group-test, association, or endpoint-analysis functions.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import scipy

import run_stx3_reward_alignment_crossnobis_v1_1 as runner


def _write_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior-contract-addendum", required=True, type=Path)
    parser.add_argument("--statistical-contract-addendum", required=True, type=Path)
    parser.add_argument("--contract-addendum", required=True, type=Path)
    parser.add_argument("--blocked-preflight-receipt", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--download-receipt", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--roi-root", required=True, type=Path)
    parser.add_argument("--roi-audit", required=True, type=Path)
    parser.add_argument("--official-code-root", required=True, type=Path)
    parser.add_argument("--twoputils-root", required=True, type=Path)
    parser.add_argument("--mouse-metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.output.exists():
        print(f"REFUSE: preflight receipt already exists: {args.output}", file=sys.stderr)
        return 2

    runner_path = Path(runner.__file__).resolve()
    audit_module_path = Path(runner.roi_audit_module.__file__).resolve()
    receipt: dict[str, Any] = {
        "contract_id": runner.CONTRACT_ID,
        "status": "STX3_V1_3_PREFLIGHT_INCOMPLETE",
        "biological_endpoint_evaluated": False,
        "scope": "all-input structural validation only; no G, delta-G, B, group, or association result",
        "preflight_script": Path(__file__).resolve().as_posix(),
        "runner": runner_path.as_posix(),
        "roi_audit_module": audit_module_path.as_posix(),
        "resolved_data_root": args.data_root.resolve().as_posix(),
        "resolved_roi_root": args.roi_root.resolve().as_posix(),
        "resolved_official_code_root": args.official_code_root.resolve().as_posix(),
        "resolved_twoputils_root": args.twoputils_root.resolve().as_posix(),
        "environment": {
            "python_executable": Path(sys.executable).resolve().as_posix(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "h5py_version": h5py.__version__,
            "platform": platform.platform(),
        },
    }
    exit_code = 1
    try:
        receipt["preflight_script_sha256"] = runner._checked_file_sha256(
            Path(__file__).resolve(),
            status="STX3_PREFLIGHT_BLOCKED",
            label="preflight script",
        )
        receipt["runner_sha256"] = runner._checked_file_sha256(
            runner_path, status="STX3_PREFLIGHT_BLOCKED", label="endpoint runner"
        )
        receipt["roi_audit_module_sha256"] = runner._checked_file_sha256(
            audit_module_path,
            status="STX3_REGISTRATION_BLOCKED",
            label="ROI audit module",
        )
        receipt["selection_receipt_sha256"] = runner._checked_file_sha256(
            args.selection, status="STX3_SOURCE_BLOCKED", label="selection receipt"
        )
        receipt["download_receipt_sha256"] = runner._checked_file_sha256(
            args.download_receipt,
            status="STX3_SOURCE_BLOCKED",
            label="download receipt",
        )
        receipt["frozen_inputs"] = runner.validate_frozen_inputs(
            args.contract,
            args.prior_contract_addendum,
            args.statistical_contract_addendum,
            args.contract_addendum,
            args.blocked_preflight_receipt,
            args.roi_audit,
            args.official_code_root,
            args.twoputils_root,
            args.mouse_metadata,
            args.selection,
        )
        assets, integrity = runner.validate_source_receipts(
            args.selection, args.download_receipt, args.data_root
        )
        receipt["runtime_roi"] = runner.validate_runtime_roi_inputs(
            args.roi_root, args.roi_audit
        )
        receipt["source_integrity"] = {
            "asset_count": len(integrity),
            "total_bytes": sum(item["size"] for item in integrity),
            "assets": integrity,
        }
        receipt["session_summaries"] = runner.preflight_all_sessions(
            assets, args.roi_root
        )
        receipt["subject_count"] = len(
            {item["subject"] for item in receipt["session_summaries"]}
        )
        receipt["session_count"] = len(receipt["session_summaries"])
        receipt["status"] = runner.PREFLIGHT_STATUS
        exit_code = 0
    except runner.ContractBlocked as exc:
        receipt["status"] = exc.status
        receipt["error"] = str(exc)
    except Exception as exc:
        receipt["status"] = "STX3_PREFLIGHT_IMPLEMENTATION_ERROR_BLOCKED"
        receipt["error"] = f"{type(exc).__name__}: {exc}"

    try:
        _write_exclusive(args.output, receipt)
    except FileExistsError:
        print(f"REFUSE: preflight receipt already exists: {args.output}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "biological_endpoint_evaluated": False,
                "subject_count": receipt.get("subject_count"),
                "session_count": receipt.get("session_count"),
                "output": args.output.as_posix(),
                "error": receipt.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
