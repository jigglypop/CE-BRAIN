"""동일 연결의 전류·전압과 독립 프로토콜 입력저항: 고정된 L1 관측 분석."""
import argparse
import hashlib
import json
import platform
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DB = ROOT / "data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"
CONTRACT = HERE / "component_contract.json"
OUTPUT = HERE / "component_result.json"
SEED = 20260905
COHORTS = [("mouse", "VisP", "ex"), ("mouse", "VisP", "in"), ("human", "TCx", "ex")]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_new(path, obj):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)


def folds(groups):
    unique = sorted(set(groups), key=lambda g: hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest())
    mapping = {g: n % 5 for n, g in enumerate(unique)}
    return np.array([mapping[g] for g in groups])


def predict_cv(y, current, resistance, split, groups):
    # 절편별 총 가중치 1: 다수 연결을 기록한 절편이 적합을 독점하지 않는다.
    counts = {g: sum(groups == g) for g in set(groups)}
    weight = np.array([1 / counts[g] for g in groups])
    matrices = [np.column_stack([np.ones(len(y)), current]),
                np.column_stack([np.ones(len(y)), current, resistance])]
    errors, coefficients = [], []
    for x in matrices:
        predictions = np.empty(len(y))
        fold_coefficients = []
        for k in range(5):
            train, test = split != k, split == k
            if train.sum() < 20 or not test.any():
                raise ValueError("분할 표본 부족")
            w = np.sqrt(weight[train])
            beta, _, rank, _ = np.linalg.lstsq(x[train] * w[:, None], y[train] * w, rcond=1e-12)
            if rank != x.shape[1]:
                raise ValueError("설계행렬 식별 불가")
            predictions[test] = x[test] @ beta
            fold_coefficients.append(beta.tolist())
        errors.append((y - predictions) ** 2)
        coefficients.append(fold_coefficients)
    unique = np.array(sorted(set(groups)))
    losses = np.array([[err[groups == g].mean() for g in unique] for err in errors])
    return losses, coefficients


def analyze(rows, cohort):
    # columns: synapse, slice, experiment, post, PSP, PSC, R, pre-R
    rows = [row for row in rows if tuple(row[8:11]) == cohort]
    counts = {"all_synapses": len(rows)}
    valid = []
    for row in rows:
        values = row[4:7]
        if any(v is None or not np.isfinite(v) for v in values):
            continue
        psp, psc, resistance = values
        sign_ok = (psp > 0 and psc < 0) if cohort[2] == "ex" else (psp < 0 and psc > 0)
        if resistance > 0 and sign_ok:
            valid.append(row)
    counts["finite_expected_sign_positive_resistance"] = len(valid)
    groups = np.array([row[1] for row in valid], dtype=int)
    counts["slices"] = len(set(groups))
    counts["postsynaptic_cells"] = len({row[3] for row in valid})
    result = {"cohort": list(cohort), "counts": counts}
    if len(valid) < 100 or len(set(groups)) < 30:
        return dict(result, status="INSUFFICIENT_SAMPLE", biological_endpoint_evaluated=False)
    values = np.array([row[4:7] for row in valid])
    # V→mV, A→pA, ohm→Mohm. 계수는 자연로그 변화율이다.
    y, current, resistance = np.log(abs(values[:, 0]) * 1e3), np.log(abs(values[:, 1]) * 1e12), np.log(values[:, 2] * 1e-6)
    split = folds(groups)
    losses, coefficients = predict_cv(y, current, resistance, split, groups)
    delta = losses[0] - losses[1]
    rng = np.random.default_rng(SEED)
    boot = delta[rng.integers(0, len(delta), size=(2000, len(delta)))].mean(axis=1)
    improvements = float(delta.mean())
    unique_cells = sorted({row[3] for row in valid})
    by_cell = {row[3]: np.log(row[6] * 1e-6) for row in valid}
    permutation = []
    for _ in range(200):
        replacement = dict(zip(unique_cells, rng.permutation([by_cell[c] for c in unique_cells])))
        shuffled = np.array([replacement[row[3]] for row in valid])
        null_loss, _ = predict_cv(y, current, shuffled, split, groups)
        permutation.append(float((null_loss[0] - null_loss[1]).mean()))
    beta = [item[2] for item in coefficients[1]]
    result.update(status="OBSERVATIONAL_COMPONENT_EVALUATED", biological_endpoint_evaluated=True,
                  split_by_slice={str(g): int(k) for g, k in zip(groups, split)},
                  synapse_ids=[row[0] for row in valid],
                  baseline_mse=float(losses[0].mean()), resistance_mse=float(losses[1].mean()),
                  mse_improvement=improvements, relative_mse_reduction=improvements / float(losses[0].mean()),
                  fixed_prediction_slice_bootstrap_interval=np.quantile(boot, [.025, .975]).tolist(),
                  resistance_coefficients_by_fold=beta, all_coefficients=coefficients,
                  shuffle_improvement_q95=float(np.quantile(permutation, .95)),
                  shuffle_tail_fraction=(1 + sum(d >= improvements for d in permutation)) / 201,
                  direction_criterion_met=bool(improvements > 0 and all(b > 0 for b in beta) and improvements > np.quantile(permutation, .95)))
    # presynaptic R: same-complete-subset negative-control comparison, never a causal test.
    mask = np.array([row[7] is not None and np.isfinite(row[7]) and row[7] > 0 for row in valid])
    result["presynaptic_control_n"] = int(mask.sum())
    if mask.sum() >= 100 and len(set(groups[mask])) >= 30:
        subgroups = groups[mask]
        subfolds = folds(subgroups)
        post_loss, _ = predict_cv(y[mask], current[mask], resistance[mask], subfolds, subgroups)
        pre_r = np.log([row[7] * 1e-6 for row, ok in zip(valid, mask) if ok])
        pre_loss, _ = predict_cv(y[mask], current[mask], pre_r, subfolds, subgroups)
        result["same_subset_control"] = {"baseline_mse": float(post_loss[0].mean()),
                                          "post_resistance_mse": float(post_loss[1].mean()),
                                          "pre_resistance_mse": float(pre_loss[1].mean())}
    return result


