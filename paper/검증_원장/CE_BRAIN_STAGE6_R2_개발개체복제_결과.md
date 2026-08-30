# CE-BRAIN Stage 6 R2 개발개체 복제 결과

Status: `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED_REPLICATED`

## 결론

R1과 동일한 고정 분석을 새 development subject에 적용했다. 직전 population state의 예측 이득은 더 강하게 반복됐지만, 교차축 순환 후보가 축별 자기상관보다 얻은 추가 이득은 사전 효과크기 문턱에 못 미쳤다.

## 자료와 결과

- subject `740268983`, session `759883607`
- 품질 기준 통과 시각 unit 205개
- 선택 rank 32, ridge 1.0, PCA 설명분산 51.00%

| 모형 | 다음-frame MSE |
|---|---:|
| `R`: 교차축 순환 후보 | 0.0788990 |
| `D`: 축별 자기상관 | 0.0791452 |
| `M`: 강한 mode 제거 | 0.0831961 |
| `N`: 자극 frame 평균 | 0.0837592 |
| `P`: 좌표 의미 permutation | 0.0864762 |

- `R` 대 `N`: 5.8025% 개선, bootstrap 하한 5.4673%.
- `R` 대 `D`: 0.3111% 개선, 하한 0.2371%. 방향은 안정적이지만 사전 문턱 0.5% 미만이다.
- `R` 대 `M`: 5.1650% 개선, 하한 4.8313%.
- `R` 대 `P`: 8.7622% 개선, 하한 8.4184%.

## 두 개발 개체를 함께 읽으면

R1과 R2 모두 자극 평균보다 history 모형이 3.69~5.80% 좋았고, mode 제거와 좌표 permutation 대조보다도 안정적으로 좋았다. 그러나 가장 중요한 `R>D`는 R1에서 -0.043%, R2에서 +0.311%로 둘 다 사전 0.5% 문턱을 넘지 못했다.

따라서 현재 선형 한-frame 계약에서 반복된 사실은 “population history가 유용하다”까지다. “교차축 recurrent degrees of freedom이 그 유용성의 독립 원천이다”는 주장은 확립되지 않았다. 생존 후보가 없으므로 confirmation 4개체는 열지 않는다.

첨부 매뉴얼의 반대 결과 규칙에 따라 Stage 7 기억 궤적은 독립적으로 진행할 수 있지만, 순환차원이 기억 용량의 원천이라는 연결 명제는 제거한다.

## 무결성 영수증

- manifest SHA-256: `86ab4421a3801054991c75e2ebc4419d3b25d1dc87dc66a08458a8abecb74fea`
- result SHA-256: `0e39b7722ea0e70c78d6ff9fa27569194122f1e588060fb75cd95c55067635de`
- validation receipt SHA-256: `4da79ed9d82169df0c25badff096cc1b8f17e11025c9545e4e6253a7112cc3e6`
- raw recomputation: `PASS`

