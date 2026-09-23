# BA-OBS-DISC2R 검증 기록: 선택과 독립 환자 장벽

Status: COMPLETE

## 검증 질문

구현이 raw voltage를 읽을 수 있다는 사실만으로는 식을 지지하지 않는다. 이 검증은 D0에서 후보를 고르고, 그 선택을 보지 않은 환자 집단 D1·D2·D3에서 같은 endpoint와 같은 문턱으로 반복해, 시간 기준식보다 유클리드 거리 감쇠 `SC`가 더 나은지를 검사했다. 따라서 D0의 좋은 점수는 발견 단계일 뿐이며, 최종 해석은 D3과 음성 대조에 달려 있다.

## 독립성·수치 안정성 검증

최종 독립 감사는 74명이 stage 사이에서 전혀 겹치지 않고, 592 source와 5,920 version-locked range가 marker·range·endpoint·result hash chain으로 연결됨을 확인했다. raw payload를 저장하지 않았으며 P0 및 substantive P1은 비어 있었다. 감사 문서는 `artifacts/21-final-audit.md`에 있으며, 경로를 반영한 최종 감사 receipt SHA-256은 `434a9a977440b29c4878d9878859235a66a3ce28170887a2966dfbe988afc09b`다.

최종 post-run 근거는 hardened v2 receipt SHA-256 `743f54b7cb35f206b505b8b8f5ebd31e4db5aba5626138dfce220c8fd8b4efeb`, validator SHA-256 `85e4d2b07a18819018a179783e96d6a4e010376eca5cec2823b217004c8995cc`다. v2는 locked manifest에 592 source, 9,472 target, 5,920 range를 정확히 다시 결박했고, D0의 30개 fold loss를 재계산했다. 또한 40개 적합 receipt 각각의 training objective, 순서 있는 source offset, anchor-profile hash, numerical Jacobian/SVD·rank·condition gate를 다시 계산했으며, 결정론적 bootstrap/permutation block 5개를 재현했다. 독립 code review는 남은 P0가 없다고 판정했다. 원시 payload를 의도적으로 저장하지 않았으므로 기록된 SHA-256은 format·request-bound 값으로 남지만, 그 내용 digest 자체를 재해시하려면 새 외부 download I/O가 필요하다.

기존 v1 post-run receipt SHA-256 `b3f3f9a1d50f52337fe867f7ab9a1e99174bfcd74b6dd4802325763c2859c3be`도 보존한다. 다만 이는 lifecycle 수준의 역사적 검증이며, v2를 대체하거나 v2와 경쟁하는 최종 근거가 아니다.

P2에는 의도적으로 보존한 lifecycle 항목이 하나 있다. pre-D0 linkage test는 `d0-opened.json`이 없어야 한다고 검사하므로, 되돌릴 수 없는 D0 opening 뒤에는 `2 PASS / 1 FAIL`이 된다. 이것은 raw endpoint나 수치 gate의 실패가 아니라 pre-open 상태를 확인하는 테스트가 stage 뒤에 재실행되었기 때문이다. 이 테스트를 성공으로 고쳐 쓰지 않았고, 대신 읽기 전용 post-run validator가 결과의 정합성을 확인했다.

## 선택 단계

D0의 환자-blocked 6-fold CV에서 `SC`의 평균 **상대 CV 개선**은 $0.0638202$, fold win은 6/6이었다. 해부학적 거리 대체 후보 `SAC`은 상대 CV 개선 $0.0640458$, 6/6으로 수치상 조금 컸지만, 사전 고정한 $0.005$ tie band 안에 있으므로 더 단순한 `SC`가 선택됐다. 이는 유클리드 거리가 생물학적 경로라는 판정이 아니라, 지정한 후보군 안에서 설명 항 하나를 고른 규칙의 결과다.

## 순차 held-out 결과

| Stage | 환자 | `SC` 평균 절대 Huber-loss 개선 | 양의 참여자 | 불확실성 및 permutation | 판정 |
|---|---:|---:|---:|---|---|
| D1 | 8 | 0.0203434 | 7/8 | $p=1/512$ | 통과 |
| D2 | 12 | 0.0168684 | 10/12 | 80% LCB $0.0127012$, $p=1/1024$ | 통과 |
| D3 | 30 | 0.0173522 | 23/30 | 97.5% LCB $0.0102676$, $p=1/4096$ | 최종 통과 |

D3의 양의 개선은 source offset과 시간·연령 공통식을 이미 포함한 비교에서 남았다. 즉 이 결과는 단순히 가까운 source가 큰 반응을 낸다는 원자료 상관을 보고한 것이 아니라, 고정한 nuisance 구조 뒤에 거리 항이 남긴 held-out 예측 이득이다. 그러나 개선의 크기는 endpoint와 이 후보군에 한정되며, 전기 전도의 인과 기전이나 축삭 경로의 추정량은 아니다.

## 대조와 반증 범위

같은 분석을 자극 전 구간으로 옮긴 prestimulus 대조는 평균 개선 $0.0000445$, 양의 참여자 16/30, 97.5% LCB $-0.0001462$, $p=0.0568848$로 stage gate를 통과하지 못했다. 따라서 선택된 거리 항이 분석 창과 무관하게 나타나는 일반적 geometry artifact라는 설명은 이 대조와 맞지 않는다. 별도로 고정한 contact-mean diagnostic은 `REFERENCE_CONCORDANT`였다. 이 두 결과는 bipolar primary endpoint의 D3 통과를 보조하지만, 독립 dataset replication을 대신하지 않는다.

검증이 지지하는 문장은 좁다. 환자-disjoint 다환자 인간 SPES CCEP의 이 관측 kernel과 이 bipolar endpoint에서만, 단순 유클리드 거리 감쇠 `SC`가 지정한 시간 기준식보다 더 잘 예측했다. 생물학적 리만 계량·geodesic·conductance tensor, 무한차원 신경 상태, 의식·자아·해마·AGI는 이 검증의 관측 대상이 아니며 통과나 실패 어느 쪽으로도 판정하지 않는다.
