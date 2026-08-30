# CE-BRAIN 실험 사다리 상태 원장

Status: `FULL_SCOPE_REALIGNED / STAGE3_TENSION / STAGE6_RECURRENCE_NOT_ISOLATED / STAGE7_TRAJECTORY_NOT_ESTABLISHED / STAGE9_CHEMICAL_NOT_ESTABLISHED`

이 원장은 사용자가 제공한 두 기준 문서, 곧 CE-BRAIN 전체 연구 로드맵과 실험 매뉴얼의 가설 계보를 현재 저장소의 실험 결과에 다시 맞춘다. 같은 `Stage` 번호를 쓰더라도 입력 자료, 반증 조건, 눈가림 절차가 다르면 같은 실험으로 인정하지 않는다.

## 1. 최종 목표와 현재 하위 목표

- **[미완성: 최종 목표]** 국소 전기동역학에서 시작해 기능적 간선, 공간 또는 연산자 구조, 해부학적 ground truth, 순환 차원, 기억, 회상·교정으로 이어지는 후보 제거형 증거 묶음을 만든다.
- **[미완성: 현재 하위 목표]** 국소기하·recurrence·trajectory/관계/빠른 correction·직접 chemistry의 현재 STOP을 보존하고, 남은 Phase 12–14가 요구하는 선행조건과 외부자료 정지선을 최종 대조한다.
- **현재 하위 목표의 완료 조건**은 실행 가능한 미개봉 development 분기와 선행단계 실패 때문에 미허가인 분기를 분리하고, 새 데이터·개입 없이는 답할 수 없는 항목을 정확히 목록화하는 것이다. confirmation을 열거나 서로 다른 자료를 사후 통합하지 않는다.
- **금지된 지름길**은 Stage 3 생존 후보 없이 Stage 4·5 기하를 실행하거나, 단순 history 이득을 순환차원·기억 용량의 증거로 부르거나, 관계복원 실패를 건너뛰어 capacity·correction을 실행하거나, dopamine/ACh의 서로 다른 과제를 합쳐 화학 gate를 증명했다고 부르는 것이다.

## 2. 단계별 현재 지위

| 기준 단계 | 실제 질문 | 현재 지위 | 다음 허용 행동 |
|---|---|---|---|
| Stage 0 | 합성자료에서 R/F/방향 그래프/전환/연산자/숨은상태/기억 후보를 구별하는가 | **[산출: 기록 결과]** 독립 successor 84/84 | 능력 검증으로만 보존 |
| Stage 1 | 단일 뉴런 반응에 과거 이력이 필요한가 | **[산출: 기록 결과]** Allen held-out 입력에서 history 후보 지지 | 간선·기하의 증거로 승격 금지 |
| Stage 2 | 고정 해부학에서 상태가 바뀌면 상대 전달관계가 바뀌는가 | **[산출: 긴장]** 단일 동물에서 `STAGE2_TRANSFER_TENSION`; 전류별 효과가 달랐음 | 상태와 입력의 상호작용으로 피벗 |
| Stage 2B | awake→isoflurane 변화가 recovery에서 awake 쪽으로 돌아오는가 | **[산출: 혼합]** 543393은 recovery 실패, 543394는 통과 | 강한 `상태→기하` 경로 보류; 개체차·전류·드리프트 분해 |
| Phase 2 | `T(s,u)=A(s)B(u)` 대 `T(s,u)\neq A(s)B(u)` | **[산출: 완료]** 새 동물·새 전류 holdout에서 `STATE_INPUT_SEPARABLE_RETAINED` | M1 대 0효과/global gain 독립 확인 |
| Phase 2C | 세 동물에 공통인 상태축이 새 동물에서도 맞는가 | **[산출: 실패]** 상태 차이는 있으나 `STATE_AXIS_NOT_ESTABLISHED` | 개체축·전류별 연산자·불안정성 경쟁 |
| Phase 2D | 새 동물 내부에서 전류를 가로지르는 개체축이 안정적인가 | **[산출: 제한적 지지]** `INDIVIDUAL_AXIS_SUPPORTED`; 한 target 동물, recovery 없음 | recovery-bearing 다중전류 동물 복제 |
| Phase 2E | 새 다중전류 동물에서 개체축과 recovery가 함께 재현되는가 | **[산출: 통과]** `INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED` | 개체 내부 Stage 3 계약 허용 |
| Stage 3 | 같은 전달행렬에서 metric/graph/operator 후보 경쟁 | **[산출: 표현 긴장]** 다중 source·교란·조건별 재학습에서 생존 후보 없음 | 고정 기하·대체 연산자 분기 중단; 새 독립 자료 없이는 구제 금지 |
| Stage 4 | 기능자료만으로 구조를 예측·해시한 뒤 MICrONS EM 공개 | **[중단: 미허가]** | Stage 3 생존 후보가 새로 확립될 때만 재개 |
| Stage 5 | local/global manifold | **[중단: 미허가]** | 확립된 국소 구조 없이 실행 금지 |
| Stage 6 | 순환 동역학이 미래 예측 차원을 설명하는가 | **[산출: 반복 미통과]** 두 개발개체에서 history 유용, recurrence 고유 이득 미격리 | 확인군 봉인; 기억용량 원인 연결 금지 |
| Stage 7 | 기억이 정적 상태보다 trajectory로 복원되는가 | **[산출: 반복 미확립]** CRCNS 두 topdir에서 encoding·trajectory 문턱 실패 | 다른 memory code 탐색 |
| Stage 8 | retrieval과 correction이 분리되는가 | **[미실행: 미허가]** | 의미가 명시된 encoding/retrieval/rule-change 자료 필요 |
| Stage 9 | 화학상태가 다음 장기변화를 추가 예측·조절하는가 | **[산출: 개발 미통과]** dopamine 추가예측이 새 동물로 일반화되지 않음 | 확인군 봉인; 인과 chemical gate 미허가 |
| Stage 10 | 살아남은 구조를 동일자료에서 통합 경쟁하는가 | **[식별 불가]** 자료계가 서로 다르고 생존 후보 부족 | 동일 자료계 통합계약 필요 |
| 로드맵 Phase 9–14 | 기억용량, 교정, 화학, 통합, 독립재현, 인간 | **[대부분 미실행]** | 전체 완료조건 감사의 순서를 따름 |

## 3. 잘못 연결했던 실험의 격리

- **[무효: 이 계보의 Stage 3로서]** 인간 CCEP에서 Euclidean 감쇠 후보를 고른 분석은 별도 CCEP 계보의 탐색·재분석이다. DANDI Stage 2 전달행렬을 사용하지 않았으므로 이 매뉴얼의 Stage 3 완료로 세지 않는다.
- **[무효: 이 계보의 Stage 4로서]** 구조 간선 라벨을 처음부터 사용한 MICrONS 분류 분석은 outcome-known 진단이다. 기능자료만으로 예측을 고정하고 해시한 뒤 EM을 여는 anatomy-blind 검증이 아니므로 이 매뉴얼의 Stage 4 완료로 세지 않는다.
- 위 두 결과는 삭제하지 않지만 이 원장의 진척률과 `국소 뇌 기하 실패` 판정에는 사용하지 않는다.

## 4. Stage 2B가 실제로 말하는 범위

기록된 두 동물의 recovery 비율은 다음과 같다.

