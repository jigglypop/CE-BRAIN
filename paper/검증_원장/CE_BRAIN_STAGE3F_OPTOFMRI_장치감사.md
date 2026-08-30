# CE-BRAIN Stage 3F — CNIR opto-fMRI 다중 자극원 장치 감사

## 질문

이 자료가 원 매뉴얼의 Stage 3 질문, 즉 여러 국소 자극원이 공통 수신 공간에 만드는
반응을 자극원·개체·조건 밖으로 일반화할 수 있는지 시험할 장치를 제공하는가?

이 문서는 영상 신호값을 읽기 전에 파일 구조와 NIfTI 헤더만 확인한 장치 감사다.
공간 반응, 효과크기, 유리한 시간창은 아직 열지 않았다.

## 자료와 고정 식별자

- 자료: `CNIR_Optogenetic and resting-state mouse fMRI`
- DOI: `10.5281/zenodo.15718273`
- 공개 파일: `Opto-fMRI.Egg`
- 크기: `22,042,485,053` bytes
- Zenodo MD5: `84cc656f6efbf7019e2a59acd4ba1cd0`
- 연결 논문: Moon et al., PNAS 2025, DOI `10.1073/pnas.2505294122`

원격 EGG는 전체 영상값을 내려받지 않고 HTTP byte range로 헤더만 읽었다. 감사 코드는
`examples/brain/ce_brain_stage3f_optofmri_apparatus.py`, 결과는
`data/external/ce_brain_stage3_optofmri/apparatus.json`, 원격 추출 위치표는 같은 폴더의
`archive_manifest.json`이다.

## outcome-blind 구조 결과

- EGG 항목 `1,037`개, 암호화 항목 `0`개, 저장 방식은 모두 method `0`(store)다.
- `Thy1-ChR2` 12마리와 `VGAT-ChR2` 12마리가 모두 존재한다.
- 모든 동물에 `MOp`, `MOs`, `SSp-bfd`, `VISp`, `RSP`, `VISarl` 여섯 자극점이 있다.
- Thy1은 모든 동물·자극점에 5회 반복이 있다.
- VGAT은 동물·자극점에 최소 7회, 최대 10회 반복이 있다. 일부 동물에서 자극점별
  반복 수가 한 회 차이 나므로 분석은 최소 공통 반복 수로 맞추거나 반복 평균을 사용해야 한다.
- 모든 동물에 해부 T2 NIfTI가 하나씩 있다.
- 대표 NIfTI 헤더 12개(두 유전자형 × 여섯 자극점)는 모두
  `96 × 48 × 18 × 120`, float32, TR 1 s였다.
- 논문 사전 명세의 한 trial은 baseline 40 s 뒤 Thy1 자극 10 s 또는 VGAT 자극 20 s,
  이어서 rest 70 s 또는 60 s다. 파일의 120 time point와 일치한다.

## 장치 판정

**`STAGE3_OPTOFMRI_APPARATUS_ELIGIBLE`**

기존 단일 MOs DANDI 자료와 달리, 이 자료는 같은 동물 안에 여섯 source와 공통 whole-brain
receiver, source별 반복 trial, 두 개의 상반된 세포형 조건을 동시에 갖는다. 따라서 다음을
분리해 시험할 수 있는 새 독립 계보다.

1. 같은 source의 반복 신뢰도
2. 보지 않은 source로의 전달 규칙 일반화
3. 흥분성 활성화(Thy1)와 억제성 silencing(VGAT) 사이의 조건 전이
4. 동물 holdout 일반화

## 아직 통과하지 않은 분석 게이트

공개 NIfTI는 획득 격자 `0.1667 × 0.1667 × 0.5 mm`에 있고, 논문은 slice timing·motion
correction 뒤 개체 해부영상과 in-house/Allen 좌표 템플릿으로 정규화했다고 명시한다.
하지만 공개 EGG에는 저자별 변환행렬·warp가 없다. 그러므로 지금 당장 voxel 좌표를
Allen 거리로 간주하거나, 반응 최대점을 자극 위치로 역추정해 거리모형을 맞추면 목표가
바뀌고 outcome leakage가 생긴다.

다음 계약은 결과를 열기 전에 다음 둘을 구분해야 한다.

- 원 좌표에서 가능한 반복성·조건 전이 분석
- 독립적으로 잠근 atlas registration을 거친 뒤에만 가능한 Euclidean/graph/ROI 경쟁

이 장치 통과는 국소 기하의 성공 판정이 아니다. 분석 가능성이 생겼다는 뜻만 가진다.

## 주장 상한

현재 허용되는 문장은 “24개체·6자극원·반복 whole-brain opto-fMRI 장치가 확인됐다”까지다.
고정 기하, switching geometry, 구조 연결, 기억 또는 화학적 write gate를 지지한다고 말할 수 없다.
