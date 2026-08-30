# CE-BRAIN Stage 3F R1 — opto-fMRI 상태별 source 관계기하 계약

## 0. 봉인 시점과 목표 정렬

이 계약은 `Opto-fMRI.Egg`의 파일명·크기와 대표 NIfTI 헤더만 읽고, fMRI voxel 값은
읽기 전에 고정한다.

최종 목표는 국소 전기·조절 상태에서 출발한 전달 관계가 어떤 수학적 구조를 요구하는지
찾는 것이다. 이번 하위목표는 물리적 Riemannian metric을 선언하는 것이 아니라, 여섯 국소
자극이 만드는 **source 사이 반응 관계도**가 반복·개체를 넘어 재현되고 세포형 조건이 바뀔
때 유지되는지 또는 전환되는지 묻는 것이다. 이는 매뉴얼 Stage 3의 분기 D
“상태마다 다른 local metric/관계”에 직접 연결된다.

## 1. 자료 고정

- DOI: `10.5281/zenodo.15718273`
- 파일: `Opto-fMRI.Egg`, 22,042,485,053 bytes
- Zenodo MD5: `84cc656f6efbf7019e2a59acd4ba1cd0`
- source 순서: `MOp, MOs, SSp-bfd, VISp, RSP, VISarl`
- 각 source에서 acquisition 번호를 정수 오름차순으로 정렬한 첫 5 trial만 사용한다.
  두 유전자형의 반복 수를 같게 만들기 위한 outcome-blind 규칙이다.

## 2. 동물 분할

키 `SHA256("10.5281/zenodo.15718273|" + subject)` 오름차순으로 각 유전자형을
development 6 / calibration 3 / confirmation 3으로 나눈다.

### development — 이번 실행에서만 개방

- Thy1: `sub05, sub08, sub09, sub10, sub07, sub06`
- VGAT: `sub07, sub08, sub05, sub02, sub03, sub09`

### calibration — 봉인

- Thy1: `sub01, sub11, sub12`
- VGAT: `sub06, sub12, sub11`

### confirmation — 봉인

- Thy1: `sub02, sub03, sub04`
- VGAT: `sub01, sub04, sub10`

development 미통과를 구제하려고 calibration 또는 confirmation을 열지 않는다.

## 3. 고정 전처리와 반응 벡터

1. 한 trial은 `96 × 48 × 18 × 120`, TR 1초인 float32 NIfTI다.
2. voxel별 baseline은 `t=0..39` 평균이다.
3. 원 CBV-weighted 신호의 극성을 논문과 같이 뒤집어 percent change를 계산한다.
4. 반응 지도는 `t=40..79`의 평균 percent change다. Thy1 10초 자극과 VGAT 20초
   자극을 모두 포함하는 동일한 40초 창이며 결과를 보고 바꾸지 않는다.
5. subject mask는 선택한 30 trial의 baseline 평균이 그 subject baseline 95백분위의
   20%보다 큰 voxel로 고정한다. response 구간은 mask 생성에 쓰지 않는다.
6. slice timing, motion, atlas registration을 사후로 흉내 내지 않는다. 반복 평균과 넓은
   시간창을 쓰되, 따라서 주장 상한은 native-grid 반응패턴 관계까지다.
7. source별 trial 1·3·5는 odd half, 2·4는 even half로 평균한다.

## 4. source 관계도

각 subject에서 여섯 source의 spatial response vector 사이 Pearson 상관을 구한다.

- odd RDM: odd map끼리 `1-r`
- even RDM: even map끼리 `1-r`
- cross-half RDM: `1 - (r(odd_i,even_j)+r(even_i,odd_j))/2`

대각을 뺀 15개 source pair가 한 subject의 관계 벡터다. 절댓값 크기보다 공간 패턴 관계를
묻기 때문에 source map별 별도 사후 thresholding은 하지 않는다.

## 5. 양성대조

각 subject의 odd RDM과 even RDM 15개 값의 Spearman 상관을 repeat reliability로 둔다.

- 두 유전자형 각각 median reliability `>= 0.30`
- 각 유전자형 6동물의 one-sided exact sign-flip `p <= 0.05`

한 유전자형이라도 실패하면 해당 조건의 관계기하를 안정된 측정물로 보지 않고 주 분석을
그 조건에서 `NOT_IDENTIFIABLE`로 제한한다.

## 6. 주 분석

### within-condition 일반화

각 subject를 한 번씩 holdout하고 같은 유전자형의 나머지 5동물 cross-half RDM 평균과
holdout RDM의 Spearman 상관을 계산한다. 유전자형별 6개 점수의 median이 `>=0.30`이고
one-sided exact sign-flip `p<=0.05`면 그 조건의 source 관계도가 개체 일반화를 통과한다.

### cross-condition 전이와 switching

각 subject RDM을 반대 유전자형 6동물 평균 RDM과 비교한 cross-condition 점수를 계산한다.
그 subject의 within-condition LOO 점수와 차이 `D = within - cross`를 만든다.

- **공통 관계 후보:** 양 조건 within 게이트 통과, cross-condition 전체 median `>=0.30`,
  one-sided sign-flip `p<=0.05`.
- **상태 전환 후보:** 양 조건 within 게이트 통과, mean `D>=0.20`, 12동물의 genotype
  label을 6/6으로 나누는 924개 exact permutation에서 `p<=0.05`.
- 둘 다 아니면 `STATE_RELATION_GEOMETRY_NOT_ESTABLISHED`.

공통 후보와 상태 전환 후보가 동시에 수치 문턱을 넘으면 cross-condition 보존을 우선 보고하고,
`D`는 조건 차이의 부차 진단으로만 남긴다.

## 7. 주장 상한과 금지

통과해도 “native-grid source-response 관계도가 개체/조건에 일반화된다” 또는 “조건에 따라
그 관계가 바뀌는 후보가 생겼다”까지만 말한다. 다음은 금지한다.

- Riemannian metric, triangle inequality, local quadraticity 통과 선언
- source 최대반응 위치를 사후 자극 좌표로 사용
- raw voxel을 Allen atlas 거리로 간주
- 기억, 순환차원, 화학 write gate로 승격
- development 결과에 맞춘 시간창·mask·source 제외 변경
