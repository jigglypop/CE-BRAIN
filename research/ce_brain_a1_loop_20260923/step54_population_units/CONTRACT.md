# A1 54단계 — 같은 방향 E-PG를 하나의 계산 단위로 보면 보존 구조만으로 연속 끌개인가 (사전등록)

작성: 2026-09-25. 연결체 망에는 아무것도 계산하지 않은 상태에서 고정한다(합성 행렬로 구성 함수만 확인).

## 왜

- 뉴런 수준 간격(47–53단계)의 후보 1은 **방향 안 기능적 평균**이다. Noorman 2024도 계산 단위를 "같은 HD 조율을 가진 뉴런 묶음"으로 정의한다.
- 50단계 결과:
  - 방향당 세포 수(4·2·3 무늬)와 방향 결합 편차는 **보존된다**.
  - 우물을 만드는 개체 고유 성분은 방향 **안**의 쌍 수준에 있다.
- 방향 집단 환원(평균장)은 보존 성분을 그대로 두고 방향 안 개체 고유 성분만 평균으로 없앤다. 이 환원이 연속 끌개이고 파리처럼 유지하면, 후보 1이 뉴런 수준 간격을 설명한다.
- 46단계 고리와의 차이: 46단계는 순환 평균 결합이라 세포 수 차이와 방향별 편차를 **지웠다**. 이번에는 둘 다 **남긴다**.

## 망

- **population.** τṙ_a = −r_a + [Σ_b g·Kd[a,b]·r_b + 1]_+
  - Kd[a,b] = (방향 a의 E-PG 평균) × (방향 b의 E-PG 전체에서 받는 K 합), K = E − I(48단계 흐름).
  - 속도 입력은 PEN 좌우 흐름 차의 같은 환원(Ad)이다.
- **population_eqcnt**(보고): 열을 세포 수로 나누어 같은 수로 맞춘 것. 세포 수 효과를 분리한다.
- 이득은 g1 = g*·16/n_EPG의 ±20% 안에서 유지 오차 최소(16위치)다. 47–51단계와 같다.

## 검사

- 48단계 검사 묶음: 64위치 유지, 회전, S1, S2.
- 표류 장: MaleCNS와 hemibrain의 상관, 63가지 원형 이동을 영가설로 쓴다.
- 53단계 걷기→멈춤 절차: 같은 행동 씨앗, U²·느린/빠른.

## 판정

- **연속성.**
  - `population`이 엄격 C1을 통과한 개체가 2곳 이상이면 `CONSERVED_POPULATION_STRUCTURE_CONTINUOUS`.
  - 아니면, 유지율 ≥ 0.8이고 끝 자리 ≥ 12인 개체가 2곳 이상이면 `…_NEARLY_CONTINUOUS`.
  - 둘 다 아니면 `…_HAS_WELLS`.
- **파리 유지.** 걷기→멈춤 U² p ≥ 0.05인 개체가 2곳 이상이면 `CONSISTENT`.
- 보고: 표류 장 상관(보존된 우물이 있으면 개체 사이에 재현될 것), eqcnt와의 차이.

**사전 예측.**
- 세포 수 차이(L8·R8 = 4, L1·R1·L2·R2 = 2)가 방향별 결합으로 완전히 보상되지는 않는다.
- 그래서 `NEARLY_CONTINUOUS` 또는 `HAS_WELLS`이고, 보존 구조이므로 표류 장은 개체 사이에 재현된다(p < 0.05).
- eqcnt는 더 연속적이다.

## 해석 한계

- 평균장 환원은 방향 안 뉴런이 같이 움직인다는 가정이다. 기전(전기 결합, 공통 입력)은 이 검사로 확인하지 않는다.
- FlyWire는 표지 없는 각도를 16칸으로 묶는다.
- 흐름 정규화·대칭화 가정이 있다.
- L4 근거가 아니다.

## 고정 코드

- `population_units.py` sha256 `bb868912d04058a573c8109abe823bbd15e3447d97d0772050505c7706f8e131`
- `../step53_walk_stand_protocol/walk_stand.py` sha256 `89980934daefc9682e9f25866ab85a3ac08bdf44e2e61dcd3e78a9f2fecea360`
- `../step52_standing_bout_test/standing_bouts.py` sha256 `2b70c3baf98b6e261ceffa52aec381634ca83442d38efaf3b01ed4ede67342f1`
- `../step50_heterogeneity_origin/heterogeneity_origin.py` sha256 `afd251beebd049230eb2df5feb7566ffb980757ec6c4191b26057ecbd89f3161`
- `../step48_homeostatic_scaling/homeostatic_ring.py` sha256 `3e1aa31dfeae387a174b1a60a2c1dd995111f501688a4fc7b0f31725e1a3351f`
- `../step47_neuron_level_wells/neuron_level_wells.py` sha256 `08cc5719a8ca6edfb225748986a20489435b6c3f674ac61d7ed366e109684816`
- `../step46_connectome_ring_class/connectome_ring_class.py` sha256 `7faccd33d464709e3ba31d8871a7be2b91df643348c77ad78bd20cd24dd9977c`
- `../step41_few_neuron_attractor/tl_ring.py` sha256 `cd4fe7b44eafb72b81cb04de9f261a77592beafc7d659d7019a2738a73f6f01c`
- `../step41_few_neuron_attractor/few_neuron_ring.py` sha256 `01fc587a5dac22ea68b435f51a4e96f9e55e3182d033240464f396da0e71c91f`
- `../step42_kim_support_ring/kim_support_ring.py` sha256 `273942be42392960184de80d23d64a97ff138008b66077816072a709e5978aba`
