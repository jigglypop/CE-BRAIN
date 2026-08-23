# BA-SRM3 route register

Status: COMPLETE

| Route | 내용 | 현재 상태 | 승격 조건 |
|---|---|---|---|
| A | 동일 frozen train manifest + official sign-matched response QC | `INVALIDATED_CLAMP_UNIT_CONTRACT` | 같은 run에서 재개 금지 |
| B | BA-SRM2 strict `stim_pulse.qc_pass=1` | `STOP_PRESERVED` | 재개 금지; 새 source가 있어야 별도 후보 |
| C | small DB 12-slot pulse vector | `REJECTED_PRODUCER_ALIAS_BUG` | medium/full event row만 허용 |
| D | full waveform Hilbert output | `NOT_ACQUIRED / NOT_THIS_CONTRACT` | full DB와 새 prereg 필요 |
| E | conductance/$Npq$/STDP/homeostasis | `UNOBSERVED` | joint physiological source 필요 |

Route A가 실패하면 QC, target, pulse horizon 또는 dimension을 바꾸어 같은 run을 계속하지 않는다.

## 최종 경로 판정

Route A의 support 자체가 아니라 clamp-mode별 단위 분리 실패가 측정모형을 무효화했다.
따라서 BA-SRM3에서 dimension, rank threshold, kernel 또는 model family를 바꾸지 않는다.
후속 후보는 새 계약에서 current-clamp와 voltage-clamp command를 별도 typed channel로
표현하고 discovery, validation, confirmation을 분리해야 한다.
