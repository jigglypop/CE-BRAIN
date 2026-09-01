# CE-NPF ALT-BIO D5 — Lee 2022 자료 접근·스키마 결과

Status: `D5_SOURCE_BYTES_ACCESS_BLOCKED / BIOLOGICAL_ENDPOINT_NOT_RUN`

판정일: 2026-09-01

## 1. 목적과 정지선

목적은 Lee et al. 2022의 동일 성체 뉴런 day 1--day 7 자료로
"세포형별 기능 편향과 동일세포 역할 지속이 있으면서 학습 중 표현도 변하는가"를
마우스 단위로 판별하는 것이었다. 출생·청소년기 고정, 연결가중치, 전도속도,
리만계량은 이 자료의 관측 대상이 아니다.

원자료 bytes와 내부 행 대응을 검증하지 못하면 endpoint를 계산하지 않는다는
정지선을 적용했다.

## 2. 공식 소스 고정

- 논문: <https://doi.org/10.7554/eLife.72549>
- Dryad: <https://doi.org/10.5061/dryad.q573n5tjj>
- 공개 판본: version 6, version ID `209607`, CC0-1.0
- `Data_For_Dryad.zip`: file ID `1963279`, 702,252,809 bytes,
  SHA-256
  `f91b64c89c3ec99e4d416c332e82627c6b4487974917d0c8c4df5c02cea6b203`
- `README.txt`: file ID `1963278`, 1,915 bytes, SHA-256
  `ded0d5124a5767fe7b1763a6fb9bcb81f97de905cd2d16d75b440a07252ff4f2`
- 공식 eLife 보충 ZIP은 별도로 획득했다.
  `data/external/lee_2022_dryad_q573n5tjj/elife-72549-supp-v1.zip`,
  3,371,020 bytes, SHA-256
  `aecb35419f2ba3bfb2eb6cf3e8fb62615c956de525340812f9f7c66ddecc95c5`.

## 3. 접근 결과

Dryad REST file-download endpoint는 bearer token 없이 `401 Unauthorized`를,
공개 web file-stream endpoint는 이 실행환경에 `403` AWS WAF 응답을 반환했다.
랜딩 페이지와 익명 metadata API는 정상 공개되어 파일명·크기·해시는 확인됐지만,
ZIP bytes는 획득하지 못했다. 이는 자료가 비공개라는 판정이 아니라 현재
비대화형 실행경로의 접근 차단이다.

따라서 다음을 열지 않았다.

- ZIP member manifest와 CRC
- `df`, `real_rois`, 행동시각 필드의 실제 shape
- day 1 ROI row index가 day 7 동일세포 행으로 보존되는지의 bytes-level 검사
- 마우스 단위 동일세포 endpoint

## 4. 스키마에서 발견한 별도 hard gate

보충표의 paired PN `Total ROIs` 합은 1,209인데 Figure 2/3/6/7 캡션은
1,029 cells로 적는다. PV 316, VIP 407, SOM 189는 보충표와 캡션이
일치한다. PN은 숫자 전도 가능성이 있어도 원자료 행수로 확인하기 전 어느 값도
교정하지 않는다.

저자 방법과 코드는 same-cell key를 명시적 UUID 대신

$$
(\text{cell type},\ \text{mouse ID},\ \text{day-1 ROI row index})
$$

로 구성한다. day 7 신규 ROI를 day 1 행수 뒤에서 잘라내고 열 인덱스를 유지하는
방식이므로, responsive cell만 먼저 압축하면 대응이 깨진다.

## 5. 생물학적으로 허용되는 범위

논문과 보충자료는 수술 P40--P60 뒤 성체 학습을 관찰한다. PV cue reliability와
VIP reward reliability 증가, PN의 새로운 reward response 감소, SOM의 cue/reward
response 출현은 성체에서 기능표현 갱신률이 0이 아님을 시사한다. day-1 responder로
조건화한 일부 PV/VIP 세포의 day-7 지속은 세포형 편향 또는 역할 anchor와 양립한다.

그러나 이는 출생·청소년기 고정 시점을 관찰하지 않았고, 사후 responder 선택과
세포 pooling이 포함된다. 독립 단위는 PN 6, PV 6, VIP 4, SOM 7마우스이지
수백 개 ROI가 아니다.

## 6. 판정

`D5_SOURCE_BYTES_ACCESS_BLOCKED`.

원래 강한 명제인 "뉴런 의미가 태어나며 청소년기에 고정된다"는 이 자료로
검증할 수 없다. 구성요소 문헌이 허용하는 재구성은

> 안정된 세포 정체성·세포형 prior + 문맥·학습 의존적 기능표현 + 일부
> 집단/동일세포 역할의 조건부 지속

이다. 이 문장은 원자료 재분석의 양성 판정이 아니라 논문이 허용하는 범위 제한이다.

## 7. 다음 허용 행동

대화형 공개 다운로드 또는 정식 Dryad API credential로 exact ZIP을 획득하고
크기·SHA-256·PN 행수·ROI 행 보존 gate를 통과한 뒤에만 사전고정 endpoint를
실행할 수 있다. credential은 저장소나 로그에 기록하지 않는다.

