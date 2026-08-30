# CE-BRAIN Stage 3J R1 — opto-fMRI 움직임보정 시공간커널 계약

## 목표와 이탈 점검

- **목표:** Stage 3I에서 VGAT 시공간 반복성이 실패한 원인이 rigid head motion인지 분리한다.
- **왜 이 단계인가:** 저자 방법은 `3dTshift → 3dvolreg`인데 공개 NIfTI에는 slice timing이 없었다. 순서를 추측하지 않고 재현 가능한 `3dvolreg` 부분만 먼저 고정하면 움직임의 기여를 독립적으로 검사할 수 있다.
- **목표 명확성·이탈 여부:** 명확하고 정렬됨. 이 단계는 새 기하 후보를 맞추는 검사가 아니라 측정 장치 감도 진단이다.
- **다음 게이트:** VGAT 반복성이 회복되면 잠근 구조관계를 다시 검사한다. 회복되지 않으면 같은 자료에서 motion 옵션을 더 고르지 않고 실제 slice acquisition metadata 또는 저자 전처리 산출물을 요구한다.

## 고정 도구

- WSL Ubuntu에서 공식 AFNI `linux_ubuntu_24_64` 바이너리를 사용한다.
- tarball SHA-256: `032e490a285c91331668b97c85e9adc67e5e73367cb5b7507da384e183c228e6`.
- AFNI version: `AFNI_26.2.05`, compile date `Aug 25 2026`.
- 공개 NIfTI의 18개 slice timing 값은 모두 0이고 논문·보충자료에는 취득 순서가 없다. 따라서 `3dTshift`는 실행하지 않는다. 이 제한을 결과에 반드시 남긴다.

## 고정 움직임보정

각 120초 trial에 다음 한 가지 설정만 적용한다.

```text
3dvolreg -Fourier -twopass -zpad 4 -base 39
```

`base 39`는 결과와 무관하게 자극 직전 마지막 baseline volume으로 고정한다. 6개 rigid-body parameter와 volume별 maximum displacement를 기록한다. motion 크기로 trial이나 volume을 제외하지 않는다.

보정 뒤 표현은 Stage 3I와 동일하다.

- baseline: 0–39초 평균
- response trajectory: 40–99초
- MION 부호 반전 percent signal
- trial 1·3·5 대 2·4 odd/even split
- 등록 atlas foreground와 baseline threshold mask
- voxel×time을 펼친 6-source cross-half RDM

## 사전 게이트

유전자형별 반복성 통과 조건은 Stage 3I와 동일하다.

1. odd/even RDM rho 중앙값 `>=0.30`.
2. exact one-sided sign-flip `p<=0.05`.

움직임이 VGAT 실패를 설명했다는 별도 진단 조건은 다음 AND다.

1. motion-corrected VGAT 반복성이 위 문턱을 통과한다.
2. 개체별 `corrected rho - raw rho` 중앙값 `>=0.10`.
3. 그 차이의 exact one-sided sign-flip `p<=0.05`.

이 조건이 통과할 때만 고정 VGAT 3차 구조연산자와의 관계를 재검사한다. Thy1도 동일 처리 결과를 기록하지만, Thy1의 기존 통과를 기준 변경의 근거로 쓰지 않는다.

## 주장 상한

이 검사는 rigid motion이 최소 `K(j,t|i)` 반복성에 미친 영향만 판정한다. slice timing correction, 저자 ICA-derived HRF, `3dDeconvolve` beta map, 국소 quadraticity 또는 인과 전달속도를 재현하거나 증명하지 않는다. calibration·confirmation은 봉인한다.
