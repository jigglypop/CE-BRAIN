# CE-BRAIN Stage 9 DA R5 학습게이트 개발 결과

Status: `DEVELOPMENT_RESULT_RECOMPUTED`

## 판정

`DOPAMINE_UPDATE_SIGNAL_NOT_ESTABLISHED`

## 자료와 봉인

- DANDI `001632@draft` development dLight cohort 7 animals
- 60sD 3 animals, 600sD 4 animals
- day01~day08, daily rows 56, next-day transition rows 49
- 57 NWB assets, 339,916,595 bytes
- manifest SHA-256: `162215743b34ef68fe17d9b5eb8199c10f95605f6c26d8b23f95028ff79f162a`
- result SHA-256: `b11a29b94c206820f2b6623c509bd2e4fed52fedf39a4b97f9996c732c07ad91`
- raw-recompute validation SHA-256: `af947985d3f10e098c22634052cefff2131505b61cfa7a9dd856df92846cfd38`

## 결과

| 모델 | held-out animal RMSE |
|---|---:|
| P: 오늘 행동 persistence | 1.371303 |
| B: ITI + day + 오늘 행동 | 1.309323 |
| C: B + 오늘 cue dopamine | 1.478995 |
| S: B + 3일 shift dopamine | 1.359605 |

| 비교 | C의 상대 개선 | animal-bootstrap 95% 구간 |
|---|---:|---:|
| C vs B | -12.9588% | [-30.2279%, 2.0483%] |
| C vs P | -7.8533% | [-28.4421%, 10.8816%] |
| C vs S | -8.7813% | [-27.0385%, 8.1138%] |

cue-dopamine 표준화 계수는 leave-one-animal-out 7개 fold 모두 양수였다. 그러나 dopamine을 추가한 C는 세 기준선 모두보다 예측 오차가 컸고 bootstrap 하한도 양성 문턱을 통과하지 못했다.

## 해석

**[산출]** dopamine과 다음날 anticipatory licking 사이의 평균 방향성은 양수였지만, reward interval·day·current behavior를 넘어 새 동물에 일반화되는 추가 예측정보는 확립되지 않았다.

**[구분]** 이는 논문의 집단 평균 dopaminergic learning 결과를 반증하지 않는다. R5는 더 좁고 어려운 질문, 즉 개별 동물의 next-day 행동을 held-out animal에서 추가 예측하는지를 물었다.

**[현재 지위]** development gate 실패이므로 calibration 2 animals와 confirmation 4 animals은 열지 않는다. 관찰적 chemical gate도 승격되지 않았고, 인과 chemical gate는 더더욱 미확립이다.

**[다음 최소 증명 의무]** 같은 endpoint를 재조정하지 말고, trial-level hierarchical model 또는 명시적 intervention 자료를 새 development 계약에서 검정해야 한다. 평균 상관과 개체 외삽을 구분해야 한다.
