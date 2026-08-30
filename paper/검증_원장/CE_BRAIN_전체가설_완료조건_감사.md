# CE-BRAIN 전체 가설·완료조건 감사

Status: `FULL_SCOPE_REALIGNED / NOT_COMPLETE`

기준일: 2026-08-31

## 1. 이 문서가 바로잡는 범위

이 감사의 정본 입력은 사용자가 제공한 두 문서다.

1. 긴 연구 로드맵: Phase 0부터 Phase 14까지의 수렴적 증거 사다리
2. `CE-BRAIN 실험 매뉴얼 v1`: Stage 0부터 Stage 10까지의 후보 제거 실험

두 문서는 번호가 같아도 뜻이 다르다. 특히 **긴 로드맵 Phase 9는 기억 용량**이고, **매뉴얼 Stage 9는 화학적 gate**다. 앞으로 번호만 쓰지 않고 `로드맵 Phase`와 `매뉴얼 Stage`를 함께 표기한다.

최종 목표는 최초의 리만 가설을 끝까지 방어하는 것이 아니다. 국소 전기·상태·입력·history에서 출발해 실제 뇌의 수학적 표현 후보를 제거하고, 살아남은 구조가 기억의 저장·복원·교정을 설명하는 범위를 새 동물과 인간에서 확인하는 것이다.

## 2. 목표 정렬 판정

- **최종 목표 명확성:** 명확하다. 하나의 QED가 아니라 독립 데이터·개입·구조 ground truth에서 경쟁 가설을 탈락시키는 수렴적 증거 묶음이다.
- **현재 하위 목표 명확성:** memory의 trajectory·관계·빠른 correction family와 독립 chemistry 후보 감사까지 끝났으므로, 남은 Phase 12–14의 선행조건과 외부자료 재개조건을 확정하는 것이다.
- **직결성:** 생존한 통합모델이 없는 상태에서 confirmation·인간 검증을 열지 않고 필요한 새 자료축을 특정하는 것은 Phase 12–14의 오류 없는 진입조건에 직접 연결된다.
- **금지된 우회:** 기억 시행 라벨이 없는 자료로 recall/correction·정답·기억용량을 주장하거나, 서로 다른 종과 과제를 한 모델 점수로 합치는 것은 목표에서 벗어난다.
- **현재 전체 지위:** `NOT_COMPLETE`. Phase 4·5, 로드맵 Phase 8–14의 확인적 완료가 남아 있다.

## 3. 전 단계 완료조건 대조표