| 동물 | 전류 | `D(awake,iso)` | `D(awake,recovery)` | `Q` | 판정 |
|---|---:|---:|---:|---:|---|
| 543393 | 70 μA | 0.275826 | 0.320307 | 1.161266 | 상태 변화는 있으나 recovery 실패 |
| 543394 | 50 μA | 0.578052 | 0.206017 | 0.356398 | 상태 변화와 recovery 통과 |

**[산출]** 두 동물이 같은 방향으로 재현되지 않았으므로 강한 보편 명제 `상태만 알면 기능적 공간이 정해진다`는 승격되지 않는다.

**[미완성]** 이 불일치는 기하의 반례가 아니다. 전류가 70 μA와 50 μA로 다르고 동물도 다르므로, 입력 효과와 개체 효과가 서로 얽혀 있다. 먼저 이를 분해해야 한다.

## 5. Phase 2 무결과 데이터 적격성 감사

공식 DANDI API와 NWB `intervals/trials` 표만 읽었고, 신경반응 endpoint는 열지 않았다. 판본은 `000458@0.230317.0039`이다.

| 동물 | 상태 | 전류 | 칸별 trial 수 | 역할 |
|---|---|---|---:|---|
| 521885 | awake, isoflurane | 20, 50, 100 μA | 60 | 두 상태의 다중 전류 개발/교차동물 검증 |
| 521886 | awake, isoflurane, recovery | 20, 50, 100 μA | 100 | 완전 3×3 핵심 요인 설계 |
| 521887 | awake, isoflurane, recovery | 20 μA | 200/300/300 | 20 μA 교차동물 검증 |
| 543393 | awake, isoflurane, recovery | 70 μA | 300 | 70 μA recovery 기록 결과 |
| 543394 | awake, isoflurane, recovery | 50 μA | 300 | 50 μA 교차동물/recovery 기록 결과 |

핵심 자산 잠금:

| 동물 | asset UUID | SHA-256 |
|---|---|---|
| 521885 | `6ab37be4-adfe-4bea-a031-eb1a2b0782a8` | `b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171` |
| 521886 | `d77558e6-1b16-49c2-9f61-885d63701331` | `a799afdf771a5f629e19312d37714b0990418cef0d2b7425b46e17574678fcb6` |
| 521887 | `ec27a42e-098f-418e-b5e6-1424d5bbdb90` | `716e5372de827ab0a72fae5036045527f5e884bcc5a48215bba278fbb516521e` |
| 543393 | `73689194-02e4-40c5-9936-5c6ed7cfb99d` | `78e4809d903aea2261c302799b3ee03b899f01183ccbf434af8671afc6fba332` |
| 543394 | `f00ff515-1833-4f4f-bd9e-9c7dbf353397` | `3d9b703e2c96428cad82af4ff13f8f4d1f4c7302c758fad4243220854dbb4c1c` |

**[산출: 설계 적격성]** 521886에는 상태와 전류를 분리해 볼 수 있는 완전요인 설계가 있다. 521885와 521886의 공통 `awake/isoflurane × 20/50/100 μA`는 제한적인 held-out animal 검증을 허용한다.

**[한계]** recovery의 완전요인 반복은 521886 한 동물뿐이다. 따라서 recovery까지 포함한 보편적 상태×입력 법칙은 이 자료만으로 확증할 수 없다. 521887·543393·543394의 단일 전류 자료는 외부 전류점 점검에는 쓰지만, 한 동물 안의 상호작용을 단독 식별하지 못한다.

## 6. 다음 실행의 사전 고정 골격

반응을 열기 전에 다음을 별도 계약으로 고정한다.

1. 동일한 channel·time grid에서 trial 반응을 `animal × state × current × time × channel` 텐서로 만든다.
2. 전역 gain만 달라진 경우를 제거하고 상대 전달 패턴을 점수화한다.
3. M1은 상태 효과와 입력 효과의 분리가능 저랭크 모형, M2는 명시적 `state × current` 상호작용 모형으로 둔다.
4. 같은 자유도 예산 또는 nested penalty를 사용하고, trial이 아니라 동물·전류 블록을 holdout 단위로 삼는다.
5. 521885/521886의 leave-one-animal-out과 leave-one-current-out을 주 판정으로 사용한다. recovery는 521886 내부 진단과 단일 전류 동물의 방향 일치만 보고 보편 확증으로 세지 않는다.
6. block drift, 개체별 baseline, 자극 순서, running/invalid trial, channel 결측, 비정상 연산자를 대조한다.
7. M2가 새 동물과 새 전류에서 함께 이기지 못하면 `STATE_INPUT_NOT_ESTABLISHED`로 닫는다. 이때 Stage 3으로 올라가지 않고 drift·heterogeneity·nonstationary operator 경로 중 사전 등록한 다음 분기로 이동한다.

## 7. 현재의 쉬운 말 결론

지금 실패한 것은 “뇌에 국소 기하가 존재한다”가 아니다. 실패한 것은 더 앞단의 강한 가정, 즉 **뇌 상태 하나만 알면 전달구조를 정할 수 있다**는 생각이다. 같은 마취·각성 변화라도 자극 세기와 동물에 따라 결과가 달랐다. 그래서 현재 질문은 지도가 유클리드인지 리만인지가 아니라, **지도 자체가 상태와 입력의 조합에 따라 바뀌는가**이다.

이 질문이 먼저 해결되어야만 같은 전달행렬을 거리, 방향 그래프, 전환 연산자 중 무엇으로 읽을지 정당하게 경쟁시킬 수 있다.

## 8. Phase 2 실행 결과

봉인된 521886 확인 endpoint를 실행하고 원자료에서 독립 재계산했다. M1은 세 전류 모두에서 M2보다 오차가 작았고, 평균오차는 `0.369712` 대 `0.424979`였다. M2 상대 개선율은 `-0.149488`, bootstrap 95% 구간은 `[-0.551496,-0.124748]`였다.

**[산출]** 등록된 해상도에서 상태×전류가 전달 대비의 방향을 바꾼다는 강한 상호작용은 지지되지 않았다. 전류별 크기 변화를 허용하되 공통 방향을 쓰는 rank-1 분리가능 후보를 유지한다.

**[미완성]** 이 결과는 M1과 무신호/global gain을 비교하지 않았다. 따라서 state-dependent edge와 geometry는 아직 승격되지 않으며 Stage 3은 계속 미허가다. 상세 수치와 영수증은 `CE_BRAIN_PHASE2_상태입력_결과.md`가 정본이다.

## 9. Phase 2C 공통 상태축 독립 확인

미개봉 동물 521887의 20 μA 확인 endpoint에서 awake–isoflurane 차이는 유의했다(`p=0.001`, raw gain residual `R=0.701467`). 그러나 앞선 두 동물의 공통 rank-1 축은 0효과보다 1.30%만 개선했고 signed cosine은 `0.174757`이었다. 두 bootstrap 하한은 각각 `-0.020307`, `-0.070723`으로 0을 넘지 못했다. recovery도 `Q=1.118803`으로 실패했다.

**[산출]** 상태 차이는 존재하지만 세 동물에 공통인 하나의 상태축은 확립되지 않았다. 공통 상태축을 전제로 한 강한 geometry 경로는 중단한다.

