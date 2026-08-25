# 출처 레인 — 전수 endpoint의 상속 provenance

Status: COMPLETE

Access date: 2026-08-25

새 외부 입력은 없다. 이 light successor는 직접 선행 run의 1차 출처와 exact artifact를
아래 hash로 다시 고정한다.

| ID | 고정 출처·artifact | 상속 사실 | 판정과 한계 |
|---|---|---|---|
| SRC-DATA | [OpenNeuro ds006065 v1.0.0](https://openneuro.org/datasets/ds006065/versions/1.0.0), git commit `14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4` | 18-object identity lock `66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`; 선행 full-object 거래에서 18/18, 총 723,560,000 bytes의 expected/observed SHA·size·version ID·ETag가 일치했다. | exact object identity를 상속한다. 이번 거래도 각 full object를 다시 검증해야 한다. |
| SRC-Q | 선행 `qc_recheck1.json` / `recheck_progress.json` | SHA-256 `04edcbe5c290985f6a59c230989f4d13d83323e193767559ec4e15562de9e6e6` / `da9d5d5f77d31632640faef11b3fb8cc7b44068c849c051d0db658938a06d679`; TS/p17/post `12/25`, PB/p17/pre `24/11`; receipt-progress 결박 유효. | 두 row는 새 18-object 계산과 exact 일치해야 한다. 선행 Q는 재실행하지 않는다. |
| SRC-PAPER | Kragel et al., *Nature Communications* 2025, DOI [10.1038/s41467-025-59417-7](https://doi.org/10.1038/s41467-025-59417-7) | theta stimulation과 유발반응/연결성 변화의 원 연구다. | 이번 run은 제한된 P2P 기술량만 계산하며 논문의 mixed model을 복제하지 않는다. |
| SRC-AUTHOR | [Zenodo record 14735080](https://zenodo.org/records/14735080), archive MD5 `6feba89b7c49fd661b39b589e8d9624a` | 공개 MATLAB 코드의 고정 archive다. `get_epoched_eeg.m` SHA `6331f0342cea448c5d4256a3e358a614cbfd3a8c0c0d3c0733ecaf9e641ef97b`; `run_ep_preproc.m` SHA `626a7467f803c28302ad712b24b891752b013fc471fec7f0057d529fc7ff0729`; `compute_p2p.m` SHA `99f799ba93c70c05e131e3f3ce51935ea72ded0d4e63065198e3bc9fb1ce59e4`. | 시간축·QC·trialwise P2P 근거를 상속한다. p17/p19 PB 호출 인자 결함과 FieldTrip 판본 미고정 때문에 literal parity는 불가하다. |
| SRC-FT | FieldTrip [`ft_preproc_dftfilter.m`](https://github.com/fieldtrip/fieldtrip/blob/master/preproc/ft_preproc_dftfilter.m), [`ft_preprocessing.m`](https://github.com/fieldtrip/fieldtrip/blob/master/ft_preprocessing.m), [`ft_timelockbaseline.m`](https://github.com/fieldtrip/fieldtrip/blob/master/ft_timelockbaseline.m) | default zero-replacement DFT 의미와 nearest-inclusive baseline semantics를 고정한다. | 현재 공식 구현 의미이며 저자 사용 commit의 binary parity는 아니다. |
| SRC-LOADER | `examples/brain/ba_obs_hpc2_author_qc_reanalysis.py` | frozen loader SHA-256 `8e9358ea72217b4f0d48f96d174ec506f3b2faf4b55cb2d2ebcc3248a93fb85c`; full-object GET, header/version/ETag/size/SHA, BrainVision decode와 selected-channel µV 변환을 수행한다. | raw-to-witness 추출은 이 단일 구현에 의존한다. 독립 validator는 witness 이후부터 재계산한다. |
| SRC-CORRECTED | `examples/brain/ba_obs_hpc5_author_intended_recheck.py` | corrected executor SHA-256 `79191826af3a28b174cc793119817e1536e9466f9a162d1dcc05bea724b25c54`; $t_j=j/499.5-0.5$, dual-path QC와 고정 aggregate 수식을 제공한다. | 계산 재사용 전 exact hash를 확인한다. 선행 endpoint validator는 사용하지 않는다. |

## 출처 판정

원자료 판본·object identity·BrainVision layout·교정 시간축·QC·P2P 정의에는 새 충돌이
없다. 새 endpoint authority는 raw-to-witness 추출의 독립 구현을 추가하지 않는다.
따라서 frozen loader와 매 object source receipt가 그 구간의 provenance ceiling이며,
별도 validator의 독립 재계산 주장은 selected-source witness 이후에만 적용한다.
