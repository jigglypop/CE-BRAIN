# A1 53단계 — 파리와 같은 걷기→멈춤 절차: 뉴런 수준 배선의 유지와 매끄러운 적분 (사전등록)

작성: 2026-09-25. 연결체 망에는 아무것도 계산하지 않은 상태에서 고정한다. 합성 코사인 고리로 절차만 확인했다(느린/빠른 0.99, 16칸, U² p = 1.0).

## 왜

- 52단계는 실제 배선이 파리 실측(Noorman 2024)과 맞지 않는다고 판정했다.
- 그러나 **단서 해제 절차의 교란**이 있었다. 약한 단서가 범프를 제자리에 두지 못해 시작 위치가 이미 몰려 있었다.
- 파리에서는 걷는 동안의 속도 적분이 범프를 EB 전체로 옮긴다. 같은 절차로 두 가지를 다시 잰다.
  1. 서 있는 구간의 유지(U²).
  2. 느린 회전의 적분. 사용자의 세 번째 간격인 "매끄러운 회전"을 뉴런 수준에서 검사한다.
- 47단계에서 실제 PEN 경로(A_pen)는 뉴런 수준에서 회전 자체를 망가뜨렸다. 그래서 속도 입력은 **각도 평균 PEN 생성자**(47단계 N1의 A1)로 두고, 지형(우물)만 실제 배선으로 둔다. PEN 경로 자체의 불균질은 이 단계의 범위 밖이다.

## 절차 (한 씨앗으로 모든 망에 같은 행동)

| 항목 | 값 |
|---|---|
| 행동 | 걷기 U(1, 4)초와 서기 U(0.3, 2)초를 번갈아 3600초. 걷는 동안 각속도는 OU(표준편차 80°/s, 상관시간 0.3초, 걷기 시작마다 0에서 출발), 서 있을 때 0 |
| 시간 | τ = 0.1초(논문), dt = 0.02τ, PVA는 10 Hz(τ마다) |
| 속도 입력 | v(t) = ω(t)·τ/G. G는 빠른 보정(24°/τ)에서의 단위 v당 범프 속도 |
| 망 | ① **literal** 47단계 N2 + A1 ② **homeostasis** 51단계 s·이득, diag(s)A1 ③ **direction** 46단계 16방향 g*, W의 미분 생성자(46단계와 같음) |
| 유지 | 시작 = 마지막 걷기 프레임의 PVA, 끝 = 마지막 서기 프레임의 PVA(저자 코드의 색인과 같음). Watson U², 순열 500회 |
| 적분 | 걷는 프레임에서 범프 속도와 ω의 원점 통과 기울기를 두 구간에서 잰다: 느린 5 ≤ \|ω\| < 30, 빠른 \|ω\| > 90°/s |
| 방문 | 걷는 프레임의 16칸 점유가 모두 ≥ 1% |
| 보고 | 좌·우 회귀 잔차를 위치 64칸으로 묶어 사인 R²(1·2·3·8·16) |

## 판정 (개체 셋)

- **유지 일치.** U² p ≥ 0.05면 파리 10마리(모두 p > 0.1)와 일치한다.
  - literal: 불일치가 2곳 이상이면 `INCONSISTENT`.
  - homeostasis: 일치가 2곳 이상이면 `CONSISTENT`.
- **매끄러운 적분.** 느린/빠른 이득 비 ∈ [0.8, 1.25] **그리고** 16칸 방문. 망마다 2곳 이상이면 `PASS`.
- **절차 타당성.** direction 망이 유지·적분을 모두 통과한 곳이 2곳 이상이어야 한다.

**사전 예측.**
- literal: 유지 `INCONSISTENT`, 적분 `FAIL`(느린 회전에서 우물에 걸린다).
- homeostasis: 유지는 `CONSISTENT`(52단계에서 MaleCNS·hemibrain 일치). 적분은 불확실하다.
- direction: 모두 통과한다.

## 해석 한계

- 모형에는 잡음이 없다.
- 행동 통계는 합성이다(파리 원자료는 방화벽 때문에 받지 못했다).
- PEN 경로는 각도 평균을 쓴다.
- 시간상수 대응은 가정이다.
- L4 근거가 아니다.

## 고정 코드

- `walk_stand.py` sha256 `89980934daefc9682e9f25866ab85a3ac08bdf44e2e61dcd3e78a9f2fecea360`
- `../step52_standing_bout_test/standing_bouts.py` sha256 `2b70c3baf98b6e261ceffa52aec381634ca83442d38efaf3b01ed4ede67342f1`
- `../step48_homeostatic_scaling/homeostatic_ring.py` sha256 `3e1aa31dfeae387a174b1a60a2c1dd995111f501688a4fc7b0f31725e1a3351f`
- `../step47_neuron_level_wells/neuron_level_wells.py` sha256 `08cc5719a8ca6edfb225748986a20489435b6c3f674ac61d7ed366e109684816`
- `../step46_connectome_ring_class/connectome_ring_class.py` sha256 `7faccd33d464709e3ba31d8871a7be2b91df643348c77ad78bd20cd24dd9977c`
- `../step41_few_neuron_attractor/tl_ring.py` sha256 `cd4fe7b44eafb72b81cb04de9f261a77592beafc7d659d7019a2738a73f6f01c`
- `../step41_few_neuron_attractor/few_neuron_ring.py` sha256 `01fc587a5dac22ea68b435f51a4e96f9e55e3182d033240464f396da0e71c91f`
- `../step42_kim_support_ring/kim_support_ring.py` sha256 `273942be42392960184de80d23d64a97ff138008b66077816072a709e5978aba`