**[미완성]** 남은 후보는 개체별 안정 축, 전류별 독립 연산자, block drift·비정상성이다. 다음 계약은 이 네 후보를 미개봉 다중전류 동물의 confirmation trial에서 경쟁시킨다.

## 10. Phase 2D 개체축·연산자 경쟁

미개봉 동물 569070의 20/40/60 μA에서 짝수 trial로 학습하고 홀수 trial로 확인했다. 개체 내부 rank-1 축 `I`의 오차는 `0.041045`로 0효과 `0.143796`보다 71.46% 작았다. 앞선 동물의 공통축 `G`보다도 66.22% 개선됐고 그 bootstrap 하한은 26.40%였다. 전류별 독립 연산자 `K`는 `I`보다 오차가 70.23% 더 커, 자유도가 큰 전류별 방향이 확인 자료로 일반화되지 않았다.

**[산출]** 한 동물 안에서는 전류를 가로지르는 안정적인 개체 고유 상태축이 지지됐다. 공통축 실패의 현재 최선 설명은 “기하가 전혀 없음”보다 “동물마다 좌표축이 다름”이다.

**[긴장]** 20 μA 상태 대비는 permutation `p=0.655`였고, 40·60 μA만 `p=0.001`이었다. 또한 유효 recovery가 없다. 따라서 세 전류의 보편 상태축, 가역성, 국소 기하를 확립한 것으로 승격하지 않는다.

**[다음 최소 증명 의무]** 유효 recovery가 있는 새 다중전류 동물에서 개체축을 독립 복제하고, 축 정렬과 awake 복귀를 함께 통과해야 Stage 3 후보 경쟁이 허용된다. 상세 결과와 영수증은 `CE_BRAIN_PHASE2D_개체축_연산자_결과.md`가 정본이다.

## 11. Phase 2E 개체축·가역성 독립 복제

미개봉 동물 551399의 40/60/80 μA 확인 자료에서 개체축 I는 0효과보다 오차를 80.29% 줄였고 bootstrap 하한은 59.75%였다. 전류별 독립 K는 I보다 32.29% 나빴다. recovery Q는 `0.722768 / 0.548705 / 0.447148`, 각 bootstrap 상한은 모두 1 미만이었다. 시간 전반·후반도 모두 Q<1이었다.

**[산출]** 개체 내부 상태축과 awake 복귀가 새 다중전류 동물에서 함께 독립 재현됐다. Phase 2D의 단일 target 결과가 recovery-bearing 동물로 확장됐다.

**[허가]** 개체별 좌표를 전제로 한 Stage 3 metric/graph/operator 후보 경쟁을 시작할 수 있다.

**[한계]** 동물 공통 좌표축은 여전히 확립되지 않았다. Stage 3 허가는 개체 내부 후보 경쟁에만 적용되며, anatomy-blind Stage 4나 기억·교정 명제는 아직 미허가다. 상세 결과는 `CE_BRAIN_PHASE2E_개체축_가역성_복제_결과.md`가 정본이다.

## 12. Stage 3 장치 준비도

해시 검증된 다섯 DANDI 동물의 trial schema에서 자극원은 모두 `MOs` 하나뿐이었다. 따라서 역방향 쌍이 필요한 대칭성, 세 source가 필요한 삼각부등식, 여러 공간 perturbation 방향이 필요한 local quadraticity를 현재 자산으로는 식별할 수 없다.

**[산출: 장치 한계]** Phase 2E는 Stage 3을 물리적으로 정당화했지만, 현재 DANDI 파일만으로 Riemannian/Finsler/graph/operator 전체 경쟁을 실행하도록 허가하지 않는다. 단일 source transition operator 보조분석은 가능하지만 geometry 승자 판정과는 분리한다.

**[다음 최소 증명 의무]** 최소 세 자극원, 공통 receiver, 양방향 source pair, 반복 trial, held-out source를 갖춘 새 perturbation 자산을 endpoint-blind로 고정한다. 상세 감사는 `CE_BRAIN_STAGE3_준비도_감사.md`가 정본이다.

## 13. Stage 3A 선충 다중 source 실행 결과

DANDI `001075@0.240930.1859`의 110개 선충 segmentation NWB를 사용해 다중 source 후보 경쟁을 실행했다. R1은 canonical node 0개 개체의 좌표 정렬에서, R2는 ragged trace의 `NaN` 전파에서 장치 중단됐다. R3는 receiver별 finite frame만 쓰도록 수정했으나 사전등록 coverage 문턱을 충족하지 못했다. 이 세 중단은 과학 승패가 아니라 장치·표본수 중단으로 보존한다.

후속 R5 탐색 분석은 development 10,766행과 confirmation 4,631행을 사용했다. common pair에서는 F가 가장 낮은 log loss를 보였지만 null 대비 개선 3.38%의 bootstrap 하한이 -1.05%였고, F 대 R 개선도 0.234%에 불과했다. unseen source에서는 O가 1위였지만 null 대비 1.37%, 하한 -1.27%로 지지 문턱을 넘지 못했다.

**[산출: 탐색적 긴장]** `EXPLORATORY_REPRESENTATION_TENSION`. 국소 기하, 방향성 기하, switching, graph, 일반 연산자 중 독립 확인 승자는 없다.

**[식별 불가]** 3개체 이상 반복된 양방향 pair는 3개, directed triad는 125개뿐이라 대칭성과 삼각부등식의 강한 공리 판정은 불충분하다. 삼각부등식은 `NOT_IDENTIFIABLE`이다.

**[현재 지위]** Stage 3 확인적 통과가 아니며 Stage 4는 계속 미허가다. “국소 기하가 반증됨”이 아니라 “새 source 일반화와 공리 표본이 부족해 아직 확립되지 않음”이 정확한 결론이다. 정본 수치와 영수증은 `CE_BRAIN_STAGE3A_R5_탐색결과.md`에 있다.

**[다음 최소 증명 의무]** 새 다중 source 자료에서 directed pair와 triad 반복수를 사전 문턱 이상 확보하고, held-out source에서 후보가 null 대비 5% 이상 개선하면서 bootstrap 하한 >0을 통과하도록 독립 복제한다.

## 14. Stage 3B `unc-31` 회로 교란 외삽

공식 OSF `E2SYT`의 WT 113개체와 `unc-31` 18개체 처리자료를 해시 고정했다. WT 세 세션은 label/signal 열 수 불일치로 사전 제외했고, WT 107개체·150,870간선으로 후보를 학습한 뒤 `unc-31` 15개체·36,201간선을 확인에 사용했다. common-pair 23,582행과 unseen-source 11,852행으로 모든 coverage 문을 통과했다.

common-pair에서는 R이 null보다 0.108% 개선했으나 bootstrap 하한 -0.182%였고, unseen-source에서는 F가 0.275% 개선했으나 사전 문턱 5%에 크게 못 미쳤다. common과 unseen의 승자도 R/F로 달랐다. graph는 common-pair에서 null보다 7.15% 악화됐다.

양방향 pair 683개와 50,000개 directed triad를 사용했다. triangle 10% slack 위반률 상한은 9.158%로 공리 진단 하나는 통과했지만, R의 예측력이 null을 이기지 못해 Riemannian-like 후보로 승격할 수 없다.

**[산출: 교란 외삽 긴장]** `CROSS_GENOTYPE_REPRESENTATION_TENSION`.

