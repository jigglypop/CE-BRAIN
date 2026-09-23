# BA-OBS-DISC2 pre-D0 독립 상태 감사

Status: COMPLETE

## 판정

`PASS_TO_OPEN_D0_AFTER_RECEIPT_SEAL`.

독립 read-only 감사자는 frozen run-lock
`2ea67d6728e1b1573d5efa15adef2e9f14ad0127bed458f43b265a3d376d9e6d`를 검사했다.
첫 응답의 형식 판정은 `STOP`이었지만, 원인은 과학·수학·구현 결함이 아니라 runner가 이
감사 결과를 담을 `preimplementation-audit-receipt.json`을 의도적으로 요구하는데 아직 그
파일을 쓰기 전이었기 때문이다. 감사자는 코드·수학·분할·fixture에 P0나 substantive P1이
없다고 명시했다. 이 문서와 receipt는 잠긴 입력을 바꾸지 않고 그 독립 결과만 봉인한다.

## 감사 범위와 확인 결과

| 항목 | 독립 판정 |
|---|---|
| run-lock | 지정 SHA와 일치; lock의 19개 파일 SHA 전부 일치 |
| endpoint blindness | `d0-opened.json` 없음; source/split manifest 모두 `scientific_endpoint_opened=false` |
| raw range | zero-based anchor, run별 512/2048 Hz, `anchor-f_s`부터 `anchor+floor(0.120f_s)`, multiplexed little-endian float32, exact HTTP 206/Content-Range/ETag/VersionId 검증 |
| 전기 endpoint | trial/contact baseline subtraction, bipolar difference, pooled-baseline `1.4826 MAD`, 10-trial mean, five-bin dimensionless RMS, `log(E+10^{-6})`, matched prestimulus 구현 일치 |
| 표본·가중 | source당 4 anchor/12 query; source equal 후 participant equal |
| 식별성 | 자유 source offset과 겹치는 global intercept/current coefficient 제거; profiled query Jacobian gate 연결 |
| 단계 | D0 six-fold patient-blocked 선택, D1/D2/D3 predecessor barrier, participant bootstrap, geometry permutation 연결 |
| controls | single orientation은 temporal repeatability만; two orientation만 polarity control; D3 prestimulus/contact-mean control 연결 |
| fixture | v1 `4/64` 실패와 unseen-v2 `0/64` 성공을 별도 receipt로 보존; runner는 v2만 사용 |
| focused validation | metadata 6 + split 5 + endpoint/runner 14 + dimensionless 19 = `44/44 PASS` |

## 지위

- `[검증 산출]` D0 raw range를 열기 위한 apparatus/implementation barrier는 substantive audit를
  통과했다.
- `[미완성]` 실제 CCEP 결과는 아직 하나도 열지 않았으므로 후보식의 경험적 지위는 미정이다.
- `[주장 상한]` 성공하더라도 held-out human SPES CCEP observed-kernel prediction까지만 말할
  수 있다. 생물학적 Riemannian metric, geodesic, 무한차원, 의식·자아·해마·AGI 검증으로
  승격하지 않는다.

## P2 기록

초기 실패 산출물 `artifacts/pre-d0-fixture-receipt.json`은 stale 원본이다. 같은 byte를
`artifacts/pre-d0-fixture-receipt-v1-failed.json`으로 명시적으로 보존했고, runner와 run-lock의
활성 fixture는 `artifacts/pre-d0-fixture-receipt-v2.json`이다. stale 파일은 성공 증거로
사용하지 않는다.
