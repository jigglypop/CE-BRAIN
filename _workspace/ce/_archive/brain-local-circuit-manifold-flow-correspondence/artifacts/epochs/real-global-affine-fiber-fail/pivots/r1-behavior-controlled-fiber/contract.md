# 구조 피벗 계약: r1-behavior-controlled-fiber

Status: COMPLETE

반례 식별자: `real-global-affine-fiber-fail`

구조 지문: `observed-position-head-direction-trial-input-enters-base-and-fiber`

구조 변경 종류: `interaction`

바뀌는 항: exogenous_behavior_input

판별 예측: Frozen observed behavior inputs improve held-out neural prediction beyond base+input and input-only controls while visited-input fiber operators meet the declared local stability rule

중단 조건: No preregistered improvement over both base+input controls, shifted behavior matches the effect, or local stability fails

## 실제 데이터·측정 계약

이 경로는 합성 데이터를 사용하지 않는다. 개발 자료는 해시가 이미 고정된
DANDI `001701@0.260120.0303`의 `BaggySweatpants-DY15-g1` 실제 Neuropixels
NWB 하나다. 이 경로는 앞선 전역 아핀 결과를 본 뒤 제안됐으므로 001701의
모든 수치는 **구조 개발**일 뿐 독립 확인이 아니다. DANDI
`001695@0.260319.2023`은 이 계약과 구현이 동결되기 전에는 열지 않는다.

신경 측정모형, 100 ms bin, train-only unit retention/Anscombe/scaling/PCA,
시간순 split, gap 제거와 bootstrap은 `real-dandi-001701/00-contract.md`를 그대로
상속한다. 새 입력 $u_t$만 아래처럼 추가한다.

$$
\phi(u_t)=(x_t,y_t,\sin\theta_t,\cos\theta_t,v^x_t,v^y_t).
$$

위치와 head direction은 다음 outcome-blind schema audit에서 유일하게 확인된
NWB stream만 사용한다.

| variable | exact data path | shape | timebase |
|---|---|---:|---|
| position | `processing/behavior/Position/position/data` | `(58000,2)` float64 | parent TimeSeries `starting_time=3.907897`, `rate=60.0 Hz` |
| head direction | `processing/behavior/CompassDirection/head direction/data` | `(58000,)` float64 | parent TimeSeries `starting_time=3.907897`, `rate=60.0 Hz` |

명시적 `timestamps`가 없는 이 두 stream은 표준 NWB 규칙 표본축
$t_k=3.907897+k/60$ seconds로 해독한다. 위치는 bin center에 선형 보간하고, 방향은 sin/cos를 각각
선형 보간한 뒤 다시 정규화한다. 속도는 100 ms backward difference다. 원 관측
간격이 500 ms를 넘는 구간, coverage 바깥 bin, 방향 norm이 $10^{-8}$ 미만인
bin은 제외한다. 입력 중심·scale도 train valid bin만 사용한다. neural 값으로
behavior feature나 상태를 선택하지 않는다.

## 고정 후보식

train-only PCA 차원 $d\in\{2,4,8\}$에 대해

$$
z_{t+1}=Bz_t+D\phi_t+b,
$$

$$
y_{t+1}=A_0y_t+Cz_t+E\phi_t
+\sum_{j=1}^{6}\phi_{tj}\operatorname{diag}(a_j)y_t+e.
$$

즉 $A(\phi)=A_0+\sum_j\phi_j\operatorname{diag}(a_j)$다. 모든 계수는 같은
unpenalized-intercept ridge로 적합한다. $d$와
$\lambda\in\{10^{-4},10^{-3},10^{-2},10^{-1},1,10\}$은 001701 development
NMSE로만 고른다. 정확 동률은 작은 $d$, 큰 $\lambda$ 순이다.

## 대조군과 판정

- `base+input`: 같은 $z,\phi$로 $z_{t+1}$과 $y_{t+1}=Cz_t+E\phi_t+e$를 적합.
- `full-VAR+input`: $x_{t+1}=Rx_t+S\phi_t+r$; 같은 ridge menu를 독립 선택.
- `input-only`: $x_{t+1}=S\phi_t+r$.
- `shifted-input`: 각 split 안에서 behavior만 100 bin 지연하고 wrap 없이 refit.
- persistence와 train mean은 보조 기준으로 보존.

001701 내부 평가에서는 후보가 `base+input`과 `full-VAR+input` 각각보다 NMSE
1% 이상 낮고, 100-bin moving-block bootstrap 95% paired-improvement 구간 두 개의
하한이 모두 0보다 커야 한다. 또한 방문한 평가 입력 전체에서

$$
q_{\max}=\max_t\|A(\phi_t)\|_2<1
$$

이어야 하며 shifted-input이 실제 입력 후보와 같거나 좋아서는 안 된다. 하나라도
실패하면 R1은 `STOP`이고 001695를 열지 않는다. 내부 개발이 모두 통과할 때만
동일 feature·penalty·판정 규칙을 001695의 사전 선택 asset에 한 번 적용한다.

## 주장 상한

001701 통과는 outcome-informed L2 개발 적합도일 뿐이다. 001695 독립 재현 전에는
생물학적 제어 수축, 회로 인과성, 불변다양체, 연속 생성자, 계량 또는 의식을
주장하지 않는다. 위치·방향 입력은 공통 감각·각성의 proxy일 수 있다.