**[해석]** Stage 3A의 표본수 부족만이 실패 원인이 아니었다. 충분한 간선과 삼각형을 가진 독립 유전자 조건에서도 고정 좌표 표현의 예측 이득이 사실상 0에 가까웠다. 국소 기하의 논리적 부재가 증명된 것은 아니지만, 조건을 넘어 일반화되는 전파 지도라는 강한 가설은 현재 지지되지 않는다.

**[현재 지위]** Stage 3 고정 기하 분기는 미통과이고 Stage 4는 계속 미허가다. 다음 정본 분기는 고정 기하의 추가 독립 복제 또는 `condition-dependent operator` 새 계약이다. 상세 결과는 `CE_BRAIN_STAGE3B_UNC31_교란외삽_결과.md`가 정본이다.

## 15. Stage 3C 조건의존 연산자 탐색

Stage 3B endpoint 공개 뒤의 탐색 분석으로, WT 구조를 `unc-31`에 맞춰 출력만 보정한 후보 `C`와 `unc-31` development 자료에서 구조 전체를 재학습한 후보 `U`를 비교했다. 평가는 별도 `unc-31` 6개체·6,344행에서 수행했다.

가장 좋은 조건별 후보 `U_F`는 같은 구조의 보정 후보 `C_F`보다 log loss를 0.0813%만 개선했고 bootstrap 하한은 -0.1302%였다. 구조 없는 `U_N`보다도 0.2263% 개선에 그쳤고 하한은 -0.3840%였다. 차순위 후보와의 차이도 0.0535%였으며 하한이 0 아래였다. 사전 고정한 3%·5%·3% 문턱을 모두 충족하지 못했다.

**[판정]** `CONDITION_DEPENDENT_OPERATOR_NOT_ESTABLISHED`.

**[계획 정렬]** metric 실패 시 operator/dynamic graph로 이동한다는 매뉴얼의 대체 분기까지 검사했으나 생존 후보가 없었다. 따라서 Stage 4·5 기하 분기는 중단하고, Stage 6 순환차원을 해부 기하와 독립된 동역학 가설로 재계약해 진행한다. 상세 수치와 후속 허가표는 각각 `CE_BRAIN_STAGE3C_조건의존연산자_결과.md`, `CE_BRAIN_STAGE3_후속분기_게이트감사.md`가 정본이다.

## 16. Stage 6 Allen 개발자료 장치 감사

DANDI `000021@0.251116.2246`의 214개 자산을 endpoint-blind로 목록화했다. 32개 subject를 development 19, calibration 9, confirmation 4로 해시 분할했으며 neural endpoint는 열지 않았다. 기존 독립 확인용 DANDI `001695` 봉인도 유지했다.

**[장치 판정]** `METADATA_PASS_SCHEMA_PENDING`. 가장 작은 development session도 1.74GB이고 현재 전송 속도에서 약 1시간이 예상돼 FAST 감사 중 전체 다운로드를 중단했다. 불완전 복사본은 삭제했고, 이는 과학 결과로 세지 않는다.

**[다음 최소 증명 의무]** development session의 공식 SHA-256을 검증한 뒤 unit·stimulus·behavior schema와 strict-past 시간 분할 가능성만 확인한다. 상세 계약과 감사는 `CE_BRAIN_STAGE6_ALLEN_장치계약.md`, `CE_BRAIN_STAGE6_ALLEN_장치감사.md`가 정본이다.

## 17. Stage 6 R1 순환예측 개발 실행

development subject `707296975`의 자연영화 20회 반복과 품질 기준을 통과한 시각 unit 214개를 사용했다. 첫 stimulus block에서 학습·rank 선택을 하고 시간적으로 떨어진 두 번째 block 10회에서 다음-frame 예측을 평가했다.

교차축 순환 후보 `R`은 자극 평균 `N`보다 3.6943% 개선했고 bootstrap 하한도 3.2248%로 양수였다. 강한 mode 제거 `M`과 좌표 permutation `P`보다도 안정적으로 나았다. 그러나 축별 자기상관 `D`보다 개선은 -0.0433%, 하한 -0.1997%로 오히려 근소하게 나빴다.

**[판정]** `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED`. history와 population mode의 예측 유용성은 보였지만, 교차축 순환차원의 고유 이득은 분리되지 않았다.

**[현재 지위]** 단일 development subject 결과이므로 Stage 6 최종 판정이 아니다. 동일한 고정 후보와 문턱을 다음 development subject에 적용해 방향 일치 여부를 확인한다. 상세 결과는 `CE_BRAIN_STAGE6_R1_순환예측_결과.md`가 정본이다.

## 18. Stage 6 R2 개발개체 복제

두 번째 후보 subject `719828686`은 자연영화 시작시각 역전 2곳 때문에 score 전 `STAGE6_STRICT_PAST_SCHEMA_STOP`으로 격리했다. 행 정렬이나 삭제로 구제하지 않았다.

다음 적격 development subject `740268983`에는 R1 코드와 문턱을 그대로 적용했다. `R`은 `N`보다 5.8025%, `M`보다 5.1650%, `P`보다 8.7622% 개선했고 각 bootstrap 하한이 양수였다. 그러나 `D`보다 추가 개선은 0.3111%로 사전 0.5% 효과크기 문턱을 넘지 못했다.

**[판정]** `HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED_REPLICATED`.

**[해석]** 두 development 개체에서 history와 population mode의 예측 유용성은 반복됐다. 교차축 순환의 고유 이득은 두 개체 모두 문턱을 넘지 못했다. 따라서 이 선형 한-frame Stage 6 후보는 confirmation 개방 자격이 없으며 confirmation 4개체와 DANDI `001695`는 계속 봉인한다.

**[후속 분기]** Stage 7 기억 궤적을 독립 계약으로 진행하되, 순환차원이 기억 용량의 원천이라는 연결 명제는 사용하지 않는다. 시간역전 중단과 복제 결과의 정본은 각각 `CE_BRAIN_STAGE6_R2_시간역전_장치중단.md`, `CE_BRAIN_STAGE6_R2_개발개체복제_결과.md`다.

## 19. Stage 7 R1 해마 기억궤적 개발 실행

CRCNS hc-3의 endpoint-blind 선형 트랙 세션 `ec013.40/ec013.719`를 고정했다. 왕복 122회와 CA1 pyramidal unit 43개를 사용했으며, 시간순으로 train 72·validation 24·encoding-test 26회로 나눴다. 계약·코드·입력·실행환경을 manifest `f1fe20f5...`로 봉인한 뒤 한 번 실행했다.

위치 해독은 정적 occupancy 기준보다 36.26% 좋아졌지만 median absolute error가 트랙의 26.57%로, 사전 문턱 15%를 넘었다. 따라서 replay를 기억 궤적으로 해석하는 encoding 허가가 실패했다.

보조적으로 304개 ripple 후보 중 41개가 활성도 조건을 만족했다. 실제 order score의 time-shuffle 대비 차이는 0.00536, cell-shuffle 대비 차이는 0.00731에 불과했고 두 bootstrap 하한은 음수였다. distance 차이도 두 대조 모두 음수였다. 두 대조의 95 percentile을 동시에 넘은 사건은 2/41(4.88%), binomial `p=0.6145`였다.

**[판정]** `TRAJECTORY_MEMORY_NOT_ESTABLISHED`.

