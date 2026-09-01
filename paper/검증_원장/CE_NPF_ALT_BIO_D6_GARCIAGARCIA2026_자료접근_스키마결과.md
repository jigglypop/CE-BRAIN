# CE-NPF ALT-BIO D6 — Garcia-Garcia 2026 자료 접근·스키마 결과

Status: `D6_SOURCE_BYTES_ACCESS_BLOCKED / BIOLOGICAL_ENDPOINT_NOT_RUN`

판정일: 2026-09-01

## 1. 목적

동일 L5PT·GrC 세포의 서로 다른 과제와 같은 과제의 종단 자료를 이용해
문맥 의존적 표현 재배치와 보통 일간 drift를 동물 단위로 구분하려 했다.
이는 재구성된 의미 가설과 활동기하를 판별하는 자료이지, 연결가중치나 전도속도의
원인을 직접 관측하는 자료는 아니다.

## 2. 공식 소스와 파일 판본

- Nature 논문: <https://doi.org/10.1038/s41586-026-10946-1>
- Dryad: <https://doi.org/10.5061/dryad.9p8cz8x0p>
- dataset ID `188995`, 최신 metadata-only version ID `456498`, version 4,
  CC0-1.0
- 실제 file-bearing version ID `453627`
- 코드 concept DOI: <https://doi.org/10.5281/zenodo.21341571>

주 분석 후보 `data4.mat`은 file ID `4871001`, 3,760,433,834 bytes,
SHA-256
`bc46a6173a379b7c16909d166ec02e046b555070bb6df632d90d692b1e39646f`이다.
Dryad 전체 판본은 6파일, 10,661,937,620 bytes다.

## 3. 접근 결과

- 익명 Dryad metadata API: 통과
- `/api/v2/files/4871001/download`: `401 Unauthorized`
- `/stash/downloads/file_stream/4871001`: 현재 경로로 `301`
- `/downloads/file_stream/4871001`: 기본 요청은 `403`; browser header 요청은
  ZIP이 아니라 Anubis/AWS WAF HTML challenge
- 1-byte Range도 실제 S3 object로 전달되지 않음

그러므로 실제 `data4.mat` bytes·Content-Length·ETag·HDF5 signature를
검증하지 못했고 endpoint를 열지 않았다.

## 4. 공식 문서로 확인된 예상 스키마

- `crossTask`: 27 paired-session structures
  - trained `mid|expert` 18쌍
  - novice 9쌍
- `sameTask`: trained VR--VR 또는 Reach--Reach 9쌍
- pair 식별: `mouse`, `learningstage`, `dates[2]`, `task[2]`, `ntrials[2]`
- registered cell table의 `cellnums: Ncell x 2`
- trial neural data: `Ntrial x Ncell x 151`
- behavior: `Ntrial x 5001`
- continuous fluorescence: `Ncell x Nt_raw`

27 pair를 27마우스로 세면 안 되며, unique mouse와 mouse별 novice/trained·control
보유 여부를 실제 bytes에서 먼저 집계해야 한다.

## 5. 판정과 해석 경계

`D6_SOURCE_BYTES_ACCESS_BLOCKED`.

Nature 논문은 L5PT trajectory의 과제 간 일반화와 GrC trajectory의 coherent
reorientation을 보고한다. 이는 동일세포 집단의 관계적 표현이 문맥에 따라
재배치될 수 있다는 재구성과 양립한다. 그러나 이번 계보에는 독립 endpoint
영수증이 없으므로 논문의 결과를 CE raw-data 양성 판정으로 승격하지 않는다.

양성 결과가 있더라도 활동기하만 관측하며
$\Delta W$, $\Delta v$, $\Delta\tau$, $\Delta g$의 미시 인과사슬을 식별하지 못한다.

## 6. 다음 허용 행동

대화형 공개 challenge를 정상 통과하거나 정식 Dryad API credential로 bytes를
획득해 exact size·SHA-256·mouse independence·cell registration gate를 통과한
뒤에만 endpoint 계약을 고정한다. 우회 credential, challenge bypass 또는
미검증 mirror는 사용하지 않는다.

