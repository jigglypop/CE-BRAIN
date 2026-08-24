# BA-SRM9 최종 보고서 — 물리시간 유효차원 후보군의 F2-C 중단

Status: COMPLETE

Final disposition: `SYNTHETIC_F2C_FUTILITY_STOP / REAL_ENDPOINT_UNOPENED`

## 초록

이 연구는 불규칙한 물리시간과 결측·잡음 아래에서 유효차원 궤적을
복원하는 48개 후보를 단계적으로 제거하는 합성 검증이다. BA-SRM9는
선행 BA-SRM8의 JUMP 센서 혼합 결함만 고쳤으며 후보 식, 점수, 임계값,
패널과 실데이터 경계를 바꾸지 않았다. F2-A에서 24개, F2-B에서 20개가
남았지만, F2-C에서는 20개 모두 ART10 순위회복 조건을 넘지 못해
`FUTILITY_KILL`되었다. 따라서 F2-D, 확인, 행동값, 모델 적합과 실제 뇌
endpoint는 열리지 않았으며, 이 결과는 뇌·의식·AGI의 증거나 반증이
아니다.

## 수학적 핵심과 증명 범위

**[정리: 조건부 PSD–resolvent 경계]** 비음수 물리시간 가중치, 유효한
유효표본수 조건과 양의 보정척도 아래에서 가중 공분산
$\widetilde G$는 양의 준정부호다. 이때

$$
S=\widetilde G(\widetilde G+I)^{-1},
\qquad d_{\rm eff}=\operatorname{tr}S
$$

의 고윳값은 $\mu_k/(1+\mu_k)$이므로 $0\le d_{\rm eff}\le r_*$이고,
동결된 정규화 $Q=d_{\rm eff}/r_*$는 $[0,1]$에 놓인다. 증명은
$\widetilde G$의 스펙트럼 분해에 이 스칼라 함수를 적용하면 끝난다.
이 정리는 분석 장치의 범위를 말할 뿐, $\widetilde G$가 생물학적
Riemann metric이라는 결론을 주지 않는다.

**[정리: JUMP 관측혼합 보조정리]** 직교행렬 $H$의 처음 $r$개 열을
$H_r$라 하고 $\xi\sim N(0,I_r)$, $x=H_r\xi$로 두면

$$
\operatorname{Cov}(x)=H_rH_r^{\mathsf T}
$$

는 rank $r$의 직교사영이며 영이 아닌 고윳값은 모두 $1$이다. 실제로
$H_r^{\mathsf T}H_r=I_r$이므로 위 행렬은 멱등이고 trace가 $r$이다.
BA-SRM9 fixture는 각 관측 채널이 jump 전후 부분공간에서 양의 에너지를
갖는지도 별도로 검사했다. 이 보조정리는 BA-SRM8의 영분산 센서 결함을
수리하지만 후보 $Q$의 정확성이나 뇌의 차원을 증명하지 않는다.

## 검증 설계

F2-C는 F2-B에서 동결된 20개 후보를 BLOCK30과 ART10에서 평가했다.
각 시나리오의 여덟 seed에서 복원 궤적과 정답 궤적 사이의 Spearman
상관과 NMAE를 계산하고, 두 시나리오 모두에서

$$
\operatorname{median}(\rho)\ge0.80,
\qquad
\operatorname{median}(\operatorname{NMAE})\le0.20
$$

일 때만 후보를 통과시켰다. 통과 후보가 있을 때만 오차, 상관, 동결
ISO false-alarm rate와 실행시간 순으로 최대 16개를 남기므로, 이번
결과에는 cap이나 tie-break가 개입하지 않았다.

## 결과

**[산출: 동결 합성 비교]** F2-C preflight는 16개 시나리오–seed cache와
20개 후보 입력을 모두 통과했다. BLOCK30 중앙 상관은 후보 전체에서
`0.9284251656475162..0.9788390822185931`이었고, ART10 중앙 상관은
`0.6136981053328..0.7404632890000811`이었다. NMAE 조건은 모두
통과했지만 ART10 상관의 최댓값조차 기준보다 약 `0.05954` 낮았다.
따라서 결과는 `20 FUTILITY_KILL / 0 PROMOTE`이며 승격 배열은 비어 있다.

이 결과가 제거하는 것은 이 동결 후보군이 ART10까지 견디면서 동결
회복 조건을 만족한다는 주장이다. PSD–resolvent 정리, JUMP 혼합
보조정리, 물리시간 공분산을 분석 장치로 사용할 가능성 자체는 이
수치 실패로 반박되지 않는다. 반대로 앞 단계의 합성 성능도 실제
뉴런 상태, 시냅스 간선, Riemann metric, 자아, 의식의 차원, 해마 주소계
또는 AGI 구조에 대한 증거로 승격할 수 없다.

## 봉인 경계와 다음 문제

Receipt는 `behavior_loaded=false`, `model_fit=false`,
`real_endpoint_opened=false`, `biological_claim=false`,
`downstream_authorized=false`를 기록한다. 그러므로 F2-D, 확인, F2R,
행동 분석과 실제 자료를 실행하면 이번 계약을 위반한다. 같은 후보를
살리기 위해 ART10 임계값, seed, 패널, 점수 또는 cap을 바꾸는 사후
조정도 금지한다.

다음 연구가 재개되려면 ART10에서 순위정보가 무너지는 이유를 겨냥한
서로 다른 후보 메커니즘과 adverse control을 새 계약에서 먼저
동결해야 한다. 그 후보는 작은 합성 단계부터 다시 시작해야 하며,
이번 F2-C와 동일한 자료를 독립 확인으로 재사용할 수 없다. 실제 뇌로
이동하려면 별도로 source-locked measurement model, held-out recording과
개입 가능한 falsifier가 필요하다.

## 재현 경로

F2-C receipt SHA-256은
`a43e14da1e099f30d3cb970f35db199159be83916b9ce33e685f494641958bf2`이고,
runner SHA-256은
`361fa1b7b8d6af1576d5a02d76159f5f9e2a6215ecedf5b95bc66cee1e209b80`이다.
다음 명령은 one-shot F2-C를 다시 실행하지 않고 frozen receipt chain과
gate를 검증한다.

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-physical-time-effective-dimension-funnel-v2-20260823\artifacts\validate_f2c_receipt.py
```

검증 결과는 `status=PASS`, 후보 20개, `FUTILITY_KILL=20`, `PROMOTE=0`이다.
전체 테스트나 downstream scientific stage는 실행하지 않았다.

## 참고자료

실데이터 provenance로 동결된 Hallinen et al., *eLife* 자료
([DOI 10.7554/eLife.66135](https://doi.org/10.7554/eLife.66135))와 OSF snapshot
([DOI 10.17605/OSF.IO/DPR3H](https://doi.org/10.17605/OSF.IO/DPR3H))은 이번
F2-C에서 열리지 않았다. 따라서 이 인용은 향후 입력의 출처 경계일 뿐
이번 합성 STOP을 경험적 뇌 결과로 바꾸지 않는다.