| 체계 | 질문·완료조건 | 현재 증거 | 지위 | 다음 허용 행동 |
|---|---|---|---|---|
| 로드맵 Phase 0 / 매뉴얼 Stage 0 | 수학적 관측 한계와 합성 구조군 구별 | 기록상 no-go·식별성 정리, synthetic successor 84/84 | **기록 완료** | 실제 뇌 증거로 자동 승격 금지 |
| 매뉴얼 Stage 1 | held-out 입력에서 history가 현재 상태보다 유용 | Allen 단일세포 계보에서 history 후보 지지 | **기록 완료** | 간선·순환·기억 증거와 분리 |
| 로드맵 Phase 1 / Stage 2B | 같은 뇌의 상태별 전달 변화와 recovery 재현 | 543393 실패, 543394 통과 | **혼합** | 상태 하나의 보편 법칙 폐기, 입력·개체 분해 |
| 로드맵 Phase 2 | state × input 상호작용이 새 동물·전류에서 separable보다 우세 | 강한 상호작용 M2가 M1을 이기지 못함; 공통축 실패, 개체축·recovery 복제 | **강한 상호작용 기각, 개체축 제한 지지** | 개체 내부 표현만 사용 |
| 로드맵 Phase 3 / 매뉴얼 Stage 3 | R/F/G/S/O를 held-out source·교란에서 경쟁 | worm WT→unc-31 및 Borealis unseen-source 미통과. CNIR 12동물 등록 뒤 직선거리·고정 구조관계 미통과; 시간 포함 표현은 Thy1 반복성만 회복했으나 구조관계 실패, VGAT 반복 실패 | **고정 공간규칙 반복 미확립 / 국소 quadraticity 직접 미식별** | 저자급 전처리 뒤 조건부 operator 또는 촘촘한 국소 perturbation 자료 필요 |
| 로드맵 Phase 4 / 매뉴얼 Stage 4 | 기능자료 blind 예측 해시 후 MICrONS EM 공개 | 기존 outcome-known 분석은 무효; 적격 blind 실행 없음 | **미실행** | Stage 3 생존 예측자가 새로 생길 때만 실행 |
| 로드맵 Phase 5 / 매뉴얼 Stage 5 | local patch를 single/atlas/stratified/Finsler/operator로 연결 | 생존 local patch 없음 | **식별 불가** | Stage 4·local predictor 전제 필요 |
| 로드맵 Phase 6 / 매뉴얼 Stage 6 | recurrent mode가 비순환 history 이상으로 미래예측을 설명하고 파괴대조에 선택적 민감 | 두 Allen 개발개체에서 history 유용, recurrence 고유 이득은 효과크기 문턱 미달 | **반복 미통과** | 확인군 봉인 유지; 기억용량의 원인으로 연결 금지 |
| 로드맵 Phase 7 / 매뉴얼 Stage 7 encoding | 정확한 encoding 후 기억이 정적 vector보다 trajectory로 복원 | CRCNS hc-3 두 topdir에서 trajectory 대조 미통과; DANDI 001701 선택코드는 event 계약 불일치가 있는 탐색에서 추가 이득 미확립 | **반복 미확립 + 대체코드 탐색 미확립** | 의미가 명시된 trial log가 있는 새 자료 필요 |
| 로드맵 Phase 8 / 매뉴얼 Stage 7 retrieval | recall이 좌표보다 관계·위상·순서·전이를 보존 | 동물 encoding 실패; 인간 R1 2명·공식창 R2 2명에서 관계복원 미통과. 같은 자료의 공식 old/new 신호는 8.75%로 재현 | **관계복원 반복 미확립 / 현재 family STOP** | calibration 봉인; 다른 data/representation family 없이는 구제 금지 |
| 로드맵 Phase 9 기억 용량 | synthetic+real latent에서 `C(N,r)` scaling, interference, error correction | Stage 6 recurrence 미확립; basin write/retrieval outcome 없음 | **미실행/현재 식별 불가** | toy 결과를 생물학적 용량으로 부르지 말 것; 적격 retrieval 자료부터 확보 |
| 로드맵 Phase 10 / 매뉴얼 Stage 8 | recall 방향 `v_R`과 지속 correction `v_C`의 분리 | DANDI 001371 R1 2 subjects와 공식-family R2 2 새 subjects에서 PFC 복제 미확립; 여러 부분 신호는 문턱 사슬 실패 | **빠른 교정 family STOP / 지속 v_C 미실행** | 새 dataset/representation 없이는 구제 금지; within-trial을 지속 write로 승격 금지 |
| 로드맵 Phase 11 / 매뉴얼 Stage 9 | 같은 전기 trajectory라도 neuromodulator 상태에 따라 장기 변화가 달라짐 | DANDI 001632 next-day 추가예측 미확립; 001176은 빠른 ACh만 식별; 000251은 modality cohort 분리; 000559 인과지속성은 14동물에서 exact p=0.133/0.251로 미확립 | **개발 미통과 + 직접 식별 불가** | 확인군 개방 금지; 같은 개체·비교단위의 ephys+화학+지속 update 자료 필요 |
| 로드맵 Phase 12 / 매뉴얼 Stage 10 | 같은 자료에서 살아남은 R/SR/MM/F/G/O 및 전기+화학+history 통합 경쟁 | 단계별 자료의 종·과제·endpoint가 다르고 생존자가 부족 | **식별 불가** | 동일 자료계 통합계약이 선행돼야 함 |
| 로드맵 Phase 13 | freeze된 모델을 새 dataset/animal/participant에서 7개 항목 재검증 | freeze할 통합 모델 없음 | **미실행** | Phase 12 생존 모델 뒤 독립 family 개방 |
| 로드맵 Phase 14 | 새 인간 CCEP·기억자료에서 아래 scale의 예측만 확인 | 기존 human D0–D3는 재사용 불가; DANDI 000004 네 development subjects에서 두 관계표현 family 미통과 | **확인 미실행** | 아래 scale 모델 freeze 후 새 환자/새 dataset 계약 |

## 4. 지금까지 실제로 답한 것

### 답한 질문

- 상태 효과는 동물 공통의 한 축으로 충분하지 않다.
- 새 recovery-bearing 다중전류 동물 내부에서는 개체 고유 상태축과 awake 복귀가 재현됐다.
- 현재 고정 metric·graph·operator 및 조건별 재학습 후보는 held-out 조건에서 의미 있는 예측 이득을 확립하지 못했다.
- 두 Allen 개발개체에서 history는 유용했지만 교차축 recurrence의 고유 이득은 격리되지 않았다.
- 두 CRCNS 개발세션에서 현재 decoder로 trajectory memory를 확립하지 못했다.
- DANDI 001632의 강한 next-day dopamine update 예측은 새 동물로 일반화되지 않았다.

### 아직 답하지 못한 질문

