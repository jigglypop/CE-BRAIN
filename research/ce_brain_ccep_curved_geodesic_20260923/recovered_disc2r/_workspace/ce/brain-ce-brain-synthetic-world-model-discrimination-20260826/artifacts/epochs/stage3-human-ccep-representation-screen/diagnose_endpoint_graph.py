"""Read-only admission diagnostic for the frozen DISC2R endpoint tables."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
ENDPOINT_ROOT = (
    REPO_ROOT
    / "_workspace"
    / "ce"
    / "brain-human-ccep-multisubject-precision-retry-20260825"
    / "artifacts"
)
OUTPUT_PATH = Path(__file__).with_name("endpoint-graph-admission.json")


def main() -> None:
    sources: list[dict] = []
    for stage in range(4):
        path = ENDPOINT_ROOT / f"d{stage}-endpoints.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources.extend(payload["sources"])

    by_subject: dict[str, list[dict]] = defaultdict(list)
    for source in sources:
        by_subject[source["subject"]].append(source)

    subject_rows = []
    for subject, subject_sources in sorted(by_subject.items()):
        source_ids = {source["source_id"] for source in subject_sources}
        edges = {
            (source["source_id"], target["site_id"])
            for source in subject_sources
            for target in source["targets"]
        }
        reciprocal_directed_edges = sum(
            1 for source_id, target_id in edges if (target_id, source_id) in edges
        )
        closed_wedges = sum(
            1
            for first, second in edges
            for third in source_ids
            if first != third
            and second != third
            and (second, third) in edges
            and (first, third) in edges
        )
        subject_rows.append(
            {
                "subject": subject,
                "source_count": len(source_ids),
                "edge_count": len(edges),
                "targets_that_are_sources": sum(
                    1 for _, target_id in edges if target_id in source_ids
                ),
                "reciprocal_directed_edges": reciprocal_directed_edges,
                "closed_wedges": closed_wedges,
            }
        )

    output = {
        "schema": "ce.stage3.ccep-endpoint-graph-admission.v1",
        "interpretation": {
            "symmetry_identifiable": any(
                row["reciprocal_directed_edges"] > 0 for row in subject_rows
            ),
            "triangle_inequality_identifiable": any(
                row["closed_wedges"] > 0 for row in subject_rows
            ),
            "local_quadraticity_coordinate_screen_identifiable": True,
            "note": (
                "Coordinate-based local quadraticity can be screened, but graph axioms "
                "require reciprocal or closed source-target observations."
            ),
        },
        "totals": {
            "subject_count": len(by_subject),
            "source_count": len(sources),
            "target_count": sum(len(source["targets"]) for source in sources),
            "targets_that_are_sources": sum(
                row["targets_that_are_sources"] for row in subject_rows
            ),
            "reciprocal_directed_edges": sum(
                row["reciprocal_directed_edges"] for row in subject_rows
            ),
            "subjects_with_reciprocity": sum(
                row["reciprocal_directed_edges"] > 0 for row in subject_rows
            ),
            "closed_wedges": sum(row["closed_wedges"] for row in subject_rows),
            "subjects_with_closed_wedges": sum(
                row["closed_wedges"] > 0 for row in subject_rows
            ),
        },
        "subjects": subject_rows,
    }
    encoded = json.dumps(output, indent=2, sort_keys=True) + "\n"
    OUTPUT_PATH.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
