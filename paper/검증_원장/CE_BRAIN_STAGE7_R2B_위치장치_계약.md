# CE-BRAIN Stage 7 R2B 위치 장치 계약

Status: `PRE_ENDPOINT_FALLBACK_LOCK`

R2 `ec016.234`가 원시 위치 유효률 90% 문턱에서 score 전 중단됐으므로, 같은 독립 topdir `ec016.17`에서 메타데이터 순위상 남은 유일한 선형 세션 `ec016.233`을 fallback으로 고정한다.

- duration: 1,928.1초
- CA1 pyramidal unit: 84개
- archive bytes: 1,052,938,781
- 공식 MD5: `9986ef9400e9862fb1142742455f95df`

공식 MD5 검증 뒤 `.whl`, `.eeg`, `.xml`, CA1 `.clu/.res`만 선별 추출한다. 다음을 모두 만족해야 분석 계약으로 이동한다.

1. spike 20kHz, LFP 1,250Hz.
2. LFP duration과 metadata duration 차이 0.1초 미만.
3. 위치 duration과 LFP duration 차이 0.1초 미만.
4. 두 LED 원시 좌표의 전체 유효률 90% 이상.
5. CA1 pyramidal metadata unit 84개의 cluster가 실제 파일에 존재.

하나라도 실패하면 `STAGE7_R2B_APPARATUS_STOP`이다. 이 검사에서는 ripple, place decoding, replay endpoint를 열지 않는다.
