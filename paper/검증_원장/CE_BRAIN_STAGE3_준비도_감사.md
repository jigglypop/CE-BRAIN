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

## 후속 자산과 실제 실행

공식 논문이 OSF `E2SYT`에 공개한 WT·`unc-31` 처리자료는 DANDI 변환본보다 source label을 더 직접적으로 보존한다. endpoint-blind 감사에서 WT 잠재 간선 210,355개, `unc-31` 잠재 간선 36,264개, `unc-31` 3개체 이상 반복 directed pair 2,959개와 잠재 triad 72,640개를 확인했다. 따라서 다중 source 장치 게이트는 이 자산에서 통과했다.

Stage 3B는 WT로 적합하고 `unc-31`으로 확인하는 교란 외삽을 봉인 실행했다. 실제 확인 36,201간선과 50,000 triad를 확보했지만 판정은 `CROSS_GENOTYPE_REPRESENTATION_TENSION`이었다. 따라서 과거의 “장치 부족”은 해결됐으나 고정 기하 후보의 과학 게이트는 통과하지 못했다.

## 후속 자산 탐색

공식 DANDI `001612@0.250927.1801`은 ALM calcium imaging과 targeted optogenetic stimulation을 포함한다. 연결 논문은 2-photon photostimulation으로 2천만 개가 넘는 흥분성 뉴런 쌍을 지도화하고, 표적 뉴런별 반복 trial 반응을 보고하므로 다중 source Stage 3의 강한 후보이다.

가장 작은 `sub-462451_ses-1` 자산을 SHA-256 `fed58ebe1a90659ad89ccc86e03806fd6d301dbe850e1d845806bff249d19af4`로 검증해 schema를 열었으나 이 행동 세션의 `stimulus/presentation`은 비어 있었다. 따라서 dandiset 수준의 설명만으로 분석 준비 완료라 하지 않는다. photostimulation 세션과 target ID·trial timing·receiver ROI를 잇는 실제 NWB 경로를 추가 식별하는 것이 다음 장치 의무다.

## photostimulation 세션 직접 재감사

공식 Figure 3 코드가 `spont_photo` 예제로 지정한 subject `486668`, session `3`의 DANDI
asset `e8dd0c75-a628-4bcc-9375-094ffa4d4306`을 추가로 열었다. 파일 크기는 782,731,036
bytes, 검증 SHA-256은 `cf572a5aade40e69a0b17f7c959a0c51acec0d87daa6c74c0c8d64ebd4530e64`다.

- 4개 fluorescence plane, 총 1,842 receiver ROI, plane당 52,600 frame이 있다.
- `experiment_description`에는 targeted optogenetic stimulation이라고 쓰여 있다.
- 그러나 `stimulus/presentation`과 `stimulus/templates`는 비어 있다.
- `intervals`/trial/epoch table이 없고, 전체 HDF5 path에 explicit `target` 또는
  `photostim` ID가 없다.
- 공식 Figure 3 MATLAB은 target group과 epoch를 NWB가 아니라 `EXP2.SessionEpoch`,
  `IMG.PhotostimGroupROI` 등 별도 DataJoint relation에서 `fetch`한다. 공개 GitHub에는 그
  table export가 없다.

**[후속 장치 판정]** `STAGE3_DANDI001612_TARGET_TIMING_NOT_IDENTIFIABLE`.

이 결과는 photostimulation 실험이 수행되지 않았다는 뜻이 아니다. 공개 NWB에는 receiver
activity는 있지만 `어느 source를 언제 자극했는가`를 복원할 키가 없으므로, source-held-out
예측과 pair/triad metric 경쟁을 재현할 수 없다는 뜻이다. 공식 DataJoint target·epoch export가
공개되거나 NWB에 대응표가 보강되면 재개한다. 검사 코드는
`examples/brain/ce_brain_stage3d_dandi001612_apparatus.py`다.

## Borealis VSD 다중-source 대체자료

Borealis `10.5683/SP2/CCHOVV` version 1.2의 공개 ZIP은 20개 양측 피질 source, 20개
receiver ROI, source당 2회 자극 TIFF, 두 source마다 짝지은 2회 no-stim TIFF, ROI 좌표와
공식 MATLAB 코드를 포함했다. 따라서 DANDI 001612에 없던 source label·timing·receiver
대응이 실제로 존재하며 Stage 3 다중-source 장치 게이트를 통과했다.

결과를 열기 전에 12 development / 4 calibration / 4 confirmation source를 SHA-256으로
봉인하고, development leave-one-source-out에서 receiver mean, isotropic Euclidean,
directed quadratic, general source kernel을 경쟁시켰다. 반복 간 off-diagonal 상관은
`0.767629`였지만 평균 개선과 exact p는 각각 Euclidean `+0.011736, p=0.402832`, directed
`-0.121727, p=0.809814`, kernel `-0.016697, p=0.703125`였다.