**[해석]** 이 결과는 해마 replay 일반의 부재를 증명하지 않는다. 이 개발 세션과 고정 분석기에서 위치 encoding 정확도와 trajectory 대조가 모두 사전 기준을 통과하지 못했다. 원자료 재계산은 저장 결과와 일치했다.

**[현재 지위]** Stage 8 인출·교정은 미허가다. 같은 공개 test를 보고 조정한 분석은 탐색으로만 취급한다. 다음 확인적 실행에는 endpoint-blind 새 해마 세션과 validation-only decoder 교정 계약이 필요하다. 상세 수치와 영수증은 `CE_BRAIN_STAGE7_R1_기억궤적_결과.md`가 정본이다.

## 20. Stage 7 R2 독립세션 장치 분기

R1과 다른 topdir 중 CA1 pyramidal unit 수를 우선해 `ec016.17`을 선택했다. 첫 선택기에서 `video_type="-"`를 영상 존재로 잘못 읽은 의미 오류를 endpoint 다운로드 전에 발견해 원본 영수증을 보존하고 교정했다. 영상 유무 조건을 제거해도 topdir과 archive 최소 세션 `ec016.234`의 선택은 같았다.

공식 MD5를 검증한 archive에는 처리된 `.whl`이 실제로 있었다. LFP·position duration은 일치했지만 원시 위치 유효률이 86.26%로 R1 장치의 90% 문턱을 실패했다.

**[장치 판정]** `STAGE7_R2_POSITION_APPARATUS_STOP`. ripple·replay score 전 중단이며 과학 음성으로 세지 않는다.

**[다음 분기]** 같은 독립 topdir에서 남은 유일한 선형 세션 `ec016.233`을 R2B fallback으로 사전 고정하고 동일한 원시 위치 90% 문턱을 유지한다. 선택 오류 교정과 중단의 정본은 `CE_BRAIN_STAGE7_R2_선택장치_교정.md`, `CE_BRAIN_STAGE7_R2_위치장치중단.md`다.

## 21. Stage 7 R2C 기억궤적 독립 개발 복제

R2B fallback `ec016.233`은 원시 위치 유효률 94.05%를 통과했으나 metadata CA1 unit 84개 중 실제 cluster에 존재하는 unit이 75개여서 84/84 계약에서 score 전 중단됐다. 이 판정을 보존하고, 실제 존재 unit 30개 이상을 요구하는 새 R2C 계약을 봉인했다.

R2C는 왕복 64회를 train 38·validation 12·test 14로 나눴다. 16개 해독 후보 중 validation에서 sigma 0.5 bin·uniform prior·0.2초 후보가 선택됐다. 그러나 test median absolute error는 트랙의 29.69%로 15% 문턱을 실패했다. 정적 기준 대비 개선은 29.56%였다.

적격 ripple 54개 중 두 null에 동시 유의한 사건은 2개(3.70%), binomial `p=0.7592`였다. order의 null 대비 차이는 0.0542와 0.0242로 사전 0.10 문턱보다 작았고 bootstrap 하한은 양수가 아니었다. distance 하한도 음수였다.

**[판정]** `TRAJECTORY_MEMORY_NOT_ESTABLISHED_REPLICATED`.

**[해석]** 서로 다른 두 development topdir에서 위치 관련 신호의 정적 기준 대비 유용성은 반복됐지만, 정확한 encoding과 ripple 내 시간순 trajectory는 확립되지 않았다. 이는 해마 replay 일반의 부재를 증명하지 않으며 현재 해독 장치의 감도 한계와 생물학적 부재를 분리하지 못한다.

**[현재 지위]** Stage 8 retrieval·correction은 미허가다. 다음 Stage 7 확인 시도는 trial·epoch 의미가 명시된 새 자료와 방향별·상태공간 decoder의 train/validation-only 고정이 필요하다. R2B 중단과 R2C 결과는 `CE_BRAIN_STAGE7_R2B_세포대응_장치중단.md`, `CE_BRAIN_STAGE7_R2C_기억궤적_결과.md`가 정본이다.

## 22. Stage 8·9 분기와 dopamine 장치

Stage 7이 두 development topdir에서 미통과했으므로 매뉴얼 의사결정 트리에 따라 Stage 8 retrieval/correction 확인은 미허가다. 좌표가 충분히 복원되지 않은 상태의 recall/correction 방향 cosine은 READ/WRITE subspace를 식별하지 못한다.

2026-08-31 최신 자료 감사에서는 행동과 dopamine 학습을 함께 담은 DANDI `001632@draft`가 발견됐다. 1,222 asset·126 subject·4.106GB 전체 목록을 inventory `ac3fa305...`로 잠그고 조건별 subject를 development/calibration/confirmation으로 해시 분할했다.

처음 선택한 plain 30·60·300·600초 cohort는 day01과 모든 day01~day08에서 행동 event만 있고 실제 chemical instance는 없었다. R1/R2는 각각 `STAGE9_DA_SCHEMA_STOP`, `STAGE9_DA_LONGITUDINAL_SCHEMA_STOP`으로 보존한다. 이는 chemical 과학 음성이 아니라 cohort 장치 오류다.

논문 원문과 inventory의 별도 `60sD`·`600sD` cohort가 dLight1.3b 측정군에 대응하므로 R3 장치 계약을 새로 고정했다. 확인군은 계속 닫혀 있다. Stage 8·9 분기, R1/R2 중단의 정본은 `CE_BRAIN_STAGE8_9_분기게이트_감사.md`, `CE_BRAIN_STAGE9_DA_R1_DAY01_장치중단.md`, `CE_BRAIN_STAGE9_DA_R2_날짜스키마_결과.md`다.

## 23. Stage 9 dopamine 학습게이트 개발 실행

`60sD`·`600sD` D-cohort에서 행동 event와 dLight1.3b photometry의 동시 스키마를 확인했다. development 7 animals·day01~08·57 assets를 공식 SHA-256으로 잠갔다. R4의 단일 lick port 정의는 실제 배선과 맞지 않아 score 전 중단했고, 모든 lick onset code `{1,3,5}`를 합치는 R5 새 계약을 봉인했다.

R5에서 cue-dopamine 계수는 7개 leave-one-animal-out fold 모두 양수였다. 그러나 dopamine 추가 모델 C의 held-out RMSE는 1.478995로, 행동·ITI·day 기준 B 1.309323, persistence P 1.371303, 3일 shift dopamine S 1.359605보다 모두 나빴다. C의 상대 개선은 각각 -12.96%, -7.85%, -8.78%였고 모든 bootstrap 구간이 0을 포함했다.

**[판정]** `DOPAMINE_UPDATE_SIGNAL_NOT_ESTABLISHED`.

**[해석]** 평균 방향성은 양수였지만, current behavior와 reward interval을 넘어 next-day 행동을 새 동물에서 추가 예측하는 chemical update signal은 확립되지 않았다. 논문의 집단 평균 dopaminergic learning을 반증하는 결과가 아니라 더 강한 개체 외삽 질문의 실패다.

**[현재 지위]** calibration 2 animals와 confirmation 4 animals은 미개봉 유지한다. 인과 chemical gate는 미허가다. R4 장치중단과 R5 결과는 `CE_BRAIN_STAGE9_DA_R4_lick채널_장치중단.md`, `CE_BRAIN_STAGE9_DA_R5_학습게이트_결과.md`가 정본이다.

