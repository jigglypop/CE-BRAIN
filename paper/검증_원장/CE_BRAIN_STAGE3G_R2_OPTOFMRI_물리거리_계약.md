# CE-BRAIN Stage 3G R2 — opto-fMRI 물리거리–반응관계 계약

## 목표와 이탈 점검

- **목표:** 여섯 피질 자극원의 실제 해부학적 간격이 자극원별 whole-brain 반응 패턴의 차이를 설명하는지 검사한다.
- **가설 사다리상의 위치:** 사용자가 제시한 Stage 3의 `metric representation useful?`에 직접 대응한다.
- **현재 단계가 필요한 이유:** native voxel 배열의 인덱스는 뇌 좌표가 아니므로, 저자 atlas → 개체 T2 → baseline EPI 정합을 통과한 뒤에만 물리거리를 정의할 수 있다.
- **이탈 여부:** 목표에 정렬되어 있다. 다만 여섯 자극점은 작은 국소 perturbation 격자가 아니므로 이 실험을 `local quadraticity`, 리만 계량, 단일 manifold의 증명으로 해석하지 않는다.
- **다음 게이트:** 반복 신뢰도와 고정 Euclidean 거리 후보가 개발군에서 모두 통과할 때만 구조 그래프 후보와의 경쟁으로 진행한다. 실패하면 `물리거리 표현 미확립`으로 기록하되 operator/graph 가설 전체를 기각하지 않는다.

## 데이터와 봉인

- 자료: CNIR `Opto-fMRI.Egg`, DOI `10.5281/zenodo.15718273`.
- 개발군은 기존 SHA-256 순열로 잠근 Thy1 6마리와 VGAT 6마리만 쓴다.
- calibration 3마리/유전자형과 confirmation 3마리/유전자형은 열지 않는다.
- 각 동물·자극점에서 번호가 작은 다섯 trial만 사용한다.
- 자극 후 결과를 보지 않고 잠근 Stage 3G 정합 장치를 그대로 쓴다. T2 정합은 12/12 통과했고, EPI 정합은 affine 우선·사전 기준 실패 시 rigid 1회 정책으로 12/12 통과했다.

## 여섯 자극원

논문 SI가 명시한 왼쪽 반구 자극만 사용한다. 라벨은 저자 `Load_ATLAS_info.m`과 `DMD_pattern_prep.m`에서 고정한다.

| source | 왼쪽 Allen-modified 라벨 묶음 |
|---|---|
| MOp | 2018–2023 |
| MOs | 2024–2029 |
| SSp-bfd | 2051–2057 |
| VISp | 2185–2191 |
| RSP | 2298–2303, 2325–2331, 2332–2338 |
| VISarl | 2346–2352, 2353–2359 |

각 개체의 `atlas_in_T2.nii.gz`에서 라벨 묶음의 물리좌표 무게중심을 구한다. 여섯 중심 사이 15개 Euclidean 거리가 고정 후보 RDM이다. AFNI식 10배 좌표 단위는 모든 거리에 공통이므로 순위 상관에는 영향을 주지 않는다.

## 반응 RDM

Stage 3F R1과 분석 자유도를 맞춘다.

1. trial별 0:40초 평균을 baseline, 40:80초 평균을 response로 둔다.
2. MION-CBV 극성을 맞추기 위해 `-100 × (response-baseline)/baseline`을 쓴다.
3. 등록 atlas의 foreground이면서 개체 baseline이 양수이고 `0.20 × positive-baseline 95백분위수`를 넘는 voxel만 쓴다.
4. trial 1·3·5와 2·4를 각각 평균해 odd/even 자극원 반응 지도를 만든다.
5. 자극원 쌍마다 odd/even 교차 Pearson 상관의 평균을 구하고 `1-correlation`을 반응 RDM으로 둔다.
6. odd RDM과 even RDM의 Spearman 상관을 개체 반복 신뢰도로 둔다.

## 1차 검정과 잠근 문턱

각 개체에서 15개 물리거리와 15개 cross-half 반응거리의 Spearman 상관 `rho`를 구한다. 방향 가설은 `물리적으로 멀수록 반응 패턴도 더 다르다`, 즉 양의 상관이다.

유전자형별로 다음 두 게이트를 모두 요구한다.

- 반복 신뢰도: 개체 중앙값 `>= 0.30` 및 6개체 exact one-sided sign-flip `p <= 0.05`.
- 물리거리 연관: 개체 `rho` 중앙값 `>= 0.30`, exact one-sided sign-flip `p <= 0.05`, 그리고 여섯 source 이름의 720개 완전 순열 음성대조 `p <= 0.05`.

source 순열에서는 같은 순열을 해당 유전자형의 모든 개체 거리 행렬에 적용하고 평균 `rho`가 관측 평균 이상인 비율을 쓴다. identity도 포함하므로 최소 p는 `1/720`이다.

## 판정

- 두 유전자형 모두 통과: `COMMON_PHYSICAL_DISTANCE_CANDIDATE`.
- 한 유전자형만 통과: `CONDITION_LIMITED_PHYSICAL_DISTANCE_CANDIDATE`.
- 둘 다 실패 또는 반복 신뢰도 실패: `PHYSICAL_DISTANCE_GEOMETRY_NOT_ESTABLISHED`.

유전자형 차이는 두 반복 신뢰도 게이트가 모두 통과할 때만 2차적으로 해석한다. 평균 `rho` 차이 절댓값 `>=0.20`과 12개체 genotype-label 완전 순열 양측 `p<=0.05`를 동시에 요구한다.

## 주장 상한

통과해도 허용되는 문장은 “이 24개체 자료의 개발군 12마리, 여섯 개의 떨어진 왼쪽 피질 자극원 척도에서 Euclidean source separation이 반응 패턴 차이와 연관된다”까지다. 국소 이차형식, 리만 다양체, 인과적 전도거리, connectome 최단경로, 기억 기하를 주장하지 않는다.
