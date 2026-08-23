# BA-SRM8 출처 레인 — 공개 전처리와 분석자 successor의 분리

Status: COMPLETE

Date: 2026-08-23

## 1. 독립 출처 표

| 출처 | 불변 식별자 | 직접 지지하는 내용 | 지지하지 않는 내용 |
|---|---|---|---|
| Hallinen et al., *eLife* (2021) | [DOI 10.7554/eLife.66135](https://doi.org/10.7554/eLife.66135) | 움직이는 *C. elegans*의 population calcium, locomotion과 held-out decoding | synaptic edge, loop operator, hippocampal hash, consciousness, AGI |
| 공개 데이터 | [OSF DOI 10.17605/OSF.IO/DPR3H](https://doi.org/10.17605/OSF.IO/DPR3H) | AML310/AML32 GCaMP와 AML18 GFP archive의 출처 | OSF license field가 null이므로 재배포 권리 |
| PredictionCode | [exact GitHub revision](https://github.com/leiferlab/PredictionCode/tree/ca59416112a9c10a8d6a3179092a7d3c888bcd4e) | published predictor와 전처리 구현 provenance | BA-SRM8 물리시간 estimator가 published method라는 주장 |
| Software Heritage | [revision archive](https://archive.softwareheritage.org/browse/revision/ca59416112a9c10a8d6a3179092a7d3c888bcd4e/) | 위 Git revision의 독립 archival locator | 현재 로컬 실행 환경의 동일성 전체 |

`artifacts/source-lock.json` SHA-256은
`234bac2c67e98a8a0745ef412745b5c360d4d5751d73c14f290c15f1d80ad495`다. 그 파일은
BA-SRM7 source lock
`d1f8063ffa823bff78d316b070327eb4358ce74a7247a19aa6f32f76b099e280`을 부모로
명시한다.

## 2. 로컬 exact provenance

로컬 read-only clone은 detached revision
`ca59416112a9c10a8d6a3179092a7d3c888bcd4e`와 일치한다.

| 파일 | SHA-256 |
|---|---|
| `utility/data_handler.py` | `69c2ff90f1aa98a04e5b4b89c7e2319b176db0dfd1a012c9b6eff54c5d6b89bd` |
| `utility/get_all_recordings.py` | `b26d0d0d9c05c2ebc3123cbdde23429225fa0d20265977ef6e09dacee488a863` |
| `LICENSE` | `189b1af95d661151e054cea10c91b3d754e4de4d3fecfb074c1fb29476f7167b` |

code license는 GPL-2.0이다. OSF metadata의 license field는 null이므로 archive와
extracted MAT는 local ignored evidence로만 사용하고 repository에 넣지 않는다.

세 archive는 predecessor에서 다음 bytes/hash로 확인됐다.

| archive | bytes | SHA-256 |
|---|---:|---|
| `AML310_moving.tar.gz` | 348444164 | `144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a` |
| `AML32_moving.tar.gz` | 1218075251 | `6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63` |
| `AML18_moving.tar.gz` | 1409801111 | `588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82` |

## 3. 공개 코드에서 확인된 좁은 사실

published predictor의 neural field는 `Neurons.I_smooth_interp_crop_noncontig`다.
`Ratio2`는 별도 correlation analysis에 쓰이지만 predictor의 primary input은 아니다.
interpolation 전 timepoint rule은 neuron의 missing fraction이 0.5보다 작은지 검사한다.
공개 smoothing은 6 Hz volume clock에서 $\sigma=5$인 centered symmetric Gaussian이다.

따라서 이 archived field는 원 논문의 predictor를 재현하는 진단에는 적합하지만,
현재 시점 $t$에서 $t+h$를 예측하는 strict causal primary에는 미래 neural sample을
읽으므로 그대로 쓸 수 없다.

## 4. BA-SRM8에서 새로 두는 분석자 공리

다음 항목은 위 논문이나 공개 코드가 채택한 방법이라고 주장하지 않는다.

- raw first-60% parameter fit과 one-sided Gaussian;
- original physical clock grid의 유지와 manual/flag mask 0;
- 비음수 EXP/BIEXP/POWER/COMPACT causal kernel;
- timepoint quality $q$와 $q^2$ weighting;
- radial Huber 또는 radial tanh map;
- weighted effective sample size $n_{\rm eff}$;
- 70/2/3/2.5/2.5/20 successive-halving funnel.

이들은 모두 `source-rooted analyst-defined successor`다. 출처가 보장하는 것은 입력
channel, 공개 preprocessing의 출발점, 데이터와 behavior field의 provenance다. 새
operator의 PSDㆍ인과성ㆍ무차원성과 복원 성능은 별도 수학ㆍ합성 검증 대상이다.

## 5. 생물학적 범위 제한

population calcium와 locomotion의 예측 관계는 세포 수준 synaptic adjacency나 방향을
식별하지 않는다. covariance는 시간 순서의 많은 정보를 버리고, 이 corpus에는 해마,
주관 report, perturbation된 의식 수준 또는 AGI agent가 없다. 따라서 edge, loop,
hippocampal hash, consciousness와 AGI 주장은 source lane에서 모두
`UNSUPPORTED / BLOCKED`다.

출처 판정: **PASS for corpus/provenance; analyst successor requires independent math and apparatus validation**.
