# CE-BRAIN Stage 7 R2 선택장치 교정

Status: `PRE_ENDPOINT_METADATA_CORRECTION`

최초 R2 선택기는 SQLite의 `video_type is not null`을 위치 추적 존재 조건으로 사용했으나, 선택된 `ec016.234`의 값은 영상 없음 표기인 `"-"`였다. 신경·ripple·replay endpoint를 다운로드하거나 열기 전에 발견한 장치 의미 오류다.

최초 영수증은 삭제하거나 덮어쓰지 않는다. 그 영수증의 “video” 조건은 무효다. 다만 해당 조건을 완전히 제거한 나머지 규칙, 즉 R1 topdir 제외·linear 600초 이상·CA1 pyramidal 30개 이상·topdir별 unit 최대화·해당 topdir archive 최소화로 다시 계산해도 선택은 `ec016.17/ec016.234`로 동일하다.

따라서 공식 MD5 `3b350f3b76d7f0c903ee4afab89db9ec`로 archive를 검증한 뒤 내부에 처리된 `.whl` 위치파일이 있는지만 새 장치 게이트로 검사한다. `.whl`이 없거나 시간축이 LFP와 맞지 않으면 score 전 `STAGE7_R2_POSITION_APPARATUS_STOP`으로 닫는다. 있더라도 traversal·ripple·replay 점수는 별도 계약 전에는 열지 않는다.
