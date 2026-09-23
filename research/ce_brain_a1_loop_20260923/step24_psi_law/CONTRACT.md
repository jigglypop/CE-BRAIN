# A1 24단계 — ψ 법칙: PEN 회전각 = PB(이동) 경로와 EB(무이동) 경로의 위상자 합 (사전등록)

작성: 2026-09-24.

**무엇을 이미 알고 무엇을 새로 보나.**
- 23단계 사후 진단에서 **입력원별** 분해를 봤다: Δ7→PEN 경로 52–69°, EPG→PEN 경로 0–16°.
- hemibrain의 EPG→PEN 위치(EB 73%, PB 27%)도 봤다.
- **ROI별 경로 각**은 어느 자료에서도 계산하지 않았다. 방향은 예상되므로, 이 검사는 확인 성격이 강하다.

## 방법

- 23단계의 1차 조화 쌍 기저와 경로 행렬을 쓴다. MaleCNS와 hemibrain은 E1, FlyWire는 표지 없는 θ로 기저를 잡는다.
- PEN 행의 입력 가중치를 시냅스가 놓인 ROI 비율로 나눈다: =W\odot(w_r/w)$, r ∈ {PB, EB, 기타}.
- ROI 자료:
  - MaleCNS: `neuron-roi-v1`(postsynaptic primary ROI).
  - FlyWire: `neuropil` 열.
  - hemibrain: `traced-roi-connections.csv`. 여기서 기타는 총합 − PB − EB다.
- 각 ROI 경로의 회전각을 잰다: $\psi_r=\arg\big(\tilde B^\top(\Gamma_sW_r)B\big)$.
- MaleCNS·FlyWire는 ROI 합이 17단계 행렬과 정확히 같은지 확인한다. 다르면 실행을 중단한다.

## 판정 (세 개체 각각)

- **P1 PB 경로는 해부학 이동량이다.**
  - 좌·우 모두 |ψ_PB|가 [35°, 75°] 안에 있다.
  - |ψ_PB^L + ψ_PB^R| ≤ 20°(좌우 반대).
  - 근거: 문헌은 한 사구체 약 45°, E1 적합값은 55°다.
- **P2 EB 경로는 이동이 없다.** 좌·우 모두 |ψ_EB| ≤ 15°다.

**종합.** 세 개체 모두 P1 ∧ P2이면 `PSI_LAW_SUPPORTED_THREE_INDIVIDUALS`다.

**보고 (판정 아님).**
- 기타 ROI(NO 등) 경로의 각·이득.
- PEN 입력 시냅스의 ROI 비율.
- 전체 ψ = arg(Σ_r Q_r)(선형 항등).

**해석 한계.**
- 선형 1차 섭동의 분해다.
- ψ가 "입력 위치 비율"로 정해진다는 구조 명제이며, 동역학·개입 검증은 아니다.

## 고정 코드

- `psi_law.py` sha256 `69854055d06051a21979f6be1965360889a0506a63f3b8d6546397fe69a18440`
- 불러오는 고정 모듈: 23단계 `isometry.py`(`0c2ef4df…`), 17단계, 22단계 로더
