# 출처 레인 — 시간축 교정과 원자료 정체성

Status: COMPLETE

Access date: 2026-08-25

| ID | 1차 출처 | 확인한 사실 | 판정과 한계 |
|---|---|---|---|
| SRC-DATA-001 | [OpenNeuro ds006065 v1.0.0](https://openneuro.org/datasets/ds006065/versions/1.0.0), git commit `14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4` | 기존 18-object identity lock SHA-256 `66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`과 공개 판본이 일치한다. TS p17 post `eppost`는 59 blocks, 175 channels, 41,300,000 bytes, annex SHA-256 `3e8619af0faf6533f13c992f7c8dd3986153c8db5faf5672259a4201eaed089a`; PB p17 pre `epcontrolpre`는 60 blocks, 175 channels, 42,000,000 bytes, annex SHA-256 `7119e7701bc789c9ab0e2b6e154cc8aa80803d564e4dd0d0a8e3ec9f836a0600`이다. | 객체 정체성 충돌 없음. 두 파일 모두 BrainVision `IEEE_FLOAT_32`, multiplexed, little-endian, `SamplingInterval=2002.002002 us`이다. |
| SRC-PAPER-001 | Kragel et al., *Nature Communications* 2025, DOI [10.1038/s41467-025-59417-7](https://doi.org/10.1038/s41467-025-59417-7) | 논문은 theta stimulation과 유발반응/연결성 변화를 보고한다. | 본 run은 논문의 생물학 결론을 검증하지 않고 공개 원자료의 제한된 P2P 기술량만 재계산한다. |
| SRC-CODE-001 | [Zenodo 14735080](https://zenodo.org/records/14735080), archive MD5 `6feba89b7c49fd661b39b589e8d9624a` | 공개 MATLAB 분석 코드의 고정 archive이다. | FieldTrip/MATLAB 실행환경 판본은 함께 고정되지 않았다. |
| SRC-CODE-002 | `utils/get_epoched_eeg.m`, SHA-256 `6331f0342cea448c5d4256a3e358a614cbfd3a8c0c0d3c0733ecaf9e641ef97b`, lines 255--266 | 원 경로는 500 Hz로 resample하고 `sr=500`을 반환한다. | 후속 `linspace`와 함께 $t_j=j/499.5-0.5$를 결정한다. |
| SRC-CODE-003 | `preprocessing/run_ep_preproc.m`, SHA-256 `626a7467f803c28302ad712b24b891752b013fc471fec7f0057d529fc7ff0729`, lines 29--69, 85--104, 123--133 | 마지막 sample 제외, DFT 60/120/180 Hz, p17 optional 80-Hz order-10 LPF, timing shift, latency, artifact-before-baseline 순서를 정의한다. `linspace(0,1000/500,1000)`의 step은 $1/499.5$ s이다. | HPC2/HPC4의 `j/999*(1000/499.5)`는 이 출처와 불일치한다. |
| SRC-CODE-004 | `analysis/compare_p2p.m` SHA-256 `c6ab8439b109b0b9cf1c046a8045c9fe2be3df72222921a7450c5515cf8d486c`; `compute_p2p.m` SHA-256 `99f799ba93c70c05e131e3f3ce51935ea72ded0d4e63065198e3bc9fb1ce59e4` | early `[.015,.05]`, late `[.05,.25]`; time comparison은 양 끝 포함이고 trial마다 P2P를 계산한다. | 저자와 가까운 기술량은 mean trialwise P2P다. 선행 mean-waveform P2P는 별도 sensitivity로만 유지한다. |
| SRC-CODE-005 | `analysis/run_group_ep.m`, SHA-256 `d4a0ad2cee828c60fb87f91fc63a9c81b3588c974335350ed5fce10f2ac38da4`, lines 62--123 | 전역 threshold는 `(k,z,a)=(5,5,500)`. 일반 TS, p20, UC 호출은 모든 인자를 전달하지만 p17/p19 PB control 호출은 kurtosis 인자를 누락한다. 전체 코드 검색에서 MIN20/all-cell gate는 없다. | `(5,5,500)`은 저자 전역 의도를 수리한 명시적 측정 공리이며 literal-script 실행이 아니다. MIN20은 선행 분석자가 추가했다. |
| SRC-CODE-006 | `utils/get_stim_info.m`, SHA-256 `9bd003199a935d1daa14d4e0a039e755f00dfca6ccd52217e118f902eb84324e` | p17 phase channel은 D1이다. | PB p17의 D1-D2 local bipolar는 본 run의 분석자 sensitivity이며 저자 primary QC aperture가 아니다. |
| SRC-FT-001 | FieldTrip [`ft_preproc_dftfilter.m`](https://github.com/fieldtrip/fieldtrip/blob/master/preproc/ft_preproc_dftfilter.m) 및 [`ft_preprocessing.m`](https://github.com/fieldtrip/fieldtrip/blob/master/ft_preprocessing.m) | 기본 `dftreplace='zero'`는 지정 주파수 sine/cosine을 적합해 빼며, `dftbandwidth`와 `dftneighbourwidth`는 이 default에서 사용되지 않는다. 999 samples, 499.5 Hz에서는 60/120/180 Hz가 각각 정수 cycle이다. | 현재 공식 구현의 의미 확인일 뿐 저자가 사용한 FieldTrip commit은 알려지지 않았다. |
| SRC-FT-002 | FieldTrip [`ft_timelockbaseline.m`](https://github.com/fieldtrip/fieldtrip/blob/master/ft_timelockbaseline.m) | baseline 양 끝은 `nearest(time, endpoint)`로 고른 뒤 포함한다. 교정 grid에서 `[-.05,-.01]`은 indices 225..245이다. | 저자 FieldTrip commit 미고정 한계를 남기되, successor measurement axiom으로 이 규칙을 고정한다. |

## 출처 판정

원자료 판본·크기·채널·sample layout에는 현재까지 충돌이 없다. 반면 선행 Python
시간축은 저자 코드와 BrainVision header 양쪽에 의해 반박된다. 이 차이는 단순
표기 오류가 아니라 DFT 기저, latency 마지막 sample, early window와 baseline
sample을 바꾸며, amplitude-only로 막힌 p17 count에 직접 영향을 줄 수 있다.

저자 archive가 FieldTrip commit과 유효한 p17/p19 PB 함수 호출을 제공하지 않으므로
exact MATLAB replication은 `BLOCKED`. 후속 계산은 출처에 맞춰 수정한
`author-intended emulation`으로만 지칭한다.
