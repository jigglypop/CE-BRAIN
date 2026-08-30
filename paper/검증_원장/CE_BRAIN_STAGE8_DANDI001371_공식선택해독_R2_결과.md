# CE-BRAIN Stage 8 DANDI 001371 공식선택해독 R2 결과

Status: `RAPID_CORRECTION_POISSON_CODE_NOT_ESTABLISHED_REPLICATED`

기준일: 2026-08-31

## 실행 보존

- 계약: `CE_BRAIN_STAGE8_DANDI001371_공식선택해독_R2_계약.md`
- 새 development subjects: S29-211118, S20-210519
- calibration S17과 confirmation S33·S28은 미개봉
- R1 세션 S34·S25는 재점수하지 않았다.

## 결과

### S29-211118

| region | units | encoder train/test | switch/stay correct | choice BA | choice perm p | DID | DID perm p | bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CA1 | 90 | 160/41 | 69/20 | 0.6413 | 0.08196 | 9.2201 | 0.001999 | [4.6705, 13.8182] |
| PFC | 52 | 160/41 | 69/20 | 0.5900 | 0.10745 | 4.1785 | 0.007996 | [1.3325, 7.1666] |

두 region 모두 DID 쪽에는 방향성 있는 부분 신호가 있었지만, choice-axis 양성대조를 통과하지 못했다.

### S20-210519

| region | units | encoder train/test | switch/stay correct | choice BA | choice perm p | DID | DID perm p | bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| CA1 | 72 | 72/19 | 26/8 | 0.9444 | 0.003998 | 5.9712 | 0.01649 | [3.5993, 8.6189] |
| PFC | 30 | 72/19 | 26/8 | 0.9000 | 0.06047 | 7.4340 | 0.24338 | [3.3475, 11.4649] |

CA1은 choice-axis 양성대조와 DID 방향·CI를 통과했지만 DID permutation이 사전 `p<0.01`을 넘었다. PFC는 높은 raw BA에도 permutation 양성대조와 DID permutation을 통과하지 못했다.

## 판정

**[판정]** `RAPID_CORRECTION_POISSON_CODE_NOT_ESTABLISHED_REPLICATED`.

R1 두 subjects의 단순 firing-rate 축과 R2 두 새 subjects의 공식-family Poisson 해독 모두 PFC 복제 문턱을 통과하지 못했다. 현재 DANDI 001371 development 자료에서 창·prior·bin·문턱을 더 조정해 구제하지 않는다.

**[family STOP]** within-trial rapid-correction family는 현재 STOP이다. 이는 prospective choice code 또는 flexible navigation 일반의 부재를 뜻하지 않는다. 선택 감도와 update DID가 같은 사전등록 사슬에서 두 개체에 재현되지 않았다는 뜻이다.

장기 `v_C`, 지속 representational change, READ/WRITE subspace는 이 결과로 답하지 못한다.
