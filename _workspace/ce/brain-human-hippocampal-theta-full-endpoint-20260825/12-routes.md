# 대안 경로 레인 — 전수 endpoint authority

Status: COMPLETE

| ID | 경로 | 판정 | 근거와 경계 |
|---|---|---|---|
| R0 | HPC5 JSON result validator를 그대로 사용 | REJECTED | clean trial에서 trialwise P2P를 다시 계산하지 못하고, bipolar availability를 raw-derived mask에서 강제하지 못하는 endpoint-authority P0가 있다. |
| R1 | selected-source witness + independent endpoint validator | SELECTED | rejected trial을 포함한 selected trace에서 QC→mask→baseline→두 P2P estimand→$D$/bootstrap/LOO/paired를 전량 재계산하여 R0의 두 P0를 닫는다. raw→witness 구간은 frozen loader provenance에 의존한다. |
| R2 | MIN20 유지 또는 관측 count에 맞춘 MIN10 | REJECTED | 전자는 저자 코드에 없는 분석자 conjunction이고 후자는 outcome tuning이다. zero-clean 정의역 외 임의 MIN gate를 두지 않는다. |
| R3 | literal MATLAB/FieldTrip/`fitlme` parity | BLOCKED | author archive의 PB 호출 결함, FieldTrip commit 미고정, MATLAB model engine 부재가 있다. corrected official release 또는 author environment receipt가 재개 조건이다. |

R1은 positive result를 얻기 위한 threshold 완화가 아니다. primary와 controls, window,
estimand, seed, draw 수와 all-or-none bipolar 규칙은 endpoint를 보기 전에 고정됐다.
PB, bipolar, early/prestim, LOO와 paired는 sensitivity/control이며 primary를 veto하거나
독립 replication으로 합산하지 않는다.

이 run은 동일 공개 7명 epilepsy-surgery 자료의 post-hoc descriptive comparison이다.
실제 인간 iEEG 계산이라는 사실은 보존하지만, causal stimulation effect, 건강인·모집단
일반화, 기억·의식, CE·AGI, exact published-model replication을 허용하지 않는다. 결과
방향에 따라 route·threshold·window·reference·estimand를 바꾸지 않는다.
