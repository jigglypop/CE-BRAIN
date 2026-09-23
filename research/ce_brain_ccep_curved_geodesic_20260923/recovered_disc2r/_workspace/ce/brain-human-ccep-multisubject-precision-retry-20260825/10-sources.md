# BA-OBS-DISC2R source lane

Status: COMPLETE

새 데이터나 출처를 추가하지 않는다. predecessor의 OpenNeuro `ds004080` v1.2.4 source
manifest SHA `9ed8cb9d…11b3c3`와 split SHA `d4b03a98…96f7`을 byte 그대로 재사용한다.

핵심 수정은 출처가 아니라 schema 독해다. `event_sample_crosswalk`는 event lookup이 아니라
`sample_start-round(onset*fs)`의 record-level histogram이다. event별 anchor의 정본은 같은
source manifest 안 `participants[].sources[].clean_trials[]`이다. 새 runner는 split trial을 이
행과 직접 대조한다.

predecessor에서 raw HTTP request와 endpoint가 시작되지 않았다는 근거는 계약 §4와
predecessor `30-implementation.md`에 고정했다.
