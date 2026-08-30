# CE-BRAIN Stage 3B R2 표본율 수정 계약

Status: `SEALED_PRE_CONFIRMATION`

봉인 전 WT-only receipt는 적격 자극 3,106개, non-holdout 학습 150,870행, source-holdout 59,483행, 107개체, 양성 간선 42,176개를 기록했다. `unc-31` 값은 열지 않았다.

- inventory SHA-256: `b6b829ff409f31a27bb2006abc3701326599f7797efc22c0fde35edd1ebe8b86`
- schema receipt SHA-256: `d4583e9ae0bfb258a27c32832dde932cece61a68460f414debaf14c2c8162c24`
- WT development receipt SHA-256: `064def2bffd49a7aa6e8309e94978a3ed29cc3fda9bb3156d2645a0a9b3dc1c3`
- 봉인 직전 집중검사: 7개 통과

R1 WT development 점검은 과학 판정 전 0행으로 장치 중단됐다. 원인은 OSF 시간축이 0.5초 간격인데 baseline 24 frame을 요구해, 실제 `[-10,-2]`초 구간의 17 frame을 전부 탈락시킨 것이다. R1의 0행 영수증은 보존한다.

R2는 시간 구간을 유지하면서 finite 최소량만 baseline 12 frame, response 12 frame으로 고친다. stimulus 뒤 response index는 2 Hz에 맞춰 `+3`부터 `+21` 전까지, 다음 stimulus 5초 전에서 자른다. `|z|≥3` 4 frame 연속은 2초 지속을 뜻한다. 나머지 endpoint, 좌표, 후보 모델, 분할, bootstrap, 승리 규칙과 coverage 문은 R1을 그대로 계승한다.

R2는 별도 artifact 디렉터리에서 inventory·schema·WT development receipt를 다시 만들며, `unc-31` 신호값은 새 manifest 봉인 전 열지 않는다.
