# BA-SELF1-L3 최종 보고 — 교차 피험자 절대 QC 전이 실패

Status: COMPLETE

## 판정

이번 실행의 최종 판정은 `APPARATUS_INVALID_CROSS_SUBJECT_ABSOLUTE_QC`이다. 이는 제안한 경로 식이 틀렸다는 판정이 아니라, 피험자 1의 기록에서 고정한 **절대 진폭 QC 척도**가 피험자 2 기록으로 전이되지 않았다는 측정장치 판정이다. 따라서 미래 EEG 예측의 경로 이득, 자아, 의식, 무한차원 상태공간, 해마 해시, 뇌 기전에 관한 과학적 결과는 하나도 계산되지 않았고, 이 실행에서 활성화된 주장은 없다.

검사하려던 경험적 질문은 존재론적 문장이 아니었다. 현재 관측 상태와 미분, 시작점, 길이·에너지, 증분의 모멘트와 범위, 단어와 조건을 이미 맞춘 뒤에도, **순서가 있는 과거 경로**가 100 ms 뒤의 관측 EEG 변화를 더 잘 예측하는가를 묻는 것이었다. 경로의 순서를 담는 추가항은 2차 반대칭 area였으며, 단순 경로 길이는 그 순서를 버리는 대조량이었다. 그러나 유한한 관측에서는 과거를 확장 상태에 포함할 수 있으므로, 이런 예측 검사가 ‘자아는 상태인가 경로인가’라는 존재론을 식별할 수는 없다. 여기서 \(d=2,3,4\)는 의식의 차원이 아니라, 학습 접힘 안에서 보존한 **관측 quotient의 rank**다.

## 실행 경과

A0은 공개 BrainVision 헤더·이벤트·바이트 범위 가능성만 확인했다. 공개 sidecar의 66채널 표기와 실제 64열 header/binary 사이의 불일치는 결함으로 기록했고, 실행 스키마는 header의 64열과 그중 ECG 한 열을 제외한 63 scalp 열로 한정했다. 신호값은 이 단계에서 열지 않았다.

A1에서는 `sub-01/ses-02`의 8 trial, A2에서는 추가 24 trial의 task/rest 창을 읽었다. 각 창은 3,001 raw sample, 768,256 byte의 단일 HTTP range 응답이었고, 64개 A2 창 모두 `206`, `Content-Range`, 길이, ETag가 A0 기록과 일치했다. ECG 제거, common-average reference, 인과 45 Hz FIR와 decimation 뒤 nonfinite 값과 zero-MAD scalp 채널은 모두 0이었다. 이 통과는 신호 효과가 아니라 byte geometry와 파서·인과 전처리의 apparatus 통과다.

A2는 이 64개 창으로 최대 절대 common-reference amplitude의 cutoff를 `281.5218166091819`, 최대 1-step difference의 cutoff를 `95.39727548778933`으로 고정했다. A2 안에서는 32쌍 중 5쌍이 미리 정한 쌍 단위 amplitude 규칙으로 제외됐지만, 그 사실은 cutoff를 다시 고를 근거가 아니다. A1 receipt는 `a1-range-receipt.json` (SHA-256 `ac6511152a10cb9682a324513e969eb4e701063aa996e6ca7c33fcefd21bd93f`), A2 receipt는 `a2-range-receipt.json` (SHA-256 `8f37e315b2a2fb808c24c60ab10f5bd3c177ad31c3e00498634c6894bc1ac8d5`)에 남아 있다.

D1에서 피험자 2의 사전 배정 32쌍을 같은 고정 QC에 통과시켰을 때, 0쌍이 남았다. 64개 창 모두 정확한 `206` range 응답, 768,256 byte, finite 값 및 zero-MAD 검사에는 통과했다. 그러나 amplitude는 `306.695415322896`부터 `2884.06387213643`까지로 cutoff를 모두 넘었고, first difference는 `17.4290236704772`부터 `74.1123038511761`까지여서 cutoff `95.39727548778933`을 넘은 창이 없었다. 따라서 국소적인 step noise의 폭발이 아니라, 절대 amplitude 척도가 피험자 간에 유지되지 않는다는 제한된 진단이 가능하다. 이 수치만으로 원인(전극 임피던스, gain, 잔여 artifact 등)을 특정할 수는 없다.