## 24. Stage 10 통합 경쟁 게이트

Stage 3·6·7·9는 서로 다른 종·회로·과제·endpoint에서 수행됐다. 이를 합쳐 R/SR/MM/F/G/O의 공정한 동일자료 경쟁 점수로 사용할 수 없다. R·F·G·O는 각 해당 개발/교란 게이트에서 생존하지 못했고, SR은 개체축만 남았으며 MM은 patch 생존자 부재로 식별되지 않는다.

**[판정]** `STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE`.

**[금지]** 단계별 부분 신호를 이어 하나의 뇌 기하·기억·화학 이론이 증명됐다고 주장하지 않는다. 동일 자료계에서 state/intervention, history dynamics, behavior/memory update, 가능하면 neuromodulator를 함께 측정하고 animal/intervention holdout을 갖춘 새 계약이 필요하다. 상세 감사는 `CE_BRAIN_STAGE10_통합경쟁_게이트감사.md`가 정본이다.

## 25. 전체 로드맵 범위 재정렬

두 첨부문서를 전수 대조해 매뉴얼 Stage 10 뒤에도 긴 로드맵의 Phase 9 기억용량, Phase 10 회상·교정, Phase 11 화학, Phase 12 통합, Phase 13 독립재현, Phase 14 인간 검증이 남아 있음을 정본 범위에 복구했다. 번호 충돌 때문에 로드맵 Phase 9 기억용량과 매뉴얼 Stage 9 화학 gate를 앞으로 반드시 이름과 함께 표기한다.

**[판정]** 전체 목표는 명확하지만 아직 완료되지 않았다. 현재 가장 이른 직접 하위 목표는 trajectory memory 미확립 뒤의 `다른 memory code 탐색`이다. 단계별 완료조건은 `CE_BRAIN_전체가설_완료조건_감사.md`가 정본이다.

## 26. DANDI 001701 X-미로 행동 장치

두 development NWB에는 trial table·task event·reward가 없지만 위치와 spike table은 있다. 고정 위치 규칙으로 BaggySweatpants에서 east→west 102회·west→east 103회, Franklin에서 각각 101회·101회의 cross-maze transition을 복원했다. 네 endpoint 방문수와 위치 유효률도 사전 장치 문턱을 통과했다.

**[장치 판정]** `STAGE7_XMAZE_BEHAVIOR_APPARATUS_ELIGIBLE`.

**[한계]** sample/rule/correct/reward 의미는 복원되지 않는다. 공식 exporter가 X Maze trial을 쓰지 않는 구현과 일치하며, DANDI 218개 asset과 공식 GitHub tree에는 별도 원시 trial log가 없다. 상세 감사와 계약은 `CE_BRAIN_STAGE7_DANDI001701_X미로_장치감사.md`, `CE_BRAIN_STAGE7_X미로_다른기억코드_장치계약.md`다.

## 27. X-미로 다른 기억코드 탐색 결과

행동 기준선 B, 정적 신경모델 S, 시간 신경모델 T를 시간순 holdout에서 비교했다. T의 B 대비 log-loss 개선은 Baggy 2.80%, Franklin 3.81%였으나 두 bootstrap 95% 구간이 0을 포함했고 사전 5% 문턱에도 못 미쳤다. S도 안정적인 추가 이득을 보이지 않았다.

계약에는 전체 transition 기준 split을 적었지만 head-direction 결측 feature 창 제외로 실제 event가 Baggy 102→87, Franklin 101→92로 줄었다. 이 불일치는 신경 결과 확인 뒤 발견됐으므로 확인적 음성으로 세지 않는다.

**[판정]** `APPARATUS_CONTRACT_MISMATCH_EXPLORATORY`. 다른 memory code는 확립되지 않았고 부재도 증명되지 않았다.

**[다음 최소 증명 의무]** 원시 task log 또는 명시적 trial semantics가 있는 새 자료에서 결측 처리와 event 문턱을 먼저 고정해 재검증한다. 상세 결과는 `CE_BRAIN_STAGE7_X미로_선택코드_R1_결과.md`가 정본이다.

## 28. 인간 기억 관계복원 개발 실행

DANDI `000004@0.220126.1852`의 한 인간 development session에서 학습 100·인식 100 trials과 exact-image old 50쌍을 확인했다. NWB 설명의 old/new 숫자는 embedded image identity와 반대였으므로 pixel SHA-256 동일성으로 의미를 고정했다. remembered 40·forgotten 10쌍, 유효 unit 14개로 계약을 실행했다.

동일항목 cosine의 category-shuffle 대비 이득은 0.00930(`p=0.3485`), encoding–recognition 관계거리 상관은 0.06376(`p=0.2935`)였다. confidence 상관은 -0.17789였고, remembered–forgotten 차이는 -0.07684로 95% CI가 0을 포함했다. 시간순서 대조도 CI 하한이 음수였다.

**[판정]** `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED`.

**[해석]** 한 사람 amygdala 계열 development 결과에서 관계형 retrieval을 확립하지 못했다. Phase 8·14 확인으로 승격하지 않으며, 동물 Stage 7 실패를 구제하지 않는다. 상세 장치·계약·결과는 `CE_BRAIN_HUMAN_MEMORY_DANDI000004_장치감사.md`, `CE_BRAIN_HUMAN_MEMORY_R1_관계복원_계약.md`, `CE_BRAIN_HUMAN_MEMORY_R1_관계복원_결과.md`가 정본이다.

## 29. 인간 기억 관계복원 독립 development 복제

DANDI 000004의 59 subjects를 outcome-blind hash로 development 35, calibration 14, confirmation 9에 나눴고, 이미 열린 P19는 별도 development로 고정했다. 다음 unopened development subject P16HMH의 완전 200-trial object를 고정해 같은 분석기를 변경 없이 적용했다.

P16의 동일항목 이득은 0.02321(`p=0.1704`), 관계거리 상관은 -0.02231(`p=0.1332`)로 주 문턱을 실패했다. remembered–forgotten 차이는 0.10164, 95% CI [0.01784, 0.18212]로 부분 통과했지만 confidence permutation `p=0.0888`, 시간순서 CI 하한 음수였다.

**[판정]** `HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED_REPLICATED`.

**[게이트]** P19와 P16 모두 주 문턱 미통과이므로 calibration·confirmation을 열지 않는다. 분할 계약은 `CE_BRAIN_HUMAN_MEMORY_독립개체_분할계약.md`, 수치 정본은 `CE_BRAIN_HUMAN_MEMORY_R1_관계복원_결과.md`다.

## 30. 인간 기억 양성대조와 공식방법 진단

outcome-blind development enrollment에서 13 subjects·251 유효 units를 고정했다. 사전등록 category-permutation 양성대조는 memory-selective 12/251(4.78%)로 7% 문턱과 cohort null 95 percentile 16개를 모두 실패했다.

**[사전등록 판정]** `MEMORY_APPARATUS_SENSITIVITY_NOT_ESTABLISHED`.

결과 공개 뒤 공식 OSF MATLAB code를 감사했다. 공식 구현은 0.2–1.7초, correct trials, centered bootstrap을 사용했다. 이를 outcome-known 진단으로 같은 cohort에 옮기자 23/263(8.75%)가 선택세포였고 논문 전체 146/1,863(7.84%)를 재현했다.

