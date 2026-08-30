# CE-BRAIN Stage 8 DANDI 001371 빠른 교정 R1 결과

Status: `RAPID_CORRECTION_CODE_NOT_ESTABLISHED_REPLICATED`

기준일: 2026-08-31

## 실행 보존

- 계약: `CE_BRAIN_STAGE8_DANDI001371_빠른교정_R1_계약.md`
- development: S34-220623, S25-210916
- calibration S17과 confirmation S33·S28은 미개봉
- 분석 중 시간창·문턱·표현을 바꾸지 않았다.

## 결과

### S34-220623

| region | units | delay train/test | switch/stay correct | choice BA | choice perm p | DID | DID perm p | bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CA1 | 54 | 88/38 | 40/13 | 0.7244 | 0.01099 | -0.0788 | 0.4053 | [-0.9508, 0.8388] |
| PFC | 50 | 88/38 | 40/13 | 0.5597 | 0.2199 | -0.2326 | 0.6662 | [-1.0408, 0.5797] |

CA1 choice accuracy는 높았지만 사전 `p<0.01`을 근소하게 넘었고, correction DID는 음수였다. PFC는 선택축 양성대조부터 통과하지 못했다.

### S25-210916

| region | units | delay train/test | switch/stay correct | choice BA | choice perm p | DID | DID perm p | bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CA1 | 56 | 42/19 | 25/8 | 0.6667 | 0.1049 | 0.0530 | 0.1529 | [-1.3142, 1.2992] |
| PFC | 30 | 42/19 | 25/8 | 0.6282 | 0.1489 | 0.8533 | 0.0009995 | [-0.1233, 1.7711] |

PFC DID와 permutation은 방향성 있는 부분 신호였지만, choice-axis 양성대조가 실패했고 bootstrap 하한도 음수였다. 따라서 통과로 세지 않는다.

## 판정

**[판정]** `RAPID_CORRECTION_CODE_NOT_ESTABLISHED_REPLICATED`.

이 결과는 논문의 prospective code 일반을 반증하지 않는다. 사전등록한 단순 firing-rate 목표축이 두 세션에서 안정적 held-out 감도를 확보하지 못했으므로, 그 축 위의 switch 변화로 빠른 correction을 확인할 수 없었다는 뜻이다.

**[금지]** S25 PFC의 단일 부분 신호만 골라 성공이라 부르지 않는다. 동일 세션에서 창·축·문턱을 조정하면 탐색 진단일 뿐 R1 판정을 바꾸지 못한다.

**[다음 최소 의무]** 결과를 보지 않은 development subjects S29·S20의 다른 세션이 trial·unit 장치 문턱을 통과하는지 먼저 감사하고, 공식 논문 choice-decoder의 실제 입력·시간정렬을 outcome-known 양성대조로 분리 진단한다. 새 계약 없이는 재점수하지 않는다.
