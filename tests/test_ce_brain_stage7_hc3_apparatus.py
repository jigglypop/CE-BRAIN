from pathlib import Path

import pytest

from examples.brain import ce_brain_stage7_hc3_apparatus as apparatus


def test_cluster_receipt_matches_labels_to_times(tmp_path):
    prefix = tmp_path / "s"
    Path(f"{prefix}.clu.1").write_text("4\n2\n3\n2\n", encoding="utf-8")
    Path(f"{prefix}.res.1").write_text("10\n20\n30\n", encoding="utf-8")
    assert apparatus.cluster_receipt(prefix, 1) == {"declared_clusters": 4, "spikes": 3, "observed_labels": 2}


def test_cluster_receipt_rejects_mismatch(tmp_path):
    prefix = tmp_path / "s"
    Path(f"{prefix}.clu.1").write_text("3\n2\n", encoding="utf-8")
    Path(f"{prefix}.res.1").write_text("10\n20\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="mismatch"):
        apparatus.cluster_receipt(prefix, 1)