- 기능적 예측자가 실제 MICrONS wiring을 blind하게 맞히는가.
- local patch가 global하게 어떤 공간으로 붙는가.
- 관계형 또는 선택 예측형의 다른 memory code가 신경신호에 존재하는가.
- recall과 correction이 분리되는가.
- recurrent dimension과 복원 가능한 기억 repertoire의 scaling은 무엇인가.
- 전기·화학·history를 같은 개체·과제에서 합치면 무엇이 살아남는가.
- freeze된 통합모델이 새 동물과 인간으로 일반화되는가.

DANDI 001371은 명시적 update trial과 CA1·PFC를 갖춘 좋은 장치였지만, 단순 목표축 R1 두 subjects와 공식-family Poisson R2 두 새 subjects 모두 PFC 복제 사슬을 넘지 못했다. S25·S29의 부분 DID 신호는 보존하되 빠른 correction 확립이나 장기 `v_C`로 승격하지 않는다.

## 5. 가장 이른 다음 증명 의무

다른 memory code로 X-미로 선택예측과 인간 exact-item 관계복원을 실행했지만 생존하지 않았다. 양성대조의 공식방법 진단은 알려진 old/new 기억신호를 논문과 비슷한 8.75%로 재현했지만, 새 두 development subjects의 공식창 관계복원 R2도 미통과했다. 현재 exact-item cosine·거리행렬 family는 STOP이다.

다음 개발 질문은 다음처럼 제한한다.

> 실패한 관계복원을 건너뛰어 기억용량·correction을 주장하지 않으면서, 독립적으로 검증 가능한 화학적 gating의 직접 자료가 있는가?

- DANDI 001176 등 ACh sensor·행동 자료의 schema와 장기변화 endpoint 동시성을 먼저 감사한다.
- 동일 전기 trajectory 조건이 없으면 `전기는 복원, 화학은 쓰기 허가`를 직접 검증할 수 없다고 판정한다.
- dopamine 개발 미통과와 ACh 장치 결과를 합쳐 chemistry를 증명했다고 주장하지 않는다.

후보 감사 결과 001176·001950·001955·001084에는 직접 주장의 네 축이 한 비교 단위에 없었고, 000251은 sensor와 unit subject가 분리되며 더 가까운 000298·001434는 현재 invalid draft였다. 000559의 약한 dopamine 개입→지속행동 분기는 양방향 cohort 14동물에서 별도 실행했으나 exact 문턱을 통과하지 못했다. 따라서 현 공개 후보에서 Phase 11 직접 실행은 중단하며, 이는 생물학적 기각이 아니라 자료 식별성과 현재 endpoint의 미확립 판정이다.

## 6. 운영 체크포인트

모든 후속 실행은 다음 순서로 기록한다.

```text
목표·하위목표 설명
→ 완료/부분/실패/미실행 증거 대조
→ 현재 실험의 목표 직결성 확인
→ 계약·데이터·모델·문턱 봉인
→ development 실행
→ answered/refuted/alive/next 갱신
```

필수 전제가 빠졌거나 목표와 직접 연결되지 않으면 실행을 중단한다. 개발자료 미통과를 confirmation 개방으로 구제하지 않는다.

## 7. 현재 정지선

관계복원과 빠른 correction은 각각 R1/R2의 서로 다른 네 development subjects에서 현재 family STOP에 도달했다. 직접 chemistry 후보 감사도 같은 비교단위의 네 필수축을 가진 자료를 찾지 못했다. Stage 3 생존 predictor와 Phase 12 freeze 모델도 없다.

관계·교정·직접 chemistry 분기의 development 계산은 여전히 소진됐다. 그러나 새 CNIR
opto-fMRI 자료에서 24개체×6 source×반복 whole-brain 장치가 outcome-blind 감사를 통과해
Stage 3만 재개됐다. 현재 허용된 다음 작업은 원시 EPI registration과 분석 계약을 먼저
봉인하는 것이며, 영상 결과를 보고 시간창·좌표·모형을 고르는 것은 허용되지 않는다. 상세
재개조건은 `CE_BRAIN_현재정지선_및_재개조건.md`를 따른다.

Stage 3F 이후 저자 공개 atlas·T2 자산으로 개발 12동물 등록을 고정해 통과시켰다. 등록된
직선거리와 outcome-blind 저자 계열 구조 전파 profile은 40초 반응관계를 설명하지 못했다.
시간 순서를 보존한 최소 `K(j,t|i)`는 Thy1 반복성을 회복했지만 고정 구조관계는 실패했고,
VGAT은 반복성부터 실패했다. 따라서 현재 정지선은 조건부 operator 또는 새 국소자료다.
여섯 source는 한 점 주변의 작은 다방향 변위를 주지 않으므로 triangle/local quadraticity의
직접 판정으로 승격하지 않는다.
