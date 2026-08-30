# CE-BRAIN 현재 정지선 및 재개조건

Status: `DEVELOPMENT_BRANCHES_EXHAUSTED / EXTERNAL_EVIDENCE_REQUIRED`

기준일: 2026-08-31

## 1. 현재 결론

주어진 두 로드맵의 모든 단계가 완료된 것은 아니다. 다만 현재 저장소와 감사한 공개자료에서 **안전하게 실행할 수 있는 독립 development 분기**는 다음 지점까지 실행했다.

| 분류 | 현재 상태 |
|---|---|
| 재현된 좁은 사실 | history의 미래예측 유용성, 개체 내부 상태축과 recovery |
| 약화·기각된 강한 가설 | 동물 공통 강한 state×input 축, 현재 고정 local geometry·graph·operator 후보의 조건 일반화, recurrence가 history 이득을 고유하게 설명한다는 연결 |
| 반복 미확립 | trajectory memory, exact-item 관계복원, next-day dopamine update, within-trial rapid correction code |
| 현재 자료에서 식별 불가 | local→global 공간 접합, 기억 용량 scaling, 지속 `v_C`, 직접 chemical write gate, 동일자료 통합모델 |
| 추가 약한 chemistry 결과 | DANDI 000559 dopamine 개입 뒤 지속 행동은 방향 양수이나 exact p=0.133/0.251로 미확립 |
| Stage 3 새 후보 | DANDI 001612 실제 photostim 세션에 1,842 ROI는 있으나 public NWB에 target ID·stimulus timing·trial table이 없어 source-held-out 분석 불가 |
| Stage 3 실행 가능 대체자료 | Borealis 20-source VSD 장치는 통과했으나 12 development source에서 Euclidean +1.17% p=0.403, directed/kernel 음수로 unseen-source 일반화 미확립 |
| Stage 3 새 독립 장치 | CNIR opto-fMRI는 24동물×6 source×반복을 제공하며, 저자 자산 기반 atlas 등록 게이트까지 개발 12/12 통과 |
| Stage 3F–3I 실행 | native 40초 RDM, 등록 물리거리, 고정 구조 전파관계 모두 미확립. 시간 포함 RDM은 Thy1 반복성만 통과했지만 고정 구조관계는 실패; VGAT 반복성 실패 |
| 미허가 | Phase 13 독립 재현과 Phase 14 최종 인간 확인. freeze할 Phase 12 모델이 없다. |

`미확립`은 생물학적 부재의 증명이 아니고, `식별 불가`는 실험축이 없다는 뜻이다. 둘을 실패 하나로 합치지 않는다.

## 2. 왜 지금 더 돌리면 목표에서 벗어나는가

현재 calibration·confirmation을 열거나 같은 development 자료에서 창·거리·prior·bin을 더 바꾸면, 사전등록 실패를 사후 최적화로 구제하는 일이 된다. 서로 다른 종·과제의 전기·기억·화학 신호를 합치면 동일자료 통합 경쟁이 아니다.

따라서 현 자료로 더 많은 모델을 돌리는 것은 “끝까지 진행”이 아니라 claim ceiling을 무너뜨리는 우회다.

## 3. 재개에 필요한 최소 외부 입력

### 국소 기하 → 구조

- 두 개 이상 source와 여러 intervention을 같은 개체에서 반복
- source×target response와 해부학적 ground truth가 함께 존재
- held-out intervention과 held-out animal을 만들 수 있는 자료

이 자료에서 새 local predictor가 살아야 MICrONS blind wiring과 local→global 접합을 다시 연다.

### 기억 → 교정

- trial 의미와 정답·오류·학습/회상 epoch가 명시됨
- 같은 unit population에서 encoding, retrieval, 새 정보 뒤 지속 변화가 연결됨
- 새 dataset family 또는 새 participant/animal split

within-trial 선택변화만 있는 자료는 지속 `v_C`의 충분조건이 아니다.

### 화학 gate

- 같은 개체·시행의 electrical population trajectory
- ACh·DA·NE sensor 또는 인과 개입
- matched electrical condition with different chemical state
- 이후에도 남는 synaptic·representational·behavioral update

네 축이 한 비교 단위에 있어야 직접 write-permission을 검사한다.

### 통합·독립재현·인간

- 위 축들을 같은 자료계에서 경쟁시켜 freeze한 생존모델
- 그 뒤에만 새 dataset family에서 Phase 13의 7개 항목을 확인
- 아래 scale 예측을 freeze한 뒤에만 새 인간 환자/자료로 Phase 14 실행

## 4. 운영 판정

**[현재 정지선]** `STAGE3_FIXED_GEOMETRY_OPERATOR_STOP_CONDITIONAL_KERNEL_OR_NEW_LOCAL_DATA_REQUIRED`.

이는 연구 목표의 완료나 국소 기하의 수학적 기각이 아니다. atlas 등록 선행조건은 해결됐고,
개발자료에서 6-source 직선거리와 고정 구조 전파 profile은 40초 평균 및 최소 시공간 표현을
설명하지 못했다. 시간정보는 Thy1 반복성을 회복했지만 구조관계는 회복하지 못했고 VGAT은
반복성부터 실패했다. calibration과 confirmation은 계속 봉인한다.

현재 허용되는 Stage 3 후속은 (a) 저자 수준 slice timing·motion correction·GLM을 재현한 뒤
개체·상태·입력·history 조건부 `K(j,t|i,s,u,h)`를 새 계약으로 검사하거나, (b) 한 점 주변의
작은 다방향 perturbation을 반복하는 새 자료로 local quadraticity를 직접 검사하는 것이다.
같은 개발값에 맞춰 창·거리·전파차수를 더 고르는 것은 금지한다.

새 후보가 들어오면 반드시 `장치 감사 → outcome-blind 분할 → 계약 봉인 → development → calibration/confirmation` 순서로 재개한다.
