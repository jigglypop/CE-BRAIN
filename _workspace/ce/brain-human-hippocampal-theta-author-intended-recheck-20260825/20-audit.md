# 형식·상태 감사 — 교정 재검산 Stage Q 승인

Status: COMPLETE

Gate: PASS

Authorization: QC_RECHECK1_COMPLETE_ONLY

독립 수학·상태·거래 감사를 같은 stable snapshot에서 반복했고 Stage Q 범위의
P0/P1은 남지 않았다. TS/p17/post와 PB/p17/pre에 대한 endpoint-free,
version-pinned `QC_RECHECK1`은 정확히 한 번 완료되었다. receipt와 COMPLETE progress
journal은 receipt SHA-256 및 completed rows로 상호 결박되었다.

이 완료 상태는 `ENDPOINT1`, endpoint-bearing receipt, aggregate, 생물학적 해석 또는
재실행을 허용하지 않는다. 기존 HPC4 `ATTEMPT1`은 불변이며 재시도하지 않는다.
`ENDPOINT1`은 별도 endpoint-authority P0 감사 때문에 `BLOCKED` 상태이고, 실제
Stage Q receipt를 사후 감사한 뒤 새 실행 승인을 받아야 한다.

## 선행 상태 정규화

- HPC4의 18-object, 723,560,000-byte source integrity는 `PASS`로 보존한다.
- HPC4의 wrong time-grid clean count는 자체 거래 기록으로는 유효하지만
  author-intended measurement에는 `APPARATUS_INVALID`이다.
- HPC4의 `QC_STOP_MIN20`은 생물학적 양성·음성 결과가 아니며 endpoint도 없다.
- 기존 ATTEMPT1은 재실행하지 않고 새 run의 별도 `QC_RECHECK1`과 조건부
  `ENDPOINT1`만 사용한다.

## 경로 감사

R1은 관측된 11에 맞춰 threshold를 10으로 내리지 않는다. 출처가 반박한 시간축을
교정하고, 저자 코드에 없는 MIN20을 estimator 정의역과 분리한다. clinical cell의
$n_{clean}\ge1$은 평균의 분모를 보장하는 최소 조건이다. bipolar에 0-cell이 있으면
partial result를 골라 쓰지 않고 sensitivity bundle 전체를 생략하며 clinical primary는
보존한다. raw 결과의 방향에 따라 cohort, contact, window, threshold, estimator,
seed를 바꾸는 분기는 없다.

## 수학·출처 감사

교정 grid $t_j=j/499.5-0.5$와 latency 50..649, baseline 225..245, early
258..274, late 275..374, prestim 100..199는 저자 코드·BrainVision sampling
interval·FieldTrip 선택 의미와 일치한다. 999 samples에서 60/120/180 Hz가 exact
integer-cycle DFT basis라는 계산도 맞다. 두 Python 표현은 모든 selected trace의
DFT+LPF 직후 999 samples와 reason/keep mask를 독립 대조한다.

저자 archive는 p17/p19 PB 함수 인자와 FieldTrip 판본을 완전히 고정하지 않는다.
따라서 이 gate는 `author-intended emulation`만 승인하며 exact MATLAB/FieldTrip
replication 또는 published `fitlme` parity를 승인하지 않는다.

## Stable Stage Q 구현 감사

- executor SHA-256: `79191826af3a28b174cc793119817e1536e9466f9a162d1dcc05bea724b25c54`
- focused test SHA-256: `7c7d6a470c09b5e8386a8b2127892e4336038e651acafe96af8772c11b3a6d78`
- analysis lock SHA-256: `5cce4a71f03090793ed21d8316cbf8fc0b9b4403ae077e331963d7c1cda2e470`
- frozen source-loader SHA-256: `8e9358ea72217b4f0d48f96d174ec506f3b2faf4b55cb2d2ebcc3248a93fb85c`
- focused no-network validation: `15 passed`, expected constant-kurtosis warning 1건

감사는 exact two-target identity/order, corrected grid와 integer-cycle DFT, p17 direct/SOS
filter parity, reason/channel/union mask와 count, amplitude margin, source object identity,
zero-clean Q 보존, source/implementation STOP 분리, prior 거부, receipt-progress 상호 결박,
atomic writer의 pre/post-commit failure 및 orphan authority 처리를 포함한다.

Stage E는 감사 범위 밖이다. 현재 result validator는 저장된 trialwise P2P를 raw clean
trials에서 독립 재구성하지 못하고, bipolar sensitivity 삭제를 권위 있게 배제하지 못하는
endpoint-authority P0가 남아 있으므로 실행하지 않는다.

## 실제 QC_RECHECK1 사후 감사

- receipt SHA-256: `04edcbe5c290985f6a59c230989f4d13d83323e193767559ec4e15562de9e6e6`
- progress SHA-256: `da9d5d5f77d31632640faef11b3fb8cc7b44068c849c051d0db658938a06d679`
- source objects: 2개, 합계 `83,300,000` bytes; expected/observed SHA·size·version ID·ETag 전부 일치
- TS/p17/post: clinical `11→12`, bipolar `25→25`
- PB/p17/pre: clinical `22→24`, bipolar `11→11`
- reason 변화: clinical amplitude reject가 TS `48→47`, PB `38→36`; 나머지 reason과 bipolar는 동일
- dual-path 최대 차이: `6.071e-11 µV` 이하, 허용치 `1e-6 µV` 통과
- `raw_result.json` 및 endpoint progress: 없음

선행 HPC4의 `11/25`, `22/11`은 당시 거래 기록으로 보존하지만, 저자 의도 시간축에
대한 값으로는 `APPARATUS_INVALID`이다. 새 값은 교정된 Python emulation의 QC 관측이다.
이것은 두 실제 공개 인간 iEEG 객체에서 계산 오산이 count에 영향을 주었음을 확인하지만,
P2P·조건차·theta 효과·인과성·기억·의식·CE·AGI를 증명하지 않는다.

P2 한계는 available-clean cell이 작을 수 있다는 점과 Python emulation이 exact MATLAB
binary가 아니라는 점이다. 이는 count 전면 공개, sensitivity bundle과 claim ceiling로
통제하며 raw 결과를 보기 전에 이미 기록한다.
