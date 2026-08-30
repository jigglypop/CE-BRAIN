# CE-BRAIN Stage 7 R2 위치 장치 중단

Status: `SCORE_BEFORE_APPARATUS_STOP`

선택된 독립 topdir 세션 `ec016.17/ec016.234`의 공식 archive MD5 `3b350f3b76d7f0c903ee4afab89db9ec`를 검증했다. 압축 내부에는 `.whl`, `.eeg`, `.xml`, `.clu`, `.res`가 있었고 LFP와 위치의 duration은 각각 1,045.4000초와 1,045.4016초로 일치했다.

그러나 `.whl` 40,836행 중 두 LED 좌표가 모두 유효한 비율은 `0.8626457048`이었다. R1 장치에서 사용한 원시 위치 유효률 90% 문턱을 통과하지 못했다.

**[판정]** `STAGE7_R2_POSITION_APPARATUS_STOP`.

이 중단 전에 ripple·replay 점수는 열지 않았다. 86.26%를 본 뒤 문턱을 낮추거나 보간 후 유효률로 기준을 바꾸지 않는다. 이는 기억궤적 가설의 음성 결과가 아니다.

동일한 endpoint-blind 메타데이터 순위에서 `ec016.17`에 남은 세션은 archive가 더 큰 `ec016.233` 하나다. 새 R2B 장치 계약에서 동일한 원시 위치 90% 문턱을 유지할 때만 fallback으로 검사한다.
