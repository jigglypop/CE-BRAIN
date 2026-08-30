# CE-BRAIN Stage 6 Allen 개발자료 장치 감사

Status: `DEVELOPMENT_SCHEMA_PASS_R1_EXECUTED`

## 결과

DANDI `000021@0.251116.2246`의 공개 API 목록을 endpoint-blind로 고정했다. 총 214개 자산, 32개 subject, 32개 session NWB, 182개 probe NWB, 477,562,344,354 bytes다. 정렬한 자산 ID·경로·크기의 inventory SHA-256은 `3ede022c7396ebd36b37b2f490e1cd9abbfa6c92682186d8098284ef830a9bd4`다.

사전 고정 salt에 따른 subject 분할은 development 19, calibration 9, confirmation 4다. confirmation neural endpoint는 열지 않았다. DANDI `001695`도 열지 않았다. 영수증 파일 SHA-256은 `db9e3b1e94487c94014dcfe8282fb91889734f6f8b05e3b9ed6377329483a54a`다.

## 장치 한계

가장 작은 development session은 subject `707296975`, session `721123822`, asset `224b57e5-c9a3-46ef-85db-966713f3ccbe`, 1,736,516,600 bytes다. 공식 SHA-256은 `4e284295a1be5c6cca49df84fab52ad38b4749d2361b2edebeb676051cf09921`이다.

전체 다운로드의 관측 속도가 약 0.4 MB/s로 약 1시간이 예상되어 이번 FAST 장치 감사에서는 중단했다. 생성된 25,292,800-byte 불완전 파일은 절대경로와 크기를 확인한 뒤 삭제했다. 원격 HDF5 range-read도 30초 안에 root schema를 반환하지 않아 정체된 reader process를 종료했다. 이는 과학적 실패가 아니라 전송·장치 상태다.

## 현재 허가

- metadata 분할과 개발 세션 선택: 허가.
- development session의 unit·stimulus·behavior schema 감사: 아직 필요.
- calibration/confirmation 점수화: 미허가.
- `r_dyn`, `r_pred` 또는 순환차원 주장: 미허가.

다음 실행은 resumable 또는 병렬 range 다운로드 장치를 마련한 뒤 위 development session의 공식 SHA-256을 맞추는 것이다. 이후 strict-past 예측 분할이 가능한지 schema만 먼저 검사한다.

## 후속 장치 복구

12-worker range downloader를 구현해 같은 development session을 재개 가능한 32MiB 조각으로 받았고 공식 SHA-256을 일치시켰다. schema 감사에서 unit 1,603개, 시각영역 unit 774개, 자연영화 900프레임 완전 반복 20회, 두 stimulus block, running 신호를 확인했다. 판정은 `STAGE6_DEVELOPMENT_SCHEMA_ELIGIBLE`이다.

품질 필터 뒤 214개 시각 unit을 사용한 R1 개발 실행과 원자료 재계산까지 완료했다. 과학 판정은 `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`이며 상세 수치는 `CE_BRAIN_STAGE6_R1_순환예측_결과.md`가 정본이다.

