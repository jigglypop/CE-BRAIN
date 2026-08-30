# CE-BRAIN Stage 6 R1 순환예측 개발 결과

Status: `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`

## 한 문장 결론

같은 영화를 반복해서 볼 때 직전 population state는 다음 프레임 반응 예측에 분명히 유용했지만, 뉴런 잠재축 사이의 교차 순환을 허용한 모형은 각 축의 자기상관만 쓰는 단순 모형보다 낫지 않았다. 따라서 이 개발 세션에서는 순환차원이 미래 예측력의 독립 원천이라고 할 수 없다.

## 자료와 분할

- development subject `707296975`, session `721123822`
- 시각영역 품질 기준을 통과한 unit 214개
- 자연영화 900프레임 반복 20회
- 첫 블록의 8회 train, 2회 validation
- 시간적으로 떨어진 두 번째 블록 10회 development test
- 선택 rank 32, ridge 1.0, PCA 설명분산 40.16%

confirmation subject와 DANDI `001695`는 열지 않았다.

## 손실과 사전 비교

| 모형 | 다음-frame MSE |
|---|---:|
| `D`: 축별 자기상관 | 0.0687157 |
| `R`: 교차축 순환 후보 | 0.0687455 |
| `M`: 강한 mode 제거 | 0.0713667 |
| `N`: 자극 frame 평균 | 0.0713826 |
| `P`: 좌표 의미 permutation | 0.0731878 |

- `R` 대 `N`: 3.6943% 개선, bootstrap 95% 하한 3.2248%. history 유용성 문턱은 통과했다.
- `R` 대 `D`: -0.0433% 개선, 하한 -0.1997%. 교차축 순환 분리 문턱은 실패했다.
- `R` 대 `M`: 3.6730% 개선, 하한 3.2264%. 강한 population mode를 제거하면 예측력이 떨어졌다.
- `R` 대 `P`: 6.0698% 개선, 하한 5.5250%. 좌표 의미를 섞은 대조보다 원래 동역학이 나았다.

사전 계약은 `R>N`, `R>D`, `R>M`을 모두 요구했다. `R>D`가 실패했으므로 판정은 `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`다.

## 쉬운 해석

영화관 관객을 예로 들면, 각 관객이 방금 얼마나 놀랐는지만 알아도 다음 순간 반응을 꽤 잘 예측했다. 관객 A의 반응이 관객 B·C의 다음 반응을 추가로 설명하는 복잡한 관계까지 넣어도 더 좋아지지 않았다. 여러 사람의 집단 모드는 중요했지만, 그것이 서로 물고 도는 순환 때문이라고 분리되지는 않았다.

이 결과는 순환회로가 없다는 뜻이 아니다. 관측된 한 프레임 지연에서는 축별 지속성만으로 교차축 VAR의 이득을 모두 설명할 수 있었다는 뜻이다. 더 긴 지연, 비선형 동역학, 다른 개체에서는 달라질 수 있으므로 동일 고정 분석의 개발 개체 복제가 다음 의무다.

## 무결성 영수증

- manifest SHA-256: `652f8c6de2e8c3df0fee198d499f1cdac3b5bc67fea55e5fb018d6abe4afc7f6`
- result SHA-256: `a1fbd5ca7dbda491e99479145d29e25635ebeed9bca6625f25184a2489fe1ab0`
- validation receipt SHA-256: `46cb33b6aa70407890caa0a540ff64df9a0f2dd04997b3f05a54ddb95006a819`
- raw recomputation: `PASS`

