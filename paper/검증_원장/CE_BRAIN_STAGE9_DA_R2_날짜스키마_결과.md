# CE-BRAIN Stage 9 DA R2 날짜 스키마 결과

Status: `SCORE_BEFORE_SCHEMA_STOP`

plain `30s`, `60s`, `300s`, `600s` development subject 네 마리의 day01~day08, 총 32개 NWB를 공식 SHA-256으로 검증했다. 모든 조건에서 행동 event session은 8개였지만 `specifications` 밖의 실제 photometry/dopamine instance는 0개였다.

**[판정]** `STAGE9_DA_LONGITUDINAL_SCHEMA_STOP`.

이는 chemical data 부재가 아니라 cohort 선택 오류다. 논문은 dopamine을 60초·600초 ITI의 subset에서 dLight1.3b로 측정했다고 기술하며, inventory에는 별도 `60sD`, `600sD` subject가 있다. chemical 값이나 학습효과 점수는 열지 않았다.

다음 계약은 `D` cohort만 사용하고 plain cohort를 chemical 분석에서 제외한다.
