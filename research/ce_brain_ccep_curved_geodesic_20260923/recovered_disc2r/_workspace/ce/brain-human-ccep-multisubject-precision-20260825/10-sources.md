# BA-OBS-DISC2 source lane — 74명 인간 SPES/CCEP 전기 response

Status: COMPLETE

## 판정

`SOURCE_SUPPORTED_RAW_MULTI_SUBJECT_TEST / BIOLOGICAL_METRIC_NOT_IDENTIFIED`.

공식 원자료와 원 논문은 74명에서 실제 전기자극에 대한 ECoG response를 patient-disjoint로
검증할 수 있게 한다. passive cable/linear-response 문헌은 cable/heat 후보 문법을 허용한다.
그러나 공개 좌표는 fsaverage/MNI305-derived surface proxy이고 diffusion tract 또는 native
axonal path가 아니므로, 성공해도 생물학적 Riemannian metric을 복원했다고 말할 수 없다.

## 1차·공식 출처 표

| source-supported claim | 1차/공식 출처 | 이번 run의 사용 | 넘지 못하는 경계 |
|---|---|---|---|
| `ds004080`은 74명, age 4–51의 SPES/CCEP ECoG 자료다. | [OpenNeuro 공식 repository, tag 1.2.4](https://github.com/OpenNeuroDatasets/ds004080/tree/1.2.4), dataset DOI [10.18112/openneuro.ds004080.v1.2.4](https://doi.org/10.18112/openneuro.ds004080.v1.2.4) | participant, events, channels, coordinates, raw BrainVision source lock | 임상 epilepsy·수술 electrode coverage이며 일반 인구의 무작위 표본이 아니다. |
| acquisition은 1 ms, 0.2 Hz monophasic 10 pulses이고 27명은 5 pulses 뒤 polarity를 바꿨다. 통상 8 mA, 필요 시 4 mA였다. | van Blooijs et al., *Developmental trajectory of transmission speed in the human brain*, [DOI 10.1038/s41593-023-01272-0](https://doi.org/10.1038/s41593-023-01272-0), Methods “Acquisition” | `A-B/B-A`를 동일 source로 합치고 orientation을 보존; current는 기록하되 자유 source offset과 비식별이므로 fitted coefficient에서 제외 | event table에는 일부 6/7 mA도 있으므로 논문 대표값을 전역 상수로 강제하지 않는다. |
| stimulation artifact는 대략 -9–9 ms이고 원 연구는 9 ms 뒤 N1을 보며 source로부터 13 mm 이내 electrode를 제외했다. | 같은 원 논문, Methods “Acquisition” 및 “N1 latency calculation” | endpoint 시작 10 ms, center distance ≥15 mm | 10 ms 이후 artifact나 volume conduction이 완전히 0이라는 보장은 아니다. |
| 원 연구는 10 epochs를 baseline-correct 후 평균하고 9–100 ms N1을 검출했다. | 같은 원 논문, Methods “N1 latency calculation” | 10-trial average와 prestimulus normalization의 생리학적 근거 | 이번 endpoint는 N1 peak 검출이 아니라 사전 고정 five-bin energy이므로 원 논문 결과를 재현한다고 과장하지 않는다. |
| dataset README는 MNI152를 말하지만 실제 `coordsystem.json`은 fsaverage, mm, MNI305 variant와 surface transform distortion을 명시한다. | [공식 dataset README](https://github.com/OpenNeuroDatasets/ds004080/blob/1.2.4/README), 각 subject의 공식 `coordsystem.json` | sidecar 우선의 `fsaverage/MNI305-derived geometry proxy` | Euclidean 거리·diagonal $G$는 native cortical/axonal geodesic이 아니다. |
| passive neuronal cable은 membrane capacitance, leakage와 axial conductance에서 diffusion/attenuation equation을 얻는다. | Rall, *Core Conductor Theory and Cable Properties of Neurons* (1977), [DOI 10.1002/j.2040-4603.1977.tb00811.x](https://doi.org/10.1002/j.2040-4603.1977.tb00811.x); Rall (1959), [DOI 10.1016/0014-4886(59)90046-9](https://doi.org/10.1016/0014-4886(59)90046-9) | $C\dot v=-Av+Bu$ local linearization, cable/heat candidate grammar | whole-brain SPES response가 passive cable 하나라는 증거가 아니다. |
| 자극-history response는 scalar connection보다 Green/response function으로 표현할 수 있고 실제 신경계는 비선형·상태 의존일 수 있다. | Randi & Leifer (2021), [DOI 10.1103/PhysRevLett.126.118102](https://doi.org/10.1103/PhysRevLett.126.118102) | history-dependent $\mathcal F$와 short-window response operator 구분 | C. elegans 결과를 인간 CCEP나 consciousness 증거로 옮기지 않는다. |
| reference와 volume conduction은 iEEG 관계를 바꾸며 montage 의존성을 남긴다. | Anastasiadou et al. (2019), [DOI 10.3389/fnins.2019.00221](https://doi.org/10.3389/fnins.2019.00221) | $C_{ref}R$, bipolar primary, contact-mean diagnostic | bipolar도 ground truth가 아니며 distant/common neural signal을 제거할 수 있다. |

## 원천 전수 감사

공식 Git tree `c4fd7418883e33b024292468eb14da1649f51aae`를 recursive로 고정했다.
`artifacts/ds004080_metadata_audit.py`는 117 recordings 각각에 대해 Git blob hash, annex
SHA-256/size, actual `.vhdr/.vmrk` hash, S3 HEAD의 ETag/VersionId/Content-Length, locked
64-byte HTTP 206 probe, BrainVision float32 multiplexed header, JSON/channels/events와 byte
duration을 대조했다. 결과는 74/74 eligible, 117/117 recording, receiver ≥6인 metadata-valid
source 3,213개다. 실제 split은 receiver ≥16인 3,202개 중 subject당 8개를 고른다.

두 번의 fail-closed가 있었다. 첫째, 이 dataset의 `sample_start`는 이미 zero-based여서
`sample_start-1` 가정이 -1 sample을 만들었다. 전체 117 tables에서
`sample_start=round(onset×fs)`를 확인해 바로잡았다. 둘째, 2048 Hz header가
`SamplingInterval=488.2812 µs`로 반올림돼 역수가 2048과 $2.10\times10^{-4}$ Hz 차이났다.
header가 JSON rate와 relative $10^{-6}$ 안인지 확인한 뒤 sample geometry에는 BIDS JSON의
2048 Hz를 사용했다. 둘 다 response endpoint를 열기 전 source-schema 교정이다.

27명의 5-trial apparent shortage는 원 논문의 polarity reversal과 일치했다. unordered
contact pair로 합치자 74명 전부가 clean 10-trial source 조건을 충족했다. source manifest
SHA-256은 `9ed8cb9d7a12cf293f8a899aa9a04de7951109b0fad0505e08ebe93f9e11b3c3`다.

## 허용·금지 추론

- `[허용]` 실제 새로운 환자에서 identical-nuisance temporal baseline과 fsaverage geometry
  후보의 five-bin bipolar response prediction을 비교한다.
- `[허용]` isotropic cable, determinant-one diagonal cable, isotropic heat coupling,
  determinant-one diagonal heat coupling을 D0에서 경쟁시킨다.
- `[금지]` fitted $G$를 axonal/cortical metric tensor, $d_G$를 fiber length로 부른다.
- `[금지]` free temporal exponent를 latent dimension $q$로 재명명한다.
- `[금지]` CCEP energy prediction을 의식, self, hippocampal indexing 또는 AGI 검증으로
  승격한다.

## Source-lane 결론

원천·형식·개입·측정 시각은 실제 뇌 검증을 수행하기에 충분하다. 남은 불확실성은 자료
접근이 아니라 식별성이다. 그래서 primary claim은 patient-held-out observed response에
한정하고, geometry permutation과 prestimulus negative control을 final falsifier로 둔다.
