import importlib.util
import sys
from pathlib import Path

import numpy as np


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("stage0", HERE / "stage0_synthetic_discrimination.py")
stage0 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage0)


def test_seed_split_and_generator_identity_are_deterministic():
    first, identity_a = stage0.generate("B", 0)
    second, identity_b = stage0.generate("B", 0)
    assert identity_a == identity_b
    assert len(set(identity_a["split_sha256"].values())) == 3
    for split in ("train", "validation", "unseen"):
        assert np.array_equal(first[split][0], second[split][0])
        assert np.array_equal(first[split][1], second[split][1])


def test_selection_api_has_no_unseen_argument_and_descriptor_is_serializable():
    splits, _ = stage0.generate("A", 1)
    selection = stage0.select_model(splits["train"], splits["validation"])
    assert selection["descriptor"]["model_sha256"] == stage0._model_hash(selection["winner"])
    descriptor = stage0.json.dumps(selection["descriptor"], sort_keys=True, separators=(",", ":"))
    assert len(stage0._sha((descriptor + "\n").encode())) == 64


def test_execute_rejects_unsealed_run(tmp_path):
    try:
        stage0.execute(tmp_path)
        raise AssertionError("unsealed execution accepted")
    except RuntimeError as exc:
        assert "missing manifest" in str(exc)


def test_split_overlap_and_unstable_rollout_fail_closed():
    splits, identity = stage0.generate("G", 2)
    identity["trajectory_sha256"]["unseen"][0] = identity["trajectory_sha256"]["train"][0]
    try:
        stage0._verify_split_identity(identity)
        raise AssertionError("trajectory overlap accepted")
    except RuntimeError as exc:
        assert "split overlap" in str(exc)
    model = {"kind": "G", "ridge": 1e-8, "parameters": 1,
             "weights": np.zeros((1 + 2 * stage0.NODES, stage0.NODES))}
    model["weights"][1:1 + stage0.NODES] = 2.0 * np.eye(stage0.NODES)
    rolled = stage0._rollout(model, *splits["validation"])
    assert not np.all(np.isfinite(rolled))


def test_aggregate_rejects_incomplete_population():
    try:
        stage0.aggregate([])
        raise AssertionError("incomplete replicate set accepted")
    except RuntimeError as exc:
        assert "replicate population" in str(exc)


def test_all_frozen_generators_are_finite_and_identity_valid():
    for world in stage0.WORLDS:
        for replicate in range(12):
            splits, identity = stage0.generate(world, replicate)
            stage0._verify_split_identity(identity)
            for states, inputs in splits.values():
                assert np.all(np.isfinite(states))
                assert np.all(np.isfinite(inputs))
                assert np.max(np.abs(states)) < stage0.MAX_ABS_STATE
