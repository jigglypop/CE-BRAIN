# BA-SRM6 출처 레인 — 실제 전뇌 칼슘자료와 측정 경계

Status: COMPLETE

Date: 2026-08-23

## 1. 출처 판정

이번 run의 실제자료 표적은 Hallinen et al.이 자유롭게 움직이는 *C. elegans*에서
동시에 기록한 population calcium activity와 locomotion이다. 논문은 population
activity가 단일 neuron보다 velocity와 curvature를 더 잘 decode했다고 보고하고,
GCaMP/RFP의 공통 변동을 제거하는 motion correction과 calcium-insensitive GFP/RFP
animals 11마리를 control로 사용했다. 따라서 이 자료는 population fluorescence와
locomotion의 예측 관계 및 motion-artifact 대조를 시험하기에 적합하다. 반면 calcium은
spike·막전압·시냅스 전류를 직접 측정하지 않고, 이 자료에는 conscious report,
hippocampus 또는 randomized neural intervention이 없다.

| 항목 | 독립 출처 판정 | 이번 run의 용도 |
|---|---|---|
| Hallinen et al., eLife 2021, DOI `10.7554/eLife.66135` | `SUPPORTED` | simultaneous population calcium–locomotion measurement와 GFP control의 1차 출처 |
| OSF `dpr3h`, DOI `10.17605/OSF.IO/DPR3H` | `SUPPORTED` | official public data node와 file identity |
| OSF node license field | `SUPPORTED: null` | local analysis·citation만 허용하고 raw 재배포·commit 금지 |
| `Ratio2`, `R2`, `hasPointsTime`, embedded behavior schema | `PENDING_FRESH_BYTE_AUDIT` | archive download·hash 뒤 MAT-v5 input gate에서 직접 확인 |
| calcium trace에서 spike/current/connectome 복원 | `BLOCKED` | measurement operator가 many-to-one이고 inverse가 source-locked되지 않음 |
| conscious moment·hippocampal index | `BLOCKED_BY_ORGANISM_AND_TASK` | 현재 dataset이 해당 변수를 측정하지 않음 |

## 2. official OSF file lock

2026-08-23 official OSF API는 node title을 “Decoding locomotion from population
neural activity in moving C. elegans”, `public=true`, node license를 `null`로 반환했다.
이번 계약이 사용하는 file identity는 다음과 같다.

| 파일 | OSF ID | API bytes | download ID | 이전 checksum receipt |
|---|---|---:|---|---|
| `AML310_moving.tar.gz` | `5fe26e73c05e2d009b1cec0f` | 348,444,164 | `evhrg` | `144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a` |
| `AML32_moving.tar.gz` | `5fe27e4066e53500b4aa8f03` | 1,218,075,251 | `v8huy` | `6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63` |
| `AML18_moving.tar.gz` | `5fe27db666e53500b3aa6b38` | 1,409,801,111 | `hsg2y` | `588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82` |

이 표는 예전 tracked manifest의 AML32 URL 오류를 고친다. 일부 HTTP redirect
response의 `Content-Length`는 OSF API의 logical file size와 달랐으므로 그것을
checksum 대용으로 쓰지 않는다. 완료된 local file의 exact byte 수와 SHA-256만 input
gate에 사용한다. 계약 전에는 raw archive가 로컬에 없었고, 과거 compact result를 새
endpoint로 재사용하지 않는다.

## 3. 측정모형과 교란

논문에서 GCaMP과 RFP는 같은 neuron에서 함께 측정되며, motion artifact가 두
fluorophore에 공통으로 나타날 수 있다는 가정 아래 correction한다. GFP control은
calcium sensitivity가 없지만 유사한 motion과 optical nuisance를 겪는다. 이 설계는
`Ratio2`의 locomotion 예측이 `R2` 또는 GFP에서 동일하게 나타나는지를 adverse
control로 시험할 근거를 준다. 하지만 이후 연구는 two-channel correction 자체가
완벽하지 않으며 motion-dependent fluorescence가 substantial할 수 있다고 지적했다.
그러므로 red-channel과 GFP control을 둘 다 통과하지 못하면 neural interpretation을
올리지 않는다.

Volume sampling은 약 5--6 Hz 계열이므로 계약의 60-volume window는 대략 10초다.
정확한 시간은 `hasPointsTime`의 train median으로 다시 계산하고, 중복 time과 긴 gap을
가로지르는 window를 제거한다. $W=60$과 $h=6$은 출처가 강제한 생물 상수가 아니라
결과 전에 동결한 분석 선택이다. Calcium-indicator kinetics와 preprocessing 때문에
유효차원은 `observed fluorescence quotient`의 통계로만 해석한다.

## 4. 데이터 단위와 일반화 경계

GCaMP 11 recording은 각각 다른 animal이다. Cross-record canonical neuron identity와
connectome node mapping이 없으므로 neuron axis를 animal 사이에 직접 정렬하지 않는다.
각 recording의 고정 basis 안에서 spectrum을 계산하고, recording 사이에는
$d_{\rm eff}$·stability 같은 불변 summary만 비교한다. Replicate unit은 neuron이나
window가 아니라 recording/animal이다.

Hallinen corpus는 이 repository의 과거 다른 분석에 노출된 적이 있다. 이번 식의
within-run held-out block은 새 endpoint에 대한 temporal holdout이지만 독립 외부
replication은 아니다. 통과하더라도 증거 상한은 developmental L3 predictive
consistency다.

## 5. 후속 독립자료 경로

| 후보 | 출처 | 허용되는 후속 시험 | 현재 제외 이유 |
|---|---|---|---|
| WormID | DANDI `001623`, version `0.251015.0312` | 다기관·다개체 NWB에서 동일 operator의 독립 replication | 약 774.2 GB이고 현재 로컬 입력이 아니며 별도 source lock 필요 |
| IBL Brain-wide Map | official IBL release와 AWS Open Data | mammalian Neuropixels에서 region/state held-out predictive transfer | 현재 official cache/session이 없고 intervention 없는 lagged relation은 causal routing이 아님 |
| Norman human iEEG | Zenodo DOI `10.5281/zenodo.3259368` | hippocampus–cortex reinstatement와 sparse-address의 별도 시험 | processed memory-task release이며 현재 calcium contract·의식 일반론과 다른 질문 |

해마 희소 index는 Norman 계열 자료에서 별도 계약으로 시험해야 한다. C. elegans
결과로 그 경로를 대신하거나 두 결과를 하나의 결합기전으로 곱하지 않는다.

## 6. 1차 출처

- Hallinen, K. M. et al. (2021), “Decoding locomotion from population neural
  activity in moving C. elegans,” *eLife* 10:e66135,
  https://doi.org/10.7554/eLife.66135, accessed 2026-08-23.
- Open Science Framework dataset, “Decoding locomotion from population neural
  activity in moving C. elegans,” https://doi.org/10.17605/OSF.IO/DPR3H,
  official API accessed 2026-08-23.
- Chaudhary, S. et al. (2022), “Correcting motion induced fluorescence artifacts
  in two-channel neural imaging,” https://doi.org/10.1371/journal.pone.0270939,
  accessed 2026-08-23.
- International Brain Laboratory Brain-wide Map data release,
  https://docs.internationalbrainlab.org/notebooks_external/data_release_brainwidemap.html,
  accessed 2026-08-23.
- DANDI Archive, Dandiset `001623`, https://dandiarchive.org/dandiset/001623,
  accessed 2026-08-23.
- Norman et al. public analysis release,
  https://doi.org/10.5281/zenodo.3259368, accessed 2026-08-23.
