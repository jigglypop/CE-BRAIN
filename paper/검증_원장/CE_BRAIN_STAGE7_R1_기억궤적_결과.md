# CE-BRAIN Stage 7 R1 기억궤적 개발 결과

Status: `DEVELOPMENT_RESULT_RECOMPUTED`

## 판정

`TRAJECTORY_MEMORY_NOT_ESTABLISHED`

이 판정은 “해마에 replay가 없다”는 반증이 아니다. 고정한 한 세션·한 위치 해독기·한 ripple 검출기에서, 기억 궤적이라고 해석하기 위한 사전 문턱을 넘지 못했다는 뜻이다.

## 봉인과 자료

- CRCNS hc-3 `ec013.40/ec013.719`
- 선형 트랙 왕복 122회: 양방향 각 61회
- 시간순 분할: train 72, validation 24, encoding-test 26
- CA1 pyramidal unit 43개
- manifest SHA-256: `f1fe20f504523df71af8eccf00c0d70d4614c3130daa3931074675e362dc55f3`
- result SHA-256: `4c70bd873e52f658464080573b7f08f919ea910086a588b2efc3d41f8166d80f`
- raw-recompute validation SHA-256: `faa39b2caac62c5be3dec203f07657ac7713e2c2d5306710ce9ab0b0a084edc8`

## 위치 encoding 게이트

| 항목 | 결과 | 사전 문턱 | 판정 |
|---|---:|---:|---|
| encoding-test 표본 | 2,272 | 100 이상 | 통과 |
| median absolute error | 0.265713 track | 0.15 이하 | 실패 |
| 정적 occupancy 기준 오차 | 0.416851 track | - | - |
| 정적 기준 대비 개선 | 36.2572% | 20% 이상 | 통과 |

신경활동은 정적인 평균 위치보다 실제 위치를 더 잘 구분했지만, 절대 위치 오차가 트랙 길이의 약 26.6%였다. 따라서 ripple 속 decoded path를 구체적인 기억 궤적으로 읽을 정확도 허가가 나지 않았다.

## ripple·trajectory 보조 결과

304개 ripple 후보 중 사전 활성도 조건을 만족한 사건은 41개였다. coverage 20개 문턱은 넘었다.

| 비교 | median 차이 | bootstrap 95% 하한 |
|---|---:|---:|
| order vs time shuffle | 0.005362 | -0.036037 |
| order vs cell shuffle | 0.007312 | -0.061311 |
| distance vs time shuffle | -0.016456 | -0.085141 |
| distance vs cell shuffle | -0.063578 | -0.135612 |

두 shuffle의 95 percentile을 동시에 넘은 사건은 2/41, 즉 4.878%였다. 5% 귀무율 단측 binomial `p=0.614464`로, 10% 및 `p<0.01` 게이트를 모두 실패했다. encoding 문턱을 무시하고 보조 점수만 보더라도 시간 순서와 세포-장소 대응을 보존한 궤적 증거는 대조보다 높지 않았다.

## 주장 범위와 다음 의무

**[산출]** 이 개발 세션에서 위치 관련 집단신호는 정적 기준보다 유용했지만, 사전 정확도와 replay 대조를 통과한 기억 궤적은 확립되지 않았다.

**[식별 불가]** 실패가 생물학적 replay 부재 때문인지, 단일 전극군 ripple 채널·43개 unit·단순 Poisson place-field decoder의 감도 부족 때문인지는 이 실행만으로 분리할 수 없다.

**[금지]** 같은 test endpoint를 보고 decoder·threshold를 조정한 결과를 확인 결과로 승격하지 않는다.

**[다음 최소 증명 의무]** endpoint-blind 새 해마 세션을 고정하고, R1에서 열지 않은 자료의 validation 구간만으로 decoder 교정법을 선택한 뒤 별도 test에서 encoding 문턱과 두 replay 대조를 다시 통과해야 한다. 그 전에는 Stage 8 인출·교정으로 연결하지 않는다.
