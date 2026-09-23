# BA-OBS-DISC2 implementation result

Status: COMPLETE

## 결과

`STOP_IMPLEMENTATION_PRE_RANGE`.

D0 open marker는 2026-08-24T16:32:20.023673Z에 생성됐고, 25.7 ms 뒤
`sealed event/sample crosswalk mismatch`로 fail-closed했다. `d0-opened.json` SHA-256은
`ff4ac42a44d34c3a4438250392d042133f84dcb8ee341537a05dfcdf8a85661e`,
`d0-failure.json` SHA-256은
`15e711b64cb0fe2b73aa3b1c1c8235ab80961b63e40f97fdf8969d3f686d0c1a`다.

## 원인

metadata audit의 `event_sample_crosswalk`는 event별 lookup이 아니다. audit code는 각 electrical
event에서

$$
\delta_e=\texttt{sample\_start}_e-operatorname{round}(f_s\,\texttt{onset}_e)
$$

를 검사한 뒤 `Counter(str(delta))`만 저장한다. 따라서 record의 `{"0":160}`은 event 0의
sample이 160이라는 뜻이 아니라 160개 electrical event 모두 $delta_e=0$이라는 뜻이다.
runner가 이 집계를 `event_index -> anchor_sample` 사전으로 오독했다.

## endpoint 노출 여부

`_ordered_trials()`는 `process_source()`에서 `fetch_trial()`과 thread pool 생성보다 먼저
호출된다. 실패는 첫 D0 source의 `_ordered_trials()`에서 발생했다. 따라서 HTTP range request,
raw payload decode, voltage endpoint 계산은 시작되지 않았다. `d0-range-receipt.json`,
`d0-endpoints.json`, `d0-endpoint-receipt.json`, `d0-result.json`은 모두 없다.

이 run의 exclusive marker는 삭제하거나 되돌리지 않는다. 같은 run을 재실행하지 않는다.

## 재개 조건

새 implementation-retry run에서만 다음을 허용한다.

1. 집계 crosswalk는 정확히 `{"0": electrical_event_count}`인지 확인한다.
2. 선택된 각 `(event_index, anchor_sample_zero_based, orientation_site)`를 해당 source record의
   정확한 `source_blocks.clean_trials` 행과 대조한다.
3. corrected linkage를 74명 전체의 선택 source에서 endpoint-blind test한다.
4. 새 run-lock과 독립 pre-D0 감사를 통과한 뒤에만 raw range를 연다.

과학식, split, endpoint, threshold는 이 실패를 보고 바꾸지 않는다.
