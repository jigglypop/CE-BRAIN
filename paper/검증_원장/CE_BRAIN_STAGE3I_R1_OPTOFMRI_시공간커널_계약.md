# CE-BRAIN Stage 3I R1 — opto-fMRI 시공간 커널 계약

## 목표와 이탈 점검

- **목표:** 40초 반응을 한 장의 공간지도로 평균하며 사라진 시간 순서를 복원했을 때, 여섯 자극원 사이 반응관계의 반복성과 고정 구조 연산자와의 관계가 살아나는지 검사한다.
- **가설 사다리상의 위치:** 매뉴얼의 일반 전이커널 `K(j,t|i,s,u,h)` 가운데 현재 자료로 식별할 수 있는 최소 조각 `K(j,t|i)`에 대응한다.
- **현재 단계가 필요한 이유:** Stage 3G의 직선거리와 Stage 3H의 고정 구조 profile은 모두 40초 평균 반응 RDM에서 실패했다. 시간 평균이 전파의 지연·순서를 지웠는지를 먼저 분리해야 한다.
- **이탈 여부:** 정렬됨. 이 검사는 국소 리만성, 삼각부등식, 인과적 전달속도를 직접 검사하지 않는다.
- **다음 게이트:** 시간 포함 반복성이 확보되면 상태·이력 조건 연산자로 확장한다. 반복성부터 실패하면 held-out을 열지 않고 움직임·slice timing·GLM을 포함한 논문급 전처리 재현이 선행 조건이다.

## 고정 입력과 표본 봉인

- Stage 3G에서 등록 게이트를 통과한 개발 12마리만 사용한다: Thy1 6, VGAT 6.
- 각 동물·자극부위의 첫 5회 반복만 사용한다.
- calibration/confirmation 각 6마리는 열지 않는다.
- 등록된 atlas foreground와 동물별 양의 baseline 상위값으로 정의한 동일 brain mask를 쓴다.
- 구조 후보는 반응 결과를 보기 전에 고정된 Stage 3H의 Thy1 1차, VGAT 3차 incremental propagation RDM을 그대로 쓴다.

## 시공간 반응표현

각 trial에서 0–39초 평균을 baseline으로 두고, 40–99초의 각 시점에 대해 MION 부호를 뒤집은 percent signal을 계산한다.

`response(j,t) = -100 * (signal(j,t) - baseline(j)) / baseline(j)`

홀수 반복 1·3·5와 짝수 반복 2·4를 각각 평균한다. 각 source의 `voxel × time` 배열을 펼친 뒤 source 쌍의 `1-Pearson correlation`을 계산한다. 홀수 RDM, 짝수 RDM, 두 방향을 평균한 cross-half RDM을 만든다. 따라서 공간 평균은 같아도 시간 순서가 다른 반응은 구분된다.

## 1차 게이트

유전자형별로 다음을 모두 요구한다.

1. 홀수 RDM과 짝수 RDM의 Spearman rho 중앙값 `>=0.30`.
2. 그 rho의 exact one-sided sign-flip `p<=0.05`.
3. 미리 고정한 구조 RDM과 cross-half 시공간 RDM의 rho 중앙값 `>=0.30`.
4. 구조 rho의 exact one-sided sign-flip `p<=0.05`.
5. 여섯 source 이름 720개 완전 순열 `p<=0.05`.

반복성은 통과하지만 구조관계가 실패하면 “시간정보는 측정되나 현재 고정 구조 연산자가 설명하지 못함”으로 판정한다. 반복성 자체가 실패하면 구조관계 수치는 기술만 하고 해석하지 않는다.

## 판정과 주장 상한

- 둘 다 통과: `SPATIOTEMPORAL_STRUCTURAL_RELATION_CANDIDATE`.
- 한 조건만 통과: `CONDITION_LIMITED_SPATIOTEMPORAL_STRUCTURAL_CANDIDATE`.
- 둘 다 실패: `SPATIOTEMPORAL_STRUCTURAL_RELATION_NOT_ESTABLISHED`.

통과해도 주장 상한은 “등록된 개발 표본의 6-source 전뇌 시공간 반응 RDM과 개체공통 구조 전파 profile의 연관”이다. 여섯 source는 국소 이웃의 미분구조를 식별하기에 부족하므로 국소 리만/핀슬러 기하의 증명이 아니다. 현재 입력은 저자 논문의 AFNI slice timing·motion correction 및 GLM을 완전히 재현하지 않은 등록 원자료라는 장치 한계를 함께 기록한다.