## 멈춘 지점과 재현성

D1은 QC를 통과한 쌍이 없어서 모델 fitting 직전에 fail-closed로 멈췄다. `d=2/3`의 futility 통계, `d=4` 진단, future-target loss, \(M_0\) 대 \(M_1\) 비교, 모델 선택은 계산되지 않았다. D2와 C1/C2/C3, 그리고 fMRI는 열리지 않았다. 최종 D1 receipt `artifacts/d1-receipt.json`의 SHA-256은 `d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2`이며 `scientific_endpoint_opened=false`, `model_outcome_computed=false`를 명시한다.

첫 D1 실행은 outcome 전에 멈췄지만 예외 경로가 receipt를 쓰지 않는 구현 결함이 있었다. 첫 보수는 최소 fail-closed receipt만 남겼고, 그 원본은 `revisions/d1-receipt-minimal-v1.json`에 SHA-256 `b9ba7c105f691056c0983749b9b8e0d954bf7c94e0144f948c69957902096d71`으로 보존했다. 그 다음 보수는 cutoff, 신호 변환, split, feature, 모델 또는 outcome 규칙을 바꾸지 않고 이미 계산된 모든 range/QC 진단을 최종 receipt에 보존한 것뿐이다. 경계와 변경 내용은 `revisions/d1-execution-receipt-repair-v1.md`(SHA-256 `e6840a99d6afc443bd5a9e145f59f89ece6ec534e0008c4210f77a7c58eea049`)에 기록했다.

구현 검증은 focused test로 수행했다. range 파서·offset·인과 필터·anchor 정렬·zero-MAD fail-closed 검사는 `5 passed in 0.77s`, D1 feature·fold-local transform·ridge intercept·pair fold·실패 receipt 보존 검사는 `6 passed in 0.93s`였다. 이는 코드의 선언된 동작 검증이며 뇌의 경로 효과 검증은 아니다.

## 주장 지위와 다음 경계

관측 quotient 위의 양의 정부호 metric 및 순서를 뒤집을 때 area의 부호가 뒤집힌다는 명제는 수학적 구성으로 남는다. 그 area가 held-out EEG 예측을 개선한다는 명제는 **미검증 경험 후보**로 남는다. 관측 EEG가 완전한 신경 상태, 자기, 의식, 연속 또는 무한 차원을 정한다는 명제는 **미완성·비식별** 상태이며, 이 실행은 그것들을 지지하거나 반박하지 않는다.

후속 판본은 새 source lock에서만 시작한다. nonfinite와 zero-scale은 계속 hard stop으로 유지하되, amplitude와 first-difference QC는 물리 단위의 절대값 대신 창 또는 기록 내부 robust scale로 정규화한 무차원·scale-free 규칙을 사전 고정해야 한다. 그 새 QC의 피험자 간 apparatus 전이를 endpoint/model 실행 전에 별도로 검증하고, `sub-03` confirmation은 계속 봉인한다. D1에서 보인 0/32는 바로 이 측정 규칙의 실패를 기록한 것이며, 경로 식을 고쳐 맞출 근거는 아니다.

## 고정 근거

본 보고는 frozen ledger (`_workspace/ce/brain-algorithm-route-ledger.md`, BA-SELF1 closure SHA-256 `dbfd96064d7e6b5a4f2e05bf61388f299e978e7ae9535702599f3959ce8de9c9`)와 contract, source, math, route, audit, implementation, validation 및 receipts를 읽기 전용으로 종합했다. 본 실행의 source-locked 실자료는 OpenNeuro `ds006033` v1.0.1 (DOI `10.18112/openneuro.ds006033.v1.0.1`)이며, raw EEG 객체는 저장하거나 Git에 추가하지 않았다.
