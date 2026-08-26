"""Stream one development stimulation site into the frozen biological endpoint."""
from __future__ import annotations

import csv
import concurrent.futures
import hashlib
import io
from typing import Any, Callable

import numpy as np

import id4_ccep_apparatus as apparatus
import id4_development_endpoint as endpoint
import id4_development_index_acquire as acquire
import id4_development_range_plan as planner
import id4_development_signal as signal

STOP = "APPARATUS_DEVELOPMENT_SITE_STOP"


def _channel_job(job: tuple[str, dict[str, Any], list[dict[str, Any]]]) -> tuple[str, np.ndarray, dict[str, Any], str]:
    """Isolated-process network/decode job; caller erases the returned transient array."""
    channel, provenance, events = job
    transport = acquire.CurlTransport()
    metadata = signal.acquire_channel_metadata(subject="sub-1", channel=channel,
                                               expected=provenance, transport=transport)
    values, receipt = signal.process_eligible_event_windows(
        metadata, events, transport=transport, processor=lambda transient, _events: transient.copy())
    return channel, values, receipt, metadata["identities"]["tmet"]["sha256"]


def run_first_sub1_site(transport: signal.RangeTransport, plan: dict[str, Any], *,
                        progress: Callable[[int, int, str], None] | None = None,
                        workers: int = 1) -> dict[str, Any]:
    """Compute one preregistered site's mean/bip endpoints without retaining raw signal."""
    if plan.get("subject") != "sub-1" or plan.get("snapshot") != planner.FROZEN_SNAPSHOT:
        raise ValueError(f"{STOP}:plan")
    tsv: dict[str, bytes] = {}
    for name, path in acquire._tsv_paths("sub-1").items():
        body = transport.get(acquire._url(acquire.RAW_PREFIX, path), timeout=acquire.TIMEOUT_SECONDS,
                             max_bytes=acquire.MAX_TSV_BYTES)
        if hashlib.sha256(body).hexdigest() != plan["tsv_sha256"][name]:
            raise RuntimeError(f"{STOP}:TSV")
        tsv[name] = body
    texts = {name: body.decode("utf-8") for name, body in tsv.items()}
    table = planner.development_event_table(snapshot=planner.FROZEN_SNAPSHOT, subject="sub-1",
                                            events_tsv=texts["events"], channels_tsv=texts["channels"],
                                            electrodes_tsv=texts["electrodes"], fs_hz=2048)
    site = table[0]["node"]
    events = [row for row in table if row["node"] == site]
    channel_rows = list(csv.DictReader(io.StringIO(texts["channels"]), delimiter="\t"))
    channels = [row["name"].strip() for row in channel_rows
                if row.get("name", "").strip() and row.get("status", "").strip().lower() == "good"
                and row.get("type", "").strip().lower() in {"ieeg", "seeg", "ecog"}]
    provenance = {row["channel"]: row for row in plan["channel_provenance"]}
    if set(channels) != set(provenance):
        raise RuntimeError(f"{STOP}:channel population")
    tile = np.empty((len(events), len(channels), endpoint.WINDOW_SAMPLES), dtype=np.float64)
    receipts: list[dict[str, Any]] = []
    def retain_channel(channel: str, values: np.ndarray, receipt: dict[str, Any], tmet_sha256: str) -> None:
        index = channels.index(channel)
        tile[:, index, :] = values
        values.fill(np.nan)
        receipts.append({"channel": channel, "payload_bytes": receipt["payload_bytes"],
                         "range_sha256": receipt["range_sha256"], "tmet_sha256": tmet_sha256})
        if progress is not None:
            progress(len(receipts), len(channels), channel)

    try:
        if workers == 1:
            for index, channel in enumerate(channels):
                metadata = signal.acquire_channel_metadata(subject="sub-1", channel=channel,
                                                           expected=provenance[channel], transport=transport)

                def retain(values: np.ndarray, _events: Any, *, column: int = index) -> bool:
                    tile[:, column, :] = values
                    return True

                _, receipt = signal.process_eligible_event_windows(metadata, events, transport=transport,
                                                                   processor=retain)
                receipts.append({"channel": channel, "payload_bytes": receipt["payload_bytes"],
                                 "range_sha256": receipt["range_sha256"],
                                 "tmet_sha256": metadata["identities"]["tmet"]["sha256"]})
                if progress is not None:
                    progress(index + 1, len(channels), channel)
        elif type(workers) is int and 2 <= workers <= 16:
            jobs = [(channel, dict(provenance[channel]), events) for channel in channels]
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_channel_job, job) for job in jobs]
                for future in concurrent.futures.as_completed(futures):
                    retain_channel(*future.result())
        else:
            raise ValueError(f"{STOP}:workers")
        metadata_plan = apparatus.canonical_metadata_plan(texts["channels"], texts["electrodes"], texts["events"],
                                                          snapshot=planner.FROZEN_SNAPSHOT, subject="sub-1")
        registered_receivers: set[str] = set()
        for pair in metadata_plan["pairs"]:
            if pair["allocation"] != "development_apparatus":
                continue
            if pair["a"] == site:
                registered_receivers.add(pair["b"])
            elif pair["b"] == site:
                registered_receivers.add(pair["a"])
        order = {channel: index for index, channel in enumerate(channels)}
        receivers = {node: (order[node.split("-")[0]], order[node.split("-")[1]])
                     for node in sorted(registered_receivers)}
        if not receivers:
            raise RuntimeError(f"{STOP}:no registered receivers")
        result = endpoint.site_endpoints(tile, stimulated=tuple(order[name] for name in site.split("-")),
                                         halves=[row["half"] for row in events], receiver_contacts=receivers)
    finally:
        tile.fill(np.nan)
        del tile
    return {"status": "PASS_FIRST_DEVELOPMENT_SITE_ENDPOINT", "snapshot": planner.FROZEN_SNAPSHOT,
            "subject": "sub-1", "stimulation_site": site, "trials": len(events),
            "channels": len(channels), "registered_receivers": len(receivers),
            "endpoints": result["endpoints"], "selected_car75_per_trial": result["selected_per_trial"],
            "payload_bytes": sum(row["payload_bytes"] for row in receipts),
            "channel_receipt_set_sha256": hashlib.sha256(
                repr(sorted(receipts, key=lambda row: row["channel"])).encode("utf-8")).hexdigest(),
            "persistent_raw_bytes": 0, "raw_tile_disposed": True,
            "endpoint_evidence": True, "development_gate_computed": False,
            "confirmation_opened": False}
