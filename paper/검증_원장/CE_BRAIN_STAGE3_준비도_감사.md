# CE-BRAIN Stage 3 metric·graph·operator 준비도 감사

Status: `SCIENTIFIC_GATE_PASSED / CURRENT_APPARATUS_INSUFFICIENT_FOR_METRIC_AXIOMS`

## 목표

Phase 2E 통과로 개체 내부 Stage 3 후보 경쟁을 시작할 과학적 근거는 생겼다. 이 감사는 현재 자산이 매뉴얼의 대칭성·삼각부등식·방향성·일반 전이커널을 실제로 구별할 수 있는지 점검한다.

## 확인 결과

다운로드·해시 검증된 521885, 521886, 521887, 569070, 551399의 `intervals/trials/estim_target_region`을 확인했다. 다섯 동물 모두 자극원은 `MOs` 하나뿐이고 stimulus description은 `biphasic` 하나뿐이다.

현재 자료가 주는 것은

```text
MOs 한 자극원 → 여러 EEG receiver의 시간 반응
```

이지, 다음과 같은 다중 자극원 행렬이 아니다.

```text
source i → receiver j
source j → receiver i
source i/j/k 사이의 모든 쌍
```

## 식별 가능성과 불가능성

- **가능:** 한 자극원에서 상태·전류·시간에 따른 response kernel 및 transition operator 예측.
- **불가능:** `d(i,j)≈d(j,i)` 대칭성. 역방향 자극 `j→i`가 없다.
- **불가능:** `d(i,k)≤d(i,j)+d(j,k)` 삼각부등식. 세 source 사이의 쌍별 비용이 없다.
- **불충분:** local quadraticity. 독립적인 작은 공간 perturbation 방향이 아니라 같은 MOs의 세 전류만 있다.
- **따라서 금지:** receiver 채널 간 상관을 임의의 거리로 바꿔 Riemannian/Finsler/graph 승자를 선언하는 것.

## 목표 이탈 점검

Stage 3의 선행 과학 게이트는 통과했지만 장치 게이트는 통과하지 못했다. 이 상태에서 현재 DANDI 자료만으로 metric 후보 경쟁을 실행하면, 매뉴얼의 질문이 아니라 “단일 자극 response vector를 얼마나 잘 압축하는가”라는 다른 질문을 실험하게 된다.

## 다음 허용 행동

1. 다중 자극원과 공통 receiver를 가진 perturbational dataset을 우선 탐색한다.
2. source별 반복 trial, 양방향 source pair, 최소 세 source, held-out source가 가능한지 endpoint를 열기 전에 schema 감사한다.
3. 적격 자료가 없으면 현재 DANDI에서는 operator-only 보조 결과만 만들고, metric/graph 판정은 `UNIDENTIFIABLE`로 유지한다.
4. 인간 CCEP 다중 자극원 자료를 쓰려면 기존 outcome-known 계보를 그대로 재사용하지 않고 새 환자/새 holdout의 별도 Stage 3 복제로 등록한다.
