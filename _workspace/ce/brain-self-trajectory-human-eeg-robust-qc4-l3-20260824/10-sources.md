# BA-SRM4-L3 source lane

Status: COMPLETE

Contract SHA-256: `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`

## Source boundary

이 실행은 세포막·cable 전류식, history-dependent synaptic efficacy, scalp EEG 측정 한계를 서로 다른 주장으로 고정한다. 앞의 두 항목은 출발 모형의 생물물리 근거이고, 마지막 항목은 왜 실제 검정이 neuron edge가 아니라 EEG 관측 quotient에 머무는지를 제한한다. 임의 causal $C^\infty$ functional, 무한차원 metric과 자아 해석은 출처가 확립한 사실이 아니라 계약의 모델 공리 또는 미완성 다리다.

| ID | 1차·공식 출처 | 이 실행에서 허용하는 주장 | 금지하는 승격 |
|---|---|---|---|
| S4-01 | Rall, *Core Conductor Theory and Cable Properties of Neurons* (1977), [DOI 10.1002/j.2040-4603.1977.tb00811.x](https://doi.org/10.1002/j.2040-4603.1977.tb00811.x) | axial current, current conservation, membrane current와 cable equation은 compartment 출발 모형으로 사용할 수 있다. | scalp EEG가 실제 인간 cortical compartment나 edge conductance를 식별한다는 주장 |
| S4-02 | Hodgkin & Huxley, *A quantitative description of membrane current...* (1952), [DOI 10.1113/jphysiol.1952.sp004764](https://doi.org/10.1113/jphysiol.1952.sp004764), [PubMed](https://pubmed.ncbi.nlm.nih.gov/12991237/) | capacitance와 voltage-dependent ionic conductance를 갖는 막전류 모형 | 계약의 history functional 또는 인간 전체 뇌 metric이 실험적으로 확립됐다는 주장 |
| S4-03 | Ghanbari et al., *Estimating short-term synaptic plasticity from pre- and postsynaptic spiking* (2017), [DOI 10.1371/journal.pcbi.1005738](https://doi.org/10.1371/journal.pcbi.1005738) | ms–초 범위의 spike history가 유효 coupling을 바꿀 수 있고 history-function description이 가능하다. | 임의 $C^\infty$ infinite-history functional이 실제 시냅스의 유일하거나 정확한 법칙이라는 주장 |
| S4-04 | Brunner et al., *Volume Conduction Influences Scalp-Based Connectivity Estimates* (2016), [DOI 10.3389/fncom.2016.00121](https://doi.org/10.3389/fncom.2016.00121) | scalp channel은 brain/non-brain source의 혼합이고 volume conduction은 channel connectivity의 직접 source 해석을 막는다. | scalp channel area를 neuron-level edge, source connectivity 또는 ambient Riemann curvature로 동일시하는 주장 |
| S4-05 | [OpenNeuro ds006033 v1.0.1](https://openneuro.org/datasets/ds006033/versions/1.0.1), [DOI 10.18112/openneuro.ds006033.v1.0.1](https://doi.org/10.18112/openneuro.ds006033.v1.0.1) | frozen public snapshot과 dataset identity | byte range, parser 결과와 window hash가 출처만으로 보장된다는 주장 |
| S4-06 | 연관 data article, [DOI 10.1016/j.dib.2025.112258](https://doi.org/10.1016/j.dib.2025.112258) | inner-speech EEG 자료의 1차 논문 provenance | self·consciousness task 또는 causal intervention 자료라는 주장 |

## Executable provenance

공식 출처는 dataset identity만 고정한다. 실제 binary geometry와 모든 signal access는 predecessor manifest SHA-256 `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061`, range/parser SHA-256 `b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559`, HTTP `206`, `Content-Range`, ETag와 payload SHA-256 receipt로 별도 검증한다.

BA-SELF3 final SHA-256 `78199331071369981cf54d18a863dab075e0a1a413ab127c0931ab8ef4a9e445`와 B1 receipt SHA-256 `d3b7319804206b3ddcc6f35260706dfe4d4b961e0053db80c1c16c9569ead362`는 max-QC가 17/32에서 실패했고 path/model endpoint가 미개방이었다는 사실만 제공한다. 그 음성 apparatus 결과는 새 path 식의 증거나 반증이 아니다.

## Source verdict

전류 보존·conductance 기반 막전류와 history-dependent synaptic efficacy는 출발 모형의 근거가 있다. 그러나 $L^2_\rho$ history, causal $C^\infty$ functional, smooth coercive metric과 level-2 area의 self 해석은 이 실행이 채택한 수학 모형이다. 공개 EEG가 직접 검정할 수 있는 것은 고정된 관측·전처리 아래 ordered history feature의 held-out prediction gain뿐이다.
