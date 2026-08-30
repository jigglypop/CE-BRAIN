# CE-BRAIN Stage 9 DA R1 day01 장치 중단

Status: `SCORE_BEFORE_SCHEMA_STOP`

DANDI `001632@draft` 전체 1,222 asset을 inventory SHA-256 `ac3fa305a9c310ad281014d88f81170378ac44a9e6e26f99651de50fe2c56536`로 잠갔다. 네 핵심 조건의 development day01 자산을 공식 SHA-256으로 검증했다.

네 파일 모두 `acquisition/eventLog`와 task parameter를 포함해 reward·behavior event는 식별됐다. 그러나 실제 photometry/dopamine time series instance는 없고 `ndx-photometry` specification만 포함했다.

**[판정]** `STAGE9_DA_SCHEMA_STOP`. day01 하나에 행동과 dopamine이 함께 있어야 한다는 R1 장치 계약을 통과하지 못했다. dopamine 값이나 학습 효과 점수는 열지 않았으며 화학 gate의 과학 음성 결과가 아니다.

**[다음 장치 교정]** 같은 네 development subject의 day01~day08 전체에서 instance가 존재하는 날짜를 스키마 수준으로 찾는다. 행동-only conditioning day와 dopamine recording day가 분리돼 있다면 subject/day linkage를 명시하는 새 분석 계약이 필요하다.
