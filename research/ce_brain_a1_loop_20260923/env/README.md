# CE-BRAIN A1 연구 실행 환경

A1 단계는 고정 환경(`uv.lock`)과 빠른 경로(`../fastcore/`)로 돌린다. 빠른 경로는 봉인된 56–63단계 코드와 같은 결과를 낸다.

## 설치 (한 번)

```sh
cd research/ce_brain_a1_loop_20260923/env
UV_LINK_MODE=copy uv sync --python C:/Users/dongh/AppData/Local/Programs/Python/Python311/python.exe
```

- Python 3.11을 쓴다. WDAC가 uv의 Python 3.14를 막는다.
- `.venv/`(약 440 MB)와 numba 캐시(`__pycache__`)는 git에서 제외된다. 판본과 해시는 `uv.lock`에 잠긴다.
- 2026-09-26 잠금: Python 3.11.9, numpy 2.4.6, scipy 1.17.1, numba 0.67.0, pyarrow 25.0.1, pandas 3.0.6, h5py 3.16.0.

## 실행

```sh
cd research/ce_brain_a1_loop_20260923
env/py stepNN_x/script.py        # Git Bash
env\py.cmd stepNN_x\script.py    # cmd / PowerShell
```

실행기는 프로세스마다 BLAS·OpenMP 스레드를 1로 고정한다. 이미 설정돼 있으면 그 값을 쓴다.
- 스레드 수가 바뀌면 행렬곱의 덧셈 순서가 바뀌어 끝자리가 달라진다. 예를 들어 584 시드의 NREM 결맞음 C는 스레드 12개일 때 …727, 1개일 때 …726이다.
- 고정하면 직렬 실행과 병렬 실행이 비트 단위로 같다.
- 봉인된 옛 단계는 스레드 12개로 돌았다. 그래서 이 실행기로 다시 돌리면 일부 값의 끝자리(10⁻¹⁶)가 다를 수 있다.

## 빠른 경로 (`../fastcore/`)

| 파일 | 내용 |
|---|---|
| `ring_kernels.py` | numba로 컴파일한 1 ms 적분 커널과 보조 함수. 커널은 기본 고리, 단기 가소성, 발화 적응이다. 보조 함수는 행렬곱(행마다 같은 덧셈 순서), 제자리 von Mises 입력, 머리 방향 OU 걷기, 스파이크 솎기(float32 산술 그대로)다. |
| `models.py` | 58단계 일정표와 58·61·62·63 모형 시뮬레이터. 난수를 옛 코드와 같은 순서로 뽑는다. 발화율 배열은 뉴런별로 연속 저장한다. |
| `analysis.py` | 58단계와 같은 스파이크를 무압축으로 저장한다. 56단계 구조 지표(C, 고리 지수)는 1000회 순열 없이 계산한다. |
| `batch.py` | 프로세스 병렬 실행기. 기본 작업자는 6개(물리 코어 수)다. 남은 메모리를 보고 작업자 수를 줄이고, 메모리 오류가 난 세션은 작업자를 절반으로 줄여 한 번 더 돌린다. |
| `check_equivalence.py` → `equivalence.json` | 봉인 코드와의 대조 기록. |
| `check_batch.py` → `batch_check.json` | 병렬 결과가 직렬과 같은지, 처리량이 얼마인지 기록한다. |

### 단계 스크립트에서 쓰는 법

```python
import sys
from pathlib import Path
import numpy as np

LOOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOOP / "fastcore"))       # 이름으로 불러야 numba 캐시가 어느 폴더에서나 잡힌다
import analysis as an, batch, models as fm

def run_one(spec):                               # 작업자: dict 하나를 받아 dict 하나를 돌려준다
    rng = np.random.default_rng(spec["seed"])
    sched = fm.schedule(rng)
    rates = fm.sim_pull(spec["sigma"], rng, sched, spec["a"], spec["s"], spec["d_wake"])
    ...

if __name__ == "__main__":                       # Windows spawn: 본 작업은 반드시 이 안에
    rows = batch.run_specs(specs, f"{Path(__file__).resolve()}:run_one")
```

단계 스크립트 이름을 `models.py`, `analysis.py`, `batch.py`, `ring_kernels.py`로 짓지 않는다. 모듈 이름이 겹친다.

## 검증 (2026-09-26)

**봉인 코드와의 대조**(`equivalence.json`): 네 모형 모두 "ALL SAME"이다.
- 일정표 배열과 그 뒤 난수 상태가 같다.
- 같은 발화율에서 나온 스파이크 배열 전체와 난수 상태가 같다.
- 62단계 지표, 57단계 분석, 56단계 C·고리 지수가 모든 자리까지 같다.
- 발화율 차이는 최대 1.5×10⁻⁸이다. 옛 코드가 numpy `W @ r`을 쓰기 때문에 생긴다.

| 모형 | 시뮬레이션 옛 → 새 (초) | 세션 전체 옛 → 새 (초) |
|---|---|---|
| 58 기본 | 30.6 → 0.96 | 38.5 → 2.1 |
| 61 단기 가소성 | 98.9 → 1.01 | 107 → 2.0 |
| 62 붙잡기 | 48.6 → 1.89 | 57 → 3.0 |
| 63 떠돌기 | 46.2 → 1.94 | 55 → 3.2 |

세션 전체는 일정표, 시뮬레이션, 스파이크, 62단계 지표, 구조 지표를 합한 시간이다. 옛 경로의 구조 지표는 56단계 analyse로 약 4.8초가 걸린다.

**병렬 실행**(`batch_check.json`): 세션 24개를 돌렸다.
- 작업자 3·6·9개에서 결과가 직렬과 비트 단위로 같다.
- 처리량은 초당 0.93, 1.18, 1.18세션이다.
- 물리 6코어에서 포화된다. VS Code, 크롬 등 다른 프로그램이 켜진 상태에서 잰 값이다.
- 작업자 하나의 최대 커밋 메모리는 0.58 GB다.

## 남은 한계

- 새 세션 한 개의 약 절반은 난수 생성이다. 잡음 정규난수에 0.6초, 스파이크 균등난수에 0.5초가 든다. 난수 순서를 바꾸면 봉인 결과와 같지 않게 되므로 그대로 둔다.
- 한 프로세스에서 일정표를 처음 호출할 때 numba 캐시를 읽느라 약 0.3초가 더 든다.
- 이 컴퓨터는 커밋 한도 70 GB 가운데 약 60 GB가 다른 프로그램에 잡혀 있었다. 병렬 작업자 수는 그때그때 남은 메모리가 정한다.

## 계약서에 남길 것

새 단계의 CONTRACT에는 단계 코드 해시와 함께 `env/uv.lock`과 쓰는 `fastcore/*.py`의 sha256을 적는다.