**[진단 판정]** `OUTCOME_KNOWN_OFFICIAL_METHOD_DIAGNOSTIC_REPRODUCED`.

**[해석]** 자료에 알려진 old/new 기억신호는 존재한다. 그러나 사전등록 관계표현의 시간창·대조는 그 신호 감도를 보장하지 못했다. 기존 P19/P16에서 창을 바꾸지 않고, 새 development subjects에 공식 창과 correct-trial 조건을 넣은 관계복원 R2를 사전등록해야 한다. calibration·confirmation은 계속 봉인한다. 정본은 `CE_BRAIN_HUMAN_MEMORY_양성대조_R1_계약.md`, `CE_BRAIN_HUMAN_MEMORY_양성대조_R1_결과.md`다.

## 31. 인간 기억 공식창 관계복원 R2

관계 endpoint 미개봉 development subjects P11HMH·P48CS에 공식 old/new 신호 창 `+0.2~+1.7초`, correct-old 조건, 여섯 시간 bin을 사전 고정해 적용했다.

P11의 matched 이득은 0.00718, 관계거리 rho 0.09731이었고 P48은 -0.01224, rho 0.02448이었다. 두 subject 모두 confidence p가 0.01을 넘었고 correct–incorrect 및 시간순서 CI가 0을 포함했다.

**[판정]** `HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED_REPLICATED`.

**[STOP]** R1 두 subjects와 R2 두 subjects, 두 시간표현 family에서 exact-item 관계복원이 생존하지 않았다. 같은 DANDI 000004 development 자료에서 창·거리·문턱을 더 조정해 구제하지 않는다. calibration·confirmation은 봉인 유지한다.

**[계보]** 알려진 old/new 기억신호는 존재하지만 CE 관계복원은 미확립이다. Phase 8은 닫고 recurrent capacity·correction으로 승격하지 않는다. 정본은 `CE_BRAIN_HUMAN_MEMORY_R2_공식창_관계복원_계약.md`, `CE_BRAIN_HUMAN_MEMORY_R2_공식창_관계복원_결과.md`다.

## 32. ACh 및 chemistry 직접 write-gate 장치 감사

DANDI `001176@0.260610.2204`의 두 대표 NWB를 공식 SHA-256으로 잠가 검사했다. ACh sensor 단독 파일에는 pupil·eye·treadmill이 있었고, 결합 파일에는 cholinergic axon GCaMP와 ACh sensor 및 행동상태가 동시에 있었다. 그러나 ephys, trial/intervention, 이후 지속 update endpoint는 없었다.

**[001176 판정]** `ACH_FAST_DYNAMICS_PRESENT_WRITE_GATE_NOT_IDENTIFIABLE`.

후보 범위를 DANDI 001950·001955·001084·000298·001434로 넓혔다. 001950의 9개 원격 Zarr `.zmetadata`를 직접 검사한 결과 unit-bearing 5개와 FIP-bearing 3개는 서로 다른 asset이었다. 001955는 ephys 34개와 photometry 32개가 있지만 공동 asset과 subject overlap이 모두 0이었다. 001084는 광학 dopamine 자료만 있고, 직접 질문에 가까운 000298·001434는 각각 buggy 1 asset과 빈 invalid draft였다.

**[후보군 판정]** `CHEMICAL_WRITE_GATE_NOT_IDENTIFIABLE_IN_AUDITED_CANDIDATES`.

**[해석]** 화학적 write gate의 생물학적 실패가 아니라 현재 공개 후보의 식별성 한계다. 서로 다른 개체·과제의 빠른 화학 dynamics, 전기활동, 장기행동을 사후 결합해 직접 증거로 승격하지 않는다. 정본은 `CE_BRAIN_STAGE9_ACH_DANDI001176_직접게이트_장치감사.md`, `CE_BRAIN_STAGE9_CHEMISTRY_후보데이터_게이트감사.md`다.

## 33. DANDI 001371 빠른 correction code R1

관계거리와 다른 representation family로 DANDI 001371의 Y-maze update task를 열었다. 7 subjects를 outcome-blind SHA-256로 development S34·S29·S20·S25, calibration S17, confirmation S33·S28로 분할했다. trial·unit만 본 장치 감사에서 S34-220623과 S25-210916이 switch≥30, stay≥10, CA1/PFC 각각 20 units 이상을 통과했다.

delay-only correct trial의 firing-rate 목표축을 시간순 train/test로 고정하고, 새 단서 전후 목표축 이동의 switch-minus-stay DID를 검사했다. S34 PFC는 choice BA 0.5597(`p=0.2199`), DID -0.2326(`p=0.6662`)였다. S25 PFC는 DID 0.8533(`p=0.0009995`)의 부분 신호가 있었지만 choice-axis `p=0.1489`였고 bootstrap 95% CI [-0.1233, 1.7711]로 0을 포함했다. CA1도 두 세션 모두 전체 문턱을 통과하지 못했다.

**[판정]** `RAPID_CORRECTION_CODE_NOT_ESTABLISHED_REPLICATED`.

**[해석]** prospective code 일반이나 빠른 선택수정의 부재를 증명하지 않는다. 사전등록한 단순 목표축의 held-out 감도가 두 세션에서 확보되지 않아 correction 주장을 식별하지 못했다. within-trial 결과이므로 장기 `v_C`·지속 geometry 변화·READ/WRITE 분리는 원래부터 claim ceiling 밖이다. 정본은 `CE_BRAIN_STAGE8_DANDI001371_업데이트과제_장치감사.md`, `CE_BRAIN_STAGE8_DANDI001371_빠른교정_R1_계약.md`, `CE_BRAIN_STAGE8_DANDI001371_빠른교정_R1_결과.md`다.

## 34. DANDI 001371 공식-family Poisson correction R2

미개봉 development subjects에서 S29-211118(298 trials, CA1 90/PFC 52)과 S20-210519(136 trials, CA1 72/PFC 30)을 고정했다. 공식 코드 계열의 `choice_binarized`, 선택별 Poisson rate, uniform prior, 0.2초 해독으로 R2를 실행했다.

S29 PFC는 choice BA 0.5900(`p=0.10745`)로 양성대조를 실패했으나 DID 4.1785, `p=0.007996`, CI [1.3325, 7.1666]의 부분 신호가 있었다. S20 PFC는 raw BA 0.9000이었지만 permutation `p=0.06047`, DID 7.4340의 permutation `p=0.24338`로 실패했다. S20 CA1은 choice 양성대조를 통과했지만 DID permutation `p=0.01649`로 사전 문턱을 넘지 못했다.

**[판정]** `RAPID_CORRECTION_POISSON_CODE_NOT_ESTABLISHED_REPLICATED`.

**[STOP]** R1 두 subjects와 R2 두 새 subjects에서 PFC 복제 사슬이 생존하지 않았다. 동일 DANDI development 자료에서 창·prior·bin을 더 조정하지 않는다. 장기 `v_C`와 READ/WRITE 분리는 미검사 상태다. 정본은 `CE_BRAIN_STAGE8_DANDI001371_R2_세션선정_감사.md`, `CE_BRAIN_STAGE8_DANDI001371_공식선택해독_R2_계약.md`, `CE_BRAIN_STAGE8_DANDI001371_공식선택해독_R2_결과.md`다.

