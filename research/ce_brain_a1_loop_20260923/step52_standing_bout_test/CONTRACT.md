# A1 52단계 — 뉴런 수준 우물은 파리 실측(Noorman 2024)에서 보였어야 하는가 (사전등록)

작성: 2026-09-25. 모형에는 아무것도 계산하지 않은 상태에서 고정한다. 합성 자료로 U² 구현과 민감도만 확인했다.

## 왜

- 47–51단계: 실제 배선을 문자 그대로 쓰면 개체마다 다른 우물 셋이 생긴다. 항상성으로 줄어들지만 없어지지는 않는다.
- 그런데 이것이 파리 실측과 **실제로 충돌하는지**는 아직 확인하지 않았다.
- Noorman et al. 2024(Nat Neurosci 27:2207)의 실측 조건은 다음과 같다.
  - 어둠에서 서 있는 구간(0.3–2초)의 시작·끝 범프 위치를 Watson U²로 비교했다.
  - 10마리 모두 차이가 없었다: p = 0.556, 1, 1, 0.992, 0.998, 1, 0.958, 1, 0.986, 0.118.
  - 모형 시간상수는 τ = 0.1초다.
- 같은 분석을 모형에 그대로 적용해, 우물이 이 실측에서 **검출됐어야 하는지** 판정한다.

## 방법 (논문 Methods와 저자 코드 plotDriftAnalysisFigs.m·watsons_U2.m에 맞춤)

| 항목 | 값 |
|---|---|
| 구간 | 망마다 700개(파리 GC7fA 703개). 시작 위치는 균일하다. 단서 20τ로 범프를 만든 뒤 놓는다. 길이는 U(0.3, 2)초 |
| 위치 | 뉴런 발화율의 집단 벡터(PVA). 시작 = 놓는 순간, 끝 = 구간 끝 |
| 검정 | Watson U²(Zar 식 27.17, 동점 처리), 순열 500회, p = mean(U²_H0 ≥ U²_obs)(저자 정의) |
| 망 (개체별) | ① **literal**: 47단계 N2, 47단계 이득 ② homeostasis: 51단계 스케일링 뒤 ③ **direction**: 46단계 16방향 고리 g*(연속 기준) |
| 시간상수 | τ = 0.1초(주), 0.05초(Kim 2019, 민감도 보고) |
| 보조 보고 | 시작 위치별 표류에 사인 적합한 R²(주파수 1·2·3·8·16). 8·16은 논문과 같고, 1–3은 개체 고유 우물용이다. 파리 원자료에 대한 예측으로 남긴다 |

- 합성 확인: 균일 700개가 우물 셋 쪽으로 거리의 20%를 움직이면 p = 0.09, 40%면 p < 0.002다. **이 검정은 둔감하다.**

## 판정

- **literal 망.** 주 조건(τ = 0.1초)에서 U² p < 0.05인 개체가 2곳 이상이면 `LITERAL_WIRING_INCONSISTENT_WITH_FLY`다. 파리 10마리는 모두 p > 0.1이다. 아니면 `LITERAL_WIRING_CONSISTENT_WITH_FLY`다.
- **절차 타당성.** direction 망은 p ≥ 0.05여야 한다(2곳 이상).

**사전 예측.**
- literal 망은 0.3–2초 안에 우물 쪽으로 20% 이상 움직이지 않는다. 그래서 `CONSISTENT`다. 즉 현재 실측은 우물을 배제하지 못한다.
- 저주파(1–3) R²는 literal 망에서 높다. 파리 원자료로 검사할 수 있는 예측이 된다.

## 해석 한계

- 모형에는 잡음이 없다(실측에는 GCaMP 잡음, 1.1초 평활, 잔여 입력이 있다).
- 시간상수 대응은 가정이다.
- 파리 원자료(figshare 10.25378/janelia.26169355)는 방화벽(AWS WAF 검사) 때문에 자동으로 받지 못했다. 논문에 보고된 값만 쓴다.
- L4 근거가 아니다.

## 고정 코드

- `standing_bouts.py` sha256 `2b70c3baf98b6e261ceffa52aec381634ca83442d38efaf3b01ed4ede67342f1`
- `../step48_homeostatic_scaling/homeostatic_ring.py` sha256 `3e1aa31dfeae387a174b1a60a2c1dd995111f501688a4fc7b0f31725e1a3351f`
- `../step47_neuron_level_wells/neuron_level_wells.py` sha256 `08cc5719a8ca6edfb225748986a20489435b6c3f674ac61d7ed366e109684816`
- `../step46_connectome_ring_class/connectome_ring_class.py` sha256 `7faccd33d464709e3ba31d8871a7be2b91df643348c77ad78bd20cd24dd9977c`
- `../step41_few_neuron_attractor/tl_ring.py` sha256 `cd4fe7b44eafb72b81cb04de9f261a77592beafc7d659d7019a2738a73f6f01c`
- `../step41_few_neuron_attractor/few_neuron_ring.py` sha256 `01fc587a5dac22ea68b435f51a4e96f9e55e3182d033240464f396da0e71c91f`
- `../step42_kim_support_ring/kim_support_ring.py` sha256 `273942be42392960184de80d23d64a97ff138008b66077816072a709e5978aba`