**[과학 판정]** `VSD_SOURCE_GENERALIZATION_NOT_ESTABLISHED`.

이 자료는 기존 worm 교란 외삽과 다른 종·측정계에서도 `고정 공간규칙이 unseen source로
일반화된다`는 강한 주장을 지지하지 못했다. 신호 반복성은 양호했으므로 순수 장치 무감도만으로
실패를 설명하기 어렵다. 다만 한 예제 동물의 mesoscale 결과이므로 calibration·confirmation을
열거나 Riemannian 부재로 승격하지 않는다. 정본은
`CE_BRAIN_STAGE3E_VSD_미개입원_공간경쟁_계약.md`와 결과 문서다.

## CNIR opto-fMRI 다중-source 독립 계보

Zenodo `10.5281/zenodo.15718273`의 `Opto-fMRI.Egg`를 영상 결과 비열람 상태에서 원격
byte-range 감사했다. `Thy1-ChR2` 12마리와 `VGAT-ChR2` 12마리 모두에 MOp, MOs,
SSp-bfd, VISp, RSP, VISarl 여섯 자극점이 있고, Thy1은 자극점당 5회, VGAT은 최소
7회에서 최대 10회 반복 whole-brain fMRI를 갖는다. 대표 헤더는 모두 120초, TR 1초였다.

**[장치 판정]** `STAGE3_OPTOFMRI_APPARATUS_ELIGIBLE`.

따라서 기존 VSD 한 예제 동물의 한계를 넘어 source·개체·활성/억제 조건 일반화를 시험할
독립 장치는 생겼다. 다만 공개 원시 EPI에 저자별 atlas warp가 포함되지 않았으므로,
등록 계약을 고정하기 전에는 voxel 좌표를 Allen 기하로 해석하지 않는다. 세부 정본은
`CE_BRAIN_STAGE3F_OPTOFMRI_장치감사.md`다.

### Stage 3F R1 native-grid 상태 관계도 결과

장치 통과 뒤 결과를 열기 전에 각 유전자형 development 6동물, source당 첫 5 trial,
baseline 40초와 response 40초, odd/even split을 봉인했다. Thy1 반복 관계도는 median
`0.38036`, `p=0.03125`로 통과했지만 VGAT은 `0.06786`, `p=0.328125`로 실패했다.
개체 holdout median은 Thy1 `0.11607`, VGAT `0.15714`로 두 조건 모두 사전 문턱 0.30을
넘지 못했다. cross-condition median은 `-0.18929`였다.

**[과학 판정]** `STATE_RELATION_GEOMETRY_NOT_ESTABLISHED`.

within-minus-cross 차이 `0.34851`, permutation `p=0.010823`은 부차적으로 크지만, 두 조건
내부 안정성이라는 선행 AND 게이트가 실패했으므로 switching geometry로 승격하지 않는다.
calibration·confirmation 동물은 봉인 유지한다. 정본은 Stage 3F R1 계약과 결과 문서다.

## Stage 3G–3I 등록·거리·구조·시간 후속

저자 공개 T2 template·atlas·자극 label과 개발 12마리의 T2/EPI를 outcome과 무관한 게이트로 등록했다. 표본 atlas 정합과 개발 anatomy/EPI 게이트는 모두 통과했으며, Thy1-sub06은 사전 허용한 rigid fallback으로 통과했다. 따라서 이전의 atlas-registration 장치 중단은 해소됐다.

등록 뒤 여섯 source의 물리 직선거리와 40초 평균 반응 RDM을 비교했으나 Thy1 rho 중앙값 `0.182`, VGAT `-0.050`으로 미통과했다. 저자 계열 15,314-parcel 방향성 connectome으로 outcome-blind 1–3차 전파 profile을 재현하고 Thy1 1차·VGAT 3차를 미리 잠갔지만 평균 반응과의 관계도 Thy1 `0.080`, VGAT `-0.014`로 실패했다.

시간 평균 손실을 검사한 Stage 3I에서 60초 시공간 관계의 반복성은 Thy1 중앙값 `0.343`, `p=0.015625`로 통과했으나 VGAT은 `-0.052`, `p=0.359375`로 실패했다. 반복된 Thy1 시간관계도 고정 1차 구조와 rho 중앙값 `0.048`, sign-flip `p=0.6875`, source 순열 `p=0.6667`로 맞지 않았다.

**[현재 과학 판정]** `SPATIOTEMPORAL_STRUCTURAL_RELATION_NOT_ESTABLISHED`.

이는 국소 미분기하의 직접 기각이 아니다. 여섯 source는 한 점 주변의 작은 다방향 perturbation을 제공하지 않아 local quadraticity를 식별할 수 없다. 현재 직접 실패한 것은 6-source 규모의 직선거리, 개체공통 고정 구조 profile, 그리고 그 구조와 최소 시공간 커널의 관계다. 다음 후보는 논문급 전처리 재현 뒤의 개체·상태·입력·history 조건부 연산자다.
