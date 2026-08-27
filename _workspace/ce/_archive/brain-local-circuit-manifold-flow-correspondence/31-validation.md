# Witness validation record

Status: COMPLETE

## Constructive successor validation

Focused command:

```text
.codex/hooks/python.cmd python docs/6_뇌/국소회로_상태다양체_흐름_대응/repro/verify_constructive.py
```

Result: `PASS`. Maximum graph-invariance residual was `1.351e-15`, exact-lift
parity residual was `1.323e-15`, the C5 observed perturbation `1.110e-01` stayed
below its bound `1.809e-01`, the Lyapunov residual was zero, and the minimum
tested metric quadratic ratio was `1.013937002662`. The repository doctor still
reports missing optional `torch` while importing `reality_stone`; the
standard-library fixture does not depend on it. Full output and interpretation
ceiling are frozen at
`artifacts/epochs/constructive-affine-fiber/31-validation.md`.

## Scope

Validation is restricted to `artifacts/verify_correspondence.py`.  This is the
FAST, dependency-free numerical witness check; no pytest, full suite, scientific
stage, or empirical claim is run.

## Commands and exact output

Command (exit 1):

```text
.codex/hooks/python.cmd doctor
```

```text
Traceback (most recent call last):
  File "C:\Users\22310326\Desktop\CE-BRAIN\.codex\hooks\python_harness.py", line 126, in <module>
    raise SystemExit(main(sys.argv[1:]))
                     ~~~~^^^^^^^^^^^^^^
  File "C:\Users\22310326\Desktop\CE-BRAIN\.codex\hooks\python_harness.py", line 116, in main
    return _doctor(env)
  File "C:\Users\22310326\Desktop\CE-BRAIN\.codex\hooks\python_harness.py", line 49, in _doctor
    import reality_stone
  File "C:\Users\22310326\Desktop\CE-BRAIN\reality_stone\python\reality_stone\__init__.py", line 3, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
```

The doctor failure is an environment prerequisite for the repository-wide
`reality_stone` package, not a dependency of this standard-library witness.
No dependency was installed or execution policy changed.

Command (exit 0):

```text
.codex/hooks/python.cmd python _workspace/ce/brain-local-circuit-manifold-flow-correspondence/artifacts/verify_correspondence.py
```

```text
PASS closed_s1_tangency max_residual=0.0e+00
PASS open_interval_escape endpoint=1.0 in_M=False
PASS cusp_two_branches x=0.015625000 y_plus=0.001953125 y_minus=-0.001953125
PASS discrete_obstructions orientation_det=-1.0 square_images=(0.25,0.25)
PASS metric_nonidentifiability drift_norm_sq=(1.0,1.0) transverse=(1.0,2.0)
PASS all_binary64_witnesses count=5
```

## Evidence boundary

A zero exit status means the five deterministic binary64 predicates passed.  It
does not establish the corresponding analytic results or an empirical neural
correspondence.  The latter remains `UNTESTED`; the proof-level content is the
conditional mathematics in `11-math.md`.

## 실제 생물 자료 STANDARD 검증

DANDI `001701`의 mouse Neuropixels X-maze 세션에서 295개 train-retained unit과 9,746개 100 ms bin을 분석했다. 전역 affine-fiber 후보 NMSE는 `0.9605288`, full VAR은 `0.9610054`였다. 상대 우위는 `0.0496%`로 1% gate에 못 미쳤고 paired block-bootstrap 95% 구간은 `[-0.1140, 0.4095]`였다. $q=1.09555$, $q\kappa=4.29341$이므로 수축·bunching도 실패했다.

행동-조절 R1 후보 NMSE는 `0.9610331`, full VAR+input은 `0.9607531`, base+input은 `0.9563235`였다. 후보는 두 대조군보다 각각 `0.0291%`, `0.4925%` 나빴고 $q_{\max}=1.1061971$이었다. 실제 행동은 1초 이동 행동보다 예측력이 있었지만 구조적 우위 gate는 실패했다. 두 실행 모두 source hash와 임시 NWB 삭제를 확인했고 독립 감사가 유효한 `EMPIRICAL STOP/FAIL`로 판정했다. 확인용 DANDI `001695`는 열지 않았다.
