# CE-BRAIN Stage 3B `unc-31` 교란 외삽 계약

Status: `DRAFT_PRE_CONFIRMATION`

## 목표와 이탈 방지

WT 개체에서 학습한 source→receiver 표현이 신경펩타이드 방출이 억제된 `unc-31` 개체의 직접 광자극 전파에도 일반화되는지 검증한다. 이는 포유류 뇌 기하의 증명이 아니라 C. elegans 회로 교란 외삽이다. Stage 3A의 표본수 부족을 성공으로 바꾸지 않으며, 결과와 무관하게 Stage 4는 자동 허가하지 않는다.

## 자산

- OSF `E2SYT` 최종 WT 처리자료 `exported_data.tar.gz`, SHA-256 `d6e7b3d93175b40b7ae17bde2182835e9c2144388142c522ee9be3832f6ce836`.
- OSF `E2SYT` `unc-31` 처리자료 `exported_data_unc31.tar.gz`, SHA-256 `8b99f6610dbb2d6ab0b8dd6ad15646fe1c120da25dd9bb725f36f530b2af321a`.
- 공식 pumpprobe commit `1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7`의 anatomical position file, SHA-256 `b854b039929185f22dcb2eadce24b08408bfdec80f1a88581fe33edb382ede40`.

신호 열 수와 label 행 수가 다른 세 WT 세션 11·20·23은 사전에 제외한다. `unc-31` 18개체 중 canonical label이 없는 개체는 적격 간선을 만들지 않는다.

## 반응 endpoint

stimulus volume 기준 baseline `[-10,-2]`초, response `[+1.5,+10]`초를 사용하되 다음 stimulus 5초 전에서 자른다. receiver별 baseline·response finite frame이 각각 24·16개 이상이어야 한다. baseline median과 `1.4826×MAD`로 z-score하고, `|z|≥3`이 4 frame 연속이며 peak `|ΔF/F|≥0.10`일 때 반응으로 기록한다. 같은 canonical label의 중복 ROI는 event 안에서 OR로 합친다. source self-response는 요구하지 않는다. 이 규칙은 WT development에서만 장치 점검한 뒤 `unc-31` 값을 열기 전에 봉인한다.

## 표현 경쟁

해부 atlas 좌표를 축별 median/IQR로 정규화한다. 원본 좌표표에서 중복된 `PVCL` 두 행은 정규화 뒤 좌표 중앙값으로 하나로 합친다. WT에서 사전 hash held-out source를 전부 제외하고 N(null), R(symmetric PSD quadratic), F(directional), S(spatial switching), G(directed pair graph), O(RFF coordinate operator)를 Stage 3A와 동일하게 적합한다.

- common-pair: WT에 존재한 non-holdout ordered pair의 `unc-31` log loss.
- unseen-source: WT 적합에서 완전히 제외한 source의 `unc-31` log loss. G는 채점하지 않는다.
- `unc-31` subject cluster bootstrap 1,999회, seed `20260906`.
- 후보 유지: common-pair와 unseen-source에서 동일 후보가 null보다 5% 이상 개선하고 bootstrap 하한 >0이며, 다음 후보보다 3% 이상 개선하고 하한 >0이어야 한다.
- R은 triangle violation 95% 상한 ≤0.10이고 F 대 R 방향성 하한 ≤0일 때만 유지한다.
- 불일치·불충분이면 `CROSS_GENOTYPE_REPRESENTATION_TENSION`.

## 최소 coverage

WT development 50,000행, 전체 `unc-31` 15,000행, common-pair 5,000행, unseen-source 2,000행, `unc-31` 유효 개체 12개 이상을 요구한다. 실패하면 `STAGE3B_APPARATUS_STOP`이며 과학 판정을 내리지 않는다.

## 실행환경

CPython 3.11.9, NumPy 2.4.6, SciPy 1.17.1, h5py 3.16.0을 고정한다. inventory·schema·WT development receipt와 코드·테스트·계약 해시를 manifest에 봉인한 뒤에만 `unc-31` 신호를 연다.
