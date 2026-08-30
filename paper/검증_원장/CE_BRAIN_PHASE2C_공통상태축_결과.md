# CE-BRAIN Phase 2C 공통 상태축 독립 확인 결과

Status: `COMPLETE / STATE_AXIS_NOT_ESTABLISHED / STAGE3_NOT_AUTHORIZED`

## 판정

미개봉 동물 521887의 20 μA 확인 endpoint에서 awake–isoflurane 차이 자체는 강했지만, 앞선 두 동물에서 만든 공통 rank-1 상태축은 그 차이를 예측하지 못했다.

| 항목 | 결과 | 사전 문턱 |
|---|---:|---:|
| 0효과 대비 상태축 개선 | 0.012950 | ≥0.10 및 bootstrap 하한 >0 |
| 개선 bootstrap 하한 | -0.020307 | >0 |
| signed cosine | 0.174757 | ≥0.30 및 bootstrap 하한 >0 |
| cosine bootstrap 하한 | -0.070723 | >0 |
| awake/iso permutation p | 0.001 | ≤0.01 |
| raw global-gain residual R | 0.701467 | ≥0.10 |
| recovery Q | 1.118803 | ≤0.75 |
| Q upper 97.5% | 1.228906 | <1 |

사전 판정은 `STATE_AXIS_NOT_ESTABLISHED`다. `stage3_authorized=false`다.

## 무엇이 실패했고 무엇이 남았나

**[산출]** 521887에는 상태 관련 전달 차이가 존재한다. label permutation에서 999회 모두 관측 거리보다 작았고, raw 평균도 하나의 nonnegative gain으로 설명되지 않았다.

**[산출]** 그러나 그 차이의 방향은 521885·521886에서 학습한 공통 축과 충분히 정렬되지 않았다. 시간 전반과 후반에서도 개선은 각각 1.09%, 1.26%에 그쳤다.

**[산출]** recovery는 awake에 가까워지지 않았다. `D_AR>D_AI`였고 bootstrap 상한도 1을 넘었다.

따라서 반증된 것은 “모든 동물에 공통인 하나의 상태축을 먼저 세우고 그 위에 기하를 얹을 수 있다”는 등록 후보다. 반대로 상태 차이 자체가 없다는 결론은 아니다. 다음 생존 후보는 개체별 안정 축, 전류별 연산자, 시간 비정상성이다.

## 쉬운 말 해석

세 동물 모두 마취 전후에 뇌 반응이 달라지기는 했다. 하지만 앞의 두 동물에서 만든 ‘공통 나침반’이 세 번째 동물의 변화 방향을 거의 가리키지 못했다. 즉 변화는 있는데 모든 동물에게 같은 방향의 지도라고 부르기 어렵다.

이 결과 때문에 지금 바로 거리나 리만 기하를 찾으면 안 된다. 먼저 각 동물 안에서는 방향이 안정적인지, 자극 세기마다 방향이 갈리는지, 시간이 지나며 방향이 흐르는지를 경쟁시켜야 한다.

## 영수증

- schema receipt: `078c69a9a1cd8195cc184c0311e49bfd6f9aca9e0c1aad74216ea19d32b51a7d`
- manifest: `2b364c7914f0b590b65049a2a6638e7704fc7ad9025b907e1453d7ea1086a529`
- result: `ed34301b365c028b082dedbeb4473122b58596ebd52a27c0c1edd3c0389bd386`
- raw recomputation validation: `14e5e82caae6411a32f82d400f30f73f345e7ef9263d1712fb70c97d0be57cdf`, `PASS`
- focused test: `8 passed`

## 다음 허용 경로

미개봉 다중전류 동물에서 다음 네 후보를 confirmation trial로 경쟁시킨다.

1. 0효과;
2. 동물 공통 축;
3. 새 동물 내부 rank-1 축;
4. 전류별 독립 연산자.

이 비교가 개체 이질성·입력 의존성·비정상성을 분리하는 다음 최소 증명 의무다.
