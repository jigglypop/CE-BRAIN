# CE-BRAIN Stage 3F R1 — opto-fMRI 상태별 source 관계기하 결과

## 실행 범위

계약 `CE_BRAIN_STAGE3F_R1_OPTOFMRI_상태관계기하_계약.md`를 먼저 봉인한 뒤 development
Thy1 6마리와 VGAT 6마리만 열었다. 각 동물의 여섯 source에서 acquisition 번호가 가장
이른 5 trial, 총 360 trial을 사용했다. calibration 6마리와 confirmation 6마리는 열지 않았다.

원격 EGG에서 내려받은 모든 개발 NIfTI는 gzip/NIfTI 해제가 완료됐고 고정 shape
`96 × 48 × 18 × 120`을 통과했다. 결과 artifact는
`data/external/ce_brain_stage3_optofmri/development_rdm_result.json`이다.

## 양성대조 — odd/even 반복 관계도

| 조건 | median Spearman | exact sign-flip p | 계약 문턱 | 판정 |
|---|---:|---:|---|---|
| Thy1 | 0.38036 | 0.03125 | median ≥ 0.30 AND p ≤ 0.05 | 통과 |
| VGAT | 0.06786 | 0.328125 | 동일 | 실패 |

Thy1 활성화에서는 여섯 source의 상대적 공간패턴 관계가 반복 반분할 사이에 재현됐다.
VGAT silencing에서는 현재 고정 창·native-grid 표현으로 같은 양성대조를 통과하지 못했다.

## 개체 holdout 일반화

| 조건 | LOO median Spearman | exact sign-flip p | 계약 문턱 | 판정 |
|---|---:|---:|---|---|
| Thy1 | 0.11607 | 0.03125 | median ≥ 0.30 AND p ≤ 0.05 | 실패 |
| VGAT | 0.15714 | 0.015625 | 동일 | 실패 |

점수 방향은 평균적으로 양수였지만 사전등록한 효과크기 문턱에 크게 못 미쳤다. 즉 일부 공통
순위 신호와 “새 동물에서도 쓸 수 있는 안정된 source 관계도”는 같은 말이 아니다.

## 조건 전이와 switching 진단

- cross-condition median Spearman: `-0.18929`
- cross-condition exact sign-flip p: `0.997803`
- within minus cross mean: `0.348512`
- genotype-label exact permutation p: `0.010823`

조건 사이 차이는 수치상 크고 permutation 문턱도 넘었다. 그러나 계약은 switching 판정 전에
두 조건의 반복성과 within-condition 일반화가 모두 살아야 한다. VGAT 반복 양성대조와 두
조건의 개체 일반화가 실패했으므로 이 차이는 **상태 전환 기하의 증거가 아니라 부차 진단**이다.

## 판정

**`STATE_RELATION_GEOMETRY_NOT_ESTABLISHED`**

## 문과 독자를 위한 해석

여섯 도시 사이의 “이동 난이도 순위표”를 동물마다 만들었다고 생각하면 된다. Thy1 한 동물
안에서는 같은 지도를 두 번 그렸을 때 어느 정도 비슷했지만, 그 지도를 다른 Thy1 동물에게
가져가면 충분히 맞지 않았다. VGAT은 같은 동물 안에서 두 번 그린 지도부터 안정적이지 않았다.
두 조건의 지도가 서로 달라 보이기는 했지만, 각 지도 자체가 동물 밖에서 재현되지 않으므로
“날씨가 바뀌어 도로망이 전환됐다”고 결론낼 수 없다.

## 주장 상한과 다음 의무

이 결과는 뇌에 국소 기하가 없다는 증명이 아니다. 고정한 native-grid 40초 반응표현에서
source 관계도가 새 동물로 일반화되지 않았다는 판정이다. 저자 atlas warp가 없는 원시 EPI를
물리 좌표로 오인하지 않았으므로 Euclidean·triangle·local quadraticity는 여전히 직접
미검사다. 같은 development 값에 맞춰 창·mask·trial 수를 바꾸지 않는다. 다음 물리기하
시도는 독립적으로 고정한 atlas registration 또는 저자 변환자산이 먼저 있어야 한다.
