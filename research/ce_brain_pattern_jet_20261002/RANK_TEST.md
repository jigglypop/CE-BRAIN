# Pattern-Jet 다음 검증: K>1 최소차원 스크린 — 2026-10-02

## 질문

이전 단계에서는 실제 자료에서 두 필요조건을 확인했다.

1. 하나의 전역 스칼라 반응관계는 부족하다.
2. 현재 감각만으로는 문맥별 내부상태 분리를 설명할 수 없다.

이번에는 그 다음 질문만 본다.

> **실제 KC 처리자료에서 rank-2 상태가 rank-1보다 새 개체의 미관측 구획 반응을 더 잘 예측하는가?**

이 검사는 Pattern-Jet의 (K>1)에 대한 **필요조건 스크린**이지,
시냅스 하나의 시간 이력 캐스케이드 직접 검증은 아니다.

## 자료

Bergmann et al. 2026 저자 공개
`CorrelationAnalysis/all KC values.csv`를 사용했다.

- 고정 Git blob: `965d7e038fa23ba4226cda865d8802157f0d18c8`
- 31°C에서 각 region의 `TRPA - ctrl` 차이를 사용
- 6개 region
- 11마리 × 7 odor 중 6개 region이 모두 있는 63 sample
- 완전자료가 있는 fly 1–9를 외부 평가에 사용

## 누수 방지

외부 평가는 **leave-one-fly-out**이다.

각 외부 held-out fly에 대해:

1. 나머지 fly에서만 PCA basis를 만든다.
2. 6 region 중 3개만 관측한다.
3. rank-1 또는 rank-2 latent score를 그 3개에서 추정한다.
4. 나머지 3개 region을 예측한다.
5. 가능한 3/3 split 20개를 모두 사용한다.
6. ridge 계수는 외부 test fly를 보지 않고, training fly 내부 leave-one-fly-out으로만 선택한다.

따라서 같은 fly의 다른 odor가 basis 학습으로 test에 새어 들어가는 것을 막았다.

## 결과

| 모델 | pooled held-out RMSE |
|---|---:|
| rank 1 | 0.275575716 |
| rank 2 | 0.273378173 |

rank-2의 상대 개선은 **0.797%**뿐이다.

개체별로는 rank-2가 9마리 중 6마리에서 낮은 RMSE를 보였지만,
정확 양측 sign test는 **p = 0.5078125**다.

즉 개선의 방향이 개체 전체에 일관되다고 볼 근거가 없다.

또한 ridge를 두 rank 모두 training set 내부에서 골랐을 때 최종 선택은 전부 1.0이었다.
정규화 없이 rank-2를 추정하면 작은 관측부분행렬의 불안정성 때문에 오히려 오차가 크게 폭증했으므로,
이번 본 판정에는 nested ridge 결과만 사용한다.

## 판정

**이 자료에서는 K>1을 채택하지 않는다.**

정확히는:

- 국소/구획 상태가 필요하다는 앞선 결과는 유지한다.
- 그러나 그 국소 상태가 최소 2차원이어야 한다는 증거는 이번 정적 KC 자료에서 나오지 않았다.
- rank-2의 0.8% 개선은 생물학적 (K=2) 증거로 세지 않는다.
- 따라서 Pattern-Jet의 (K>1)은 여전히 **미검증**이다.

이것은 Pattern-Jet 전체의 반증도 아니다. 이 자료에는 시간축이 없어서
(u_1,ldots,u_K)의 서로 다른 이완시간을 직접 분리할 수 없기 때문이다.

## 다음으로 필요한 자료

이제 병목은 명확하다. **시간축이 있는 개별 bouton/synapse 자료**가 필요하다.

우선순위:

1. 같은 bouton을 pairing 전·직후·지연 후 반복 측정한 calcium/release 기록
2. KC population clock처럼 odor 이후 여러 지연에서 같은 세포 집단을 읽은 trial-level trace
3. train animal에서 (	au_k)를 고정하고 held-out animal에서 (K=1) 대 (K>1) 예측
4. history shuffle 대조
5. current-activity-only 대조

이 직접 시험에서 (K>1)이 held-out 성능을 올리지 못하면,
Pattern-Jet의 다중 시간모드 부분은 실패로 판정한다.
