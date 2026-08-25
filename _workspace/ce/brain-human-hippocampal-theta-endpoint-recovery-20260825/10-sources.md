# 복구 입력 증거

Status: COMPLETE

이 run은 새 외부 출처나 네트워크 입력을 사용하지 않는다. source evidence는 선행
`ENDPOINT_FULL1`의 동결 artifact와 그 선행 source lock을 상속한다.

## 실제 raw 실행 사실

- 18개 completed source rows가 모두 존재한다.
- 각 row의 expected/observed SHA-256, size, version ID, ETag가 exact 일치한다.
- expected 및 observed byte 합계는 모두 `723560000`이다.
- result status는 `RAW_COMPLETE`, records/files는 각각 18개다.
- semantic status는 `PUBLISHED_MODEL_ENGINE_UNAVAILABLE`,
  `SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION`,
  `CLINICAL_AVAILABLE_CLEAN_PRIMARY`, `BIPOLAR_SENSITIVITY_AVAILABLE`이다.
- predecessor anchors는 TS/p17/post clinical/bipolar `12/25`, PB/p17/pre `24/11`로
  이전 receipt와 exact 일치했다.

## 실패 경계

선행 progress SHA는
`2a1f1e3a4730c04b3d79426d592c4b3c071fe4088c2953b2afa87dfefe11ae90`이고 상태는
`IMPLEMENTATION_STOP`, attempt는 `ENDPOINT_FULL1`, completed rows는 18, error는 exact
`ModuleNotFoundError: No module named 'examples'`이다. progress rows는 result records와
exact 일치한다. 실패는 모든 source와 result를 쓴 뒤 producer의 package import에서
발생했다. 이 문서는 그 실패를 숨기거나 원 progress를 승격하지 않는다.

## 저장된 계산 입력

`source_witness.npz` SHA
`2a5a9328cab95f6a484a76af5c7e34deccbace52a9eb5a00241ee08f0d2e58ae`는
13,053,329 bytes이며 rejected trial을 포함한 18개 clinical selected-QC tensor와
local-bipolar tensor, 총 36 arrays를 담는다. `raw_result.json` SHA
`cd3aaff53b1db1dba97f92812f529f066c870ac968bdd7a27f0b9ad4c0a8585d`는 모든
trialwise/mean-waveform P2P와 aggregate를 담는다. clinical zero와 bipolar zero cell은
각각 0개다.

실패 직후 read-only synthetic IN_PROGRESS view를 사용한 frozen validator content check는
`CONTENT_PASS`였다. 이는 복구 가능성의 사전 증거이지 최종 COMPLETE authority는 아니다.

## 출처 상한

OpenNeuro `ds006065` v1.0.0, commit
`14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`와 기존 source lock을 상속한다.
Kragel et al. 2025, DOI `10.1038/s41467-025-59417-7`, Zenodo `14735080`의 공개자료다.
새 표본이나 독립 decoder evidence는 추가되지 않았다.