## 35. 현재 development 정지선

국소기하, recurrence 고유이득, trajectory·관계·빠른 correction memory code, next-day dopamine update는 각 계약에서 생존하지 않았다. local→global, 기억용량, 지속 `v_C`, 직접 chemical write gate, 통합모델은 필요한 관측축 또는 선행 생존자가 없어 식별할 수 없다.

**[운영 판정]** `DEVELOPMENT_BRANCHES_EXHAUSTED_EXTERNAL_EVIDENCE_REQUIRED`.

이는 전체 연구 완료나 모든 생물학적 가설의 기각이 아니다. 현재 자료에서 confirmation 개방·사후 문턱 조정·서로 다른 과제의 사후 통합 없이 실행 가능한 분기를 소진했다는 뜻이다. 정확한 새 자료 요건은 `CE_BRAIN_현재정지선_및_재개조건.md`가 정본이다.

## 36. 체계적 chemistry 재탐색과 DANDI 000559 인과지속성

DANDI 000251은 sensor와 single-unit를 함께 수록하지만 subject/session 계보가 분리되어 직접
화학×전기 gate가 아니다. DANDI 000559는 ephys가 없지만 폐루프 dopamine axon 광자극 뒤
무자극 post 행동을 제공하므로 더 약한 `chemical intervention → persistent behavior update`
하위분기를 사전등록했다.

cohort와 처치가 섞인 전체 표본을 쓰지 않고 양 군이 함께 있는 cohort 0·3·5의 chr2 8동물,
ctrl 6동물만 사용했다. 결과는 post 3·4 효과 `+0.0292049`, exact `p=0.133333`; session 4
효과 `+0.0246765`, `p=0.251111`이었다. leave-one-animal-out 방향은 모두 양수였지만 AND
문턱의 exact p를 통과하지 못했다.

**[판정]** `DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED`.

**[목표 정렬]** 이는 도파민 효과 부재도, 직접 chemistry×electrical gate의 실패도 아니다.
현재 endpoint family에서 약한 지속 행동 하위증거가 확립되지 않았다는 판정이며 Stage 10은
계속 미허가다. 정본은 `CE_BRAIN_STAGE9_DA_R6_인과지속성_계약.md`와
`CE_BRAIN_STAGE9_DA_R6_인과지속성_결과.md`다.

## 37. Stage 3E Borealis VSD 미개입원 공간경쟁

DANDI 001612는 실제 photostimulation 세션에도 target/timing 표가 없어 장치 중단됐다. 후속
검색에서 Borealis `10.5683/SP2/CCHOVV`의 20-source×20-receiver, 2-repeat VSD 예제는
다중-source 장치 게이트를 통과했다. 12 development source만 열어 source-held-out 경쟁을
실행했고 calibration 4·confirmation 4 source는 봉인했다.

반복상관은 `0.767629`였지만 Euclidean 개선 `+1.1736%, p=0.402832`, directed quadratic
`-12.1727%, p=0.809814`, general kernel `-1.6697%, p=0.703125`였다.

**[판정]** `VSD_SOURCE_GENERALIZATION_NOT_ESTABLISHED`.

**[해석]** 안정적으로 반복되는 연결행렬과 unseen intervention을 예측하는 고정 공간법칙은
다르다. 현 세 family는 새 source 일반화를 확립하지 못했으며, calibration/confirmation 개방과
같은 development 결과에 대한 사후 모델 추가는 금지한다.

## 38. Stage 3F CNIR opto-fMRI 장치 재개

새 독립 자료 `10.5281/zenodo.15718273`의 22 GB EGG를 outcome-blind 원격 목차로 감사했다.
Thy1 12마리와 VGAT 12마리 모두에 여섯 cortical source와 whole-brain 120초 fMRI가 있고,
Thy1은 source당 5회, VGAT은 최소 7회에서 최대 10회 반복을 갖는다.

**[장치 판정]** `STAGE3_OPTOFMRI_APPARATUS_ELIGIBLE`.

이는 35절의 외부증거 재개조건 가운데 다중-source·반복·held-out animal 축을 충족해 Stage 3
분기를 다시 연다. 아직 원시 EPI의 atlas registration과 분석 계약이 잠기지 않았고 영상값도
열지 않았으므로 과학 판정은 없다. 저자별 warp가 공개되지 않은 상태에서 raw voxel을 Allen
거리로 간주하지 않는다. 정본은 `CE_BRAIN_STAGE3F_OPTOFMRI_장치감사.md`다.

## 39. Stage 3F R1 native-grid 상태 관계기하

결과 비열람 상태에서 development 6+6동물, source당 첫 5 trial, 40초 고정 반응창과
odd/even 반복 분할을 봉인했다. Thy1 반복성은 median `0.38036`, `p=0.03125`로 통과했지만
VGAT 반복성은 `0.06786`, `p=0.328125`로 실패했다. 개체 LOO median은 Thy1 `0.11607`,
VGAT `0.15714`로 두 조건 모두 효과크기 문턱 0.30을 넘지 못했다.

cross-condition median은 `-0.18929`였다. within-minus-cross 차이 `0.34851`과 permutation
`p=0.010823`은 크지만, 두 조건 내부의 선행 안정성 AND 게이트가 실패했으므로 switching
geometry로 승격하지 않는다.

**[판정]** `STATE_RELATION_GEOMETRY_NOT_ESTABLISHED`.

**[STOP]** 이 native-grid 40초 RDM family는 development에서 중단한다. 같은 값에 맞춰
창·mask·trial 수를 바꾸거나 calibration/confirmation을 열지 않는다. 물리기하 질문은
저자 atlas warp 또는 독립적으로 고정한 registration이 있어야 별도 계약으로 재개할 수 있다.

## 40. Stage 3G–3I atlas 등록과 고정 후보 경쟁

저자 공개 template·atlas·stimulus label을 해시로 고정하고 개발 12마리 anatomy/EPI 등록 게이트를 통과했다. 이로써 물리좌표를 쓰기 위한 장치 선행조건은 해결됐다.

같은 개발자료에서 여섯 source 직선거리, 저자 계열 voxelwise connectome의 고정 방향성 1–3차 전파 profile, 위치별 60초 순서를 보존한 최소 `K(j,t|i)`를 순서대로 사전계약했다. 직선거리와 40초 평균 반응은 Thy1·VGAT 모두 실패했고, 잠근 Thy1 1차·VGAT 3차 구조 후보도 실패했다.

시간정보는 Thy1 반복성을 중앙값 `0.343`, `p=0.015625`로 회복했지만 VGAT은 `-0.052`, `p=0.359375`였다. Thy1의 반복되는 시공간 RDM도 고정 구조와 중앙 rho `0.048`, `p=0.6875`, source 순열 `p=0.6667`로 미통과했다.

**[판정]** `SPATIOTEMPORAL_STRUCTURAL_RELATION_NOT_ESTABLISHED`.

**[STOP]** calibration·confirmation은 봉인한다. 여섯 source 결과를 국소 quadraticity 반증으로 과장하지 않는다. 현재 등록 원자료에서 창·거리·차수를 더 맞추지 않고, 저자 수준 slice timing·motion correction·GLM 재현 또는 독립된 촘촘한 국소 perturbation 자료가 있어야 재개한다.