def freeze():
    manifest = json.loads((HERE / "source_snapshots/source_manifest.json").read_text(encoding="utf-8-sig"))
    source_hashes = {s["file"]: sha(HERE / "source_snapshots" / s["file"]) for s in manifest["sources"]}
    write_new(CONTRACT, {
        "id": "Q-NPF-04-ALLEN-COMPONENT-01", "frozen_at": datetime.now(timezone.utc).isoformat(),
        "question": "독립 프로토콜의 후세포 입력저항이 같은 연결의 PSC를 넘어 PSP 변동을 설명하는가?",
        "objective_chain": "C19에서 확인한 막·관측 보정의 필요성을 실제 세포 연결 자료에서 점검. 전체 뇌 구조나 CE 매개 검증 아님.",
        "bio_starting_mechanism": "수동막 C*dV/dt+V/R=I의 전류-전압 필터. 과도응답 PSP peak=PSC peak*R라는 항등식을 가정하지 않음.",
        "ce_delta": "없음. 기존 생물 기준선의 구성요소 관측이며 CE 고유성을 시험하지 않음.",
        "measurement_model": "다른 clamp 시행의 휴지기 평균 적합 PSP(V), PSC(A), 별도 intrinsic 긴 전류 계단 프로토콜 R(ohm). 통계적 독립이나 동시 측정 보장 없음.",
        "provenance": "Allen synphys r2.1 small, schema22, DB 생성일 2021-12-21. 참조 upstream 코드는 고정했으나 원 DB 생성 commit과 동일하다고 확인한 것은 아님.",
        "db_sha256": sha(DB), "db_bytes": DB.stat().st_size, "source_hashes": source_hashes,
        "code_sha256": sha(Path(__file__)), "join_code_sha256": sha(HERE / "inspect_overlap.py"),
        "overlap_receipt_sha256": sha(HERE / "overlap_receipt.json"),
        "runtime": {"executable": sys.executable, "python": platform.python_version(), "numpy": np.__version__},
        "prior_access": "메타데이터·ID결합·결측 건수만 열람. 반응값과 상관·모델 결과는 아직 열람하지 않음.",
        "primary": list(COHORTS[0]), "secondary": [list(c) for c in COHORTS[1:]],
        "observations": "모든 해당 synapse에서 유한한 PSP/PSC/R, R>0, ex PSP>0 PSC<0; in PSP<0 PSC>0. 사후 clipping·이상값 삭제 없음. 동일 post.cell_id 및 experiment_id 결합.",
        "models": "M0: ln|PSP_mV|=a+b ln|PSC_pA|; M1: M0+c ln(R_Mohm). 자유도2 대3, 절편별 총가중치1의 OLS, rcond1e-12, ridge 없음.",
        "split": "seed20260905와 slice ID의 SHA256 순서로 5등분. 같은 절편의 모든 세포·연결을 한 fold에 배정. 최소100연결·30절편, 각 훈련fold 최소20연결. donor ID 미확인으로 동물 단위 독립은 주장 불가.",
        "endpoint": "절편별 평균 log PSP 제곱오차를 동등 평균한 M0-M1. 5fold는 분석 내 교차검증이며 독립 종단확인 또는 L2가 아님.",
        "direction_rule": "primary MSE차>0, 모든 훈련fold c>0, 세포별 R 200회 무작위 재배정 개선의95백분위 초과를 모두 만족해야 기술적 방향 기준 충족. 인과 p값 아님.",
        "controls": "R을 post.cell_id 단위로 섞어 같은 세포 반복을 유지. pre-R도 있는 동일 부분집합에서 post-R 모델과 pre-R 모델 비교. 세포형·절편·donor 교란을 완전히 통제하지 못함.",
        "uncertainty": "seed20260905, 고정 OOF 예측 손실을 절편단위2000회 bootstrap한2.5/97.5백분위. 모델 재적합·donor 상관·측정오차를 포함하지 않는 기술적 구간.",
        "falsifier": "M1이 교차검증 오차를 개선하지 않거나 계수 방향이 일관되지 않으면 이 코호트에서 유용한 보정이라는 방향 기준 미충족. 전체 생물 법칙 반증으로 확대하지 않음.",
        "revision_trigger": "입력·ID·단위 오류면 중단 기록 후 별도 판본. 결과를 본 뒤 포함·문턱·split을 바꾸지 않음.",
        "claim_ceiling": "BIO_EVIDENCE_L1_COMPONENT_OBSERVATION; full chain remains L0/unestablished",
        "next_gate": "입력·소스·실행기 해시, 무결성·ID검사 통과 후 고정 분석1회 실행. 결과와 한계 기록."})
    print("분석 계약 고정 완료:", CONTRACT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        rng = np.random.default_rng(19)
        groups = np.repeat(np.arange(50), 4)
        x, r = rng.normal(size=(2, 200))
        y = 2 + .7*x + .9*r
        split = folds(groups)
        loss, beta = predict_cv(y, x, r, split, groups)
        assert loss[1].max() < 1e-20 and loss[0].mean() > .1
        assert all(abs(b[2]-.9) < 1e-10 for b in beta[1])
        assert all(len(set(split[groups == g])) == 1 for g in set(groups))
        print("합성 회귀 복원·절편 분할 검사 통과")
        return
    if args.freeze:
        freeze()
        return
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if OUTPUT.exists():
        raise RuntimeError("결과가 이미 있습니다. 기존 결과를 덮어쓰지 않습니다.")
    assert c["db_sha256"] == sha(DB) and c["code_sha256"] == sha(Path(__file__))
    assert c["join_code_sha256"] == sha(HERE / "inspect_overlap.py")
    assert c["overlap_receipt_sha256"] == sha(HERE / "overlap_receipt.json")
    assert c["runtime"] == {"executable": sys.executable, "python": platform.python_version(), "numpy": np.__version__}
    for name, expected in c["source_hashes"].items():
        assert sha(HERE / "source_snapshots" / name) == expected
    from inspect_overlap import JOIN
    audit = json.loads((HERE / "overlap_receipt.json").read_text(encoding="utf-8"))
    assert audit["integrity"] == "ok" and all(audit[k] == 0 for k in ("duplicate_intrinsic_cells", "duplicate_synapse_pairs", "identity_mismatches"))
    with sqlite3.connect(DB.as_uri()+"?mode=ro", uri=True) as db:
        rows = db.execute("SELECT s.id,sl.id,e.id,post.id,s.psp_amplitude,s.psc_amplitude,i.input_resistance,ip.input_resistance,sl.species,e.target_region,s.synapse_type " + JOIN + " LEFT JOIN intrinsic ip ON ip.cell_id=pre.id ORDER BY s.id").fetchall()
    result = {"contract_sha256": sha(CONTRACT), "completed_at": datetime.now(timezone.utc).isoformat(),
              "cohorts": [analyze(rows, cohort) for cohort in COHORTS], "claim_ceiling": c["claim_ceiling"]}
    write_new(OUTPUT, result)
    for cohort in result["cohorts"]:
        print(json.dumps({k:v for k,v in cohort.items() if k not in ("synapse_ids", "split_by_slice", "all_coefficients")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
