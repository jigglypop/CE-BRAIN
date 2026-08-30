# CE-BRAIN Stage 9 DA-R6 도파민 개입 뒤 행동 지속성 계약

> 상태: **사전등록 / 결과 미개봉**  
> 자료: DANDI `000559`, Zenodo `10.5281/zenodo.7274803`의
> `optoda_raw_data/learning_timecourse_processed_summary.parquet`  
> 원본 SHA-256: `3b139a1f46c750181616930d753dd1d804e01a75686e5c0cb34904932e401344`

## 1. 쉬운 말로 말한 목표

- **최종 목표:** 같은 전기 궤적의 쓰기 여부를 화학 상태가 가르는지 확인한다.
- **이번 하위 목표:** 도파민 축삭을 폐루프 광자극한 뒤, 자극이 없는 다음 세션에도 표적 행동 사용 증가가 남는지 확인한다.
- **필요한 이유:** 지속 효과조차 없으면 도파민이 미래 행동 레퍼토리를 쓴다는 더 강한 가설로 올라갈 수 없다.

이번 자료에는 동시 전기생리 측정이 없다. 따라서 통과해도 말할 수 있는 최대치는
`도파민계 개입이 이후 행동 선택을 지속적으로 바꿀 수 있다`이다. `같은 전기 궤적에서
화학만 달라 쓰기가 갈린다`는 직접 게이트나 내인성 도파민 농도의 측정으로 승격하지 않는다.

## 2. 목표 정렬과 이탈 검사

| 질문 | 사전 판정 |
|---|---|
| 목표가 명확한가 | 예. 무자극 post 세션의 표적 행동 지속 변화다. |
| 현재 분석이 목표를 직접 판별하는가 | 부분적으로 예. 화학계 인과개입과 지속 행동은 보지만 전기 궤적은 보지 못한다. |
| 다른 계보를 같은 Stage로 잘못 세는가 | 아니오. 이 결과는 `chemical intervention sufficiency` 하위증거로만 기록한다. |
| 선행 게이트를 건너뛰는가 | 아니오. 직접 chemistry×electrical write gate와 Stage 10 통합은 계속 잠근다. |

## 3. 표본과 오염 방지

1. `experiment_type == reinforcement`, `rle == false`, `stim_duration == 0.25`만 쓴다.
2. 처치는 `area == "snc (axon)" and opsin == "chr2"`, 대조는
   `area == "ctrl" and opsin == "ctrl"`이다.
3. cohort와 처치가 완전히 뒤엉킨 배치를 제외한다. 두 군이 함께 있는 cohort `0, 3, 5`만 쓴다.
4. 이때 독립 단위는 세션이나 표적 음절이 아니라 동물이다. 장치 감사에서 고정된 수는
   처치 8마리, 대조 6마리다.
5. `syllable == target_syllable`인 행만 쓰고 각 UUID의 마지막 30초 bin
   (`bin_start == 1770`, `bin_end == 1800`)을 사용한다.
6. 한 동물에 여러 UUID/표적 음절이 있으면 먼저 동물 안에서 평균하여 의사반복을 막는다.

## 4. 고정 endpoint

- UUID 값: 공식 처리표의 `change_usage`.
- session 값: 같은 동물·`session_number`에 속한 UUID 값의 산술평균.
- primary: 무자극 post `session_number in {3, 4}`의 동물별 평균.
- persistence secondary: 더 늦은 `session_number == 4`의 동물별 평균.
- 효과량: cohort 고정효과를 넣은 `chr2 - ctrl` 계수. 구현은 cohort 안에서 처치와 endpoint를
  각각 중심화한 뒤의 최소제곱 계수와 정확히 같다.

## 5. 고정 추론과 통과문턱

처치 라벨은 cohort 안에서 원래 처치 수를 보존해 가능한 모든 배치를 열거한다. cohort별
조합은 `15 × 3 × 10 = 450`개이며, 한쪽 꼬리 정확 p값은 `beta_perm >= beta_observed`인
배치 비율이다.

`DA_CAUSAL_PERSISTENCE_ESTABLISHED_DEVELOPMENT`는 다음을 모두 만족할 때만 낸다.

1. primary 계수 `> 0`이고 정확 `p <= 0.01`.
2. 동물을 한 마리씩 제외한 모든 primary 계수가 `> 0`.
3. session 4 계수 `> 0`이고 정확 `p <= 0.05`.
4. 필요한 cohort·군·session 셀이 모두 존재하고 값이 유한하다.

하나라도 실패하면 `DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED`다. 유의하지 않은 결과를
`도파민 효과가 없다`로 읽지 않으며, 통과 결과도 직접 화학-전기 쓰기 게이트로 읽지 않는다.

## 6. 실행 후 기록할 것

- 원래 질문에 답했는가: 지속 행동 하위질문에만 답한다.
- 무엇이 반증 또는 미확립되었는가: 위 고정 endpoint family만 판정한다.
- 무엇이 살아 있는가: 다른 시간창·내인성 농도·동시 전기생리·다른 신경조절물질.
- 다음 허용 행동: 통과 여부와 무관하게 직접 chemistry×electrical 자료 없이는 Stage 10으로
  자동 상승하지 않는다.
