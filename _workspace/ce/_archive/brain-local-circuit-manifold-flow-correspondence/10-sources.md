# 출처 레인 — neural manifold와 dynamics의 경험적 상한

Status: COMPLETE

## Constructive successor

The source audit is frozen at
`artifacts/epochs/constructive-affine-fiber/10-sources.md`. Population ODEs and
latent/recurrent population-state models support the modeling background, but
do not establish the affine contracting-fiber assumptions in a biological
circuit. That endpoint is UNVERIFIED.

Access date: 2026-08-27

## 실제 자료 출처 잠금

개발 자료는 DANDI `001701`, immutable version `0.260120.0303`, DOI `10.48324/dandi.001701/0.260120.0303`이다. 사용 자산은 `sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb`, asset UUID `3f3d0b16-9b3e-42ac-a5e6-327829df1116`, 크기 `12,967,760` bytes, SHA-256 `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3`로 고정했다. 자료는 수컷 C57BL/6 mouse의 X-maze Neuropixels 세션이며 Units, LFP, position, compass direction을 포함한다. 라이선스는 CC-BY-4.0, 접근 상태는 OpenAccess다.

출처 영수증은 `artifacts/epochs/real-dandi-001701/source-receipt.json`과 R1 pivot의 `source-receipt.json`에 있다. 확인 후보 DANDI `001695@0.260319.2023`은 R1 내부 gate를 모두 통과할 때만 열도록 봉인했으며, 실제로 열지 않았다.

이 레인은 첨부문의 배경만 확인한다. 아래 문헌은 수학 정리
$(G,W,\Phi)\Rightarrow(M,b)$를 증명하지 않으며, 실제 뇌가 계약의 정칙성·불변성
가정을 만족한다는 증거로 쓰지 않는다.

| 배경 주장 | 1차/권위 출처 | 지지 범위와 한계 |
|---|---|---|
| neural population activity가 고차원 발화공간에서 저차원 trajectory를 보일 수 있음 | Churchland et al., *Nature* 487, 51–56 (2012), DOI: https://doi.org/10.1038/nature11129 | 원숭이 운동피질 reach 자료에서 저차원 population trajectory와 회전성 dynamics를 보고했다. 모든 뇌·과제의 보편 manifold 또는 회로 원인을 증명하지 않는다. |
| 여러 행동에서 보존되는 저차원 population 구조가 존재할 수 있음 | Gallego et al., *Nature Communications* 9, 4233 (2018), DOI: https://doi.org/10.1038/s41467-018-06560-z | 분석된 운동행동 범위의 통계적 보존이다. 해부학적 connectivity가 manifold를 직접 생성한다는 개입 증거는 아니다. |
| 비평면 intrinsic topology의 직접 사례 | Gardner et al., *Nature* 602, 123–128 (2022), DOI: https://doi.org/10.1038/s41586-021-04268-7 | grid-cell module에서 toroidal population topology를 추론했다. torus만으로 continuous-attractor mechanism을 유일하게 식별하지 못하며 feedforward 설명도 배제하지 않는다. |
| recurrent network를 continuous-time nonlinear dynamics로 기술 가능 | Sussillo & Abbott, *Neuron* 63, 544–557 (2009), DOI: https://doi.org/10.1016/j.neuron.2009.07.018 | 모델 RNN에서 synaptic weight와 population dynamics를 연결한다. 실제 뇌 특정 회로가 동일 ODE를 구현한다는 실증은 아니다. |
| population dynamics를 computation의 분석 단위로 삼는 관점 | Vyas et al., *Annual Review of Neuroscience* 43, 249–275 (2020), DOI: https://doi.org/10.1146/annurev-neuro-092619-094115 | 종합 리뷰다. 회로 원인과 population-level 기술을 구별해야 한다. |
| 저차원성은 보편 명제가 아님 | Stringer et al., *Nature* 571, 361–365 (2019), DOI: https://doi.org/10.1038/s41586-019-1346-5 | mouse visual cortex에서 high-dimensional geometry를 보고했다. 유효 차원은 영역·자극·과제·추정법에 의존할 수 있다. |
| 실제 자료의 “manifold”는 엄밀한 매끄러운 다양체가 아닐 수 있음 | Chung & Abbott, *Current Opinion in Neurobiology* 64, 1–8 (2021), author manuscript: https://www.columbia.edu/cu/neurotheory/Larry/ChungCurrOpin21.pdf | noise와 sparse sampling 아래 neural manifold는 넓은 의미의 geometry일 수 있다. 매끄러움·차원·불변성은 별도 검정 대상이다. |
| movement neural-manifold 분석이 metric tensor의 기전 식별을 제공하지는 않음 | Gallego et al., *Neuron* 79, 698–715 (2017), DOI: https://doi.org/10.1016/j.neuron.2017.05.025 | modes와 trajectories를 설명하지만 고유한 neural cost metric을 도출하지 않는다. |

## 출처 판정

문헌이 허용하는 최소 경험 문장은 “일부 neural populations에서 저차원 또는
비선형 population structure가 관측되고, vector-field/dynamical-system 모델이
유용할 수 있다”이다. connectivity와 update에서 매끄러운 invariant $M$, 유일한
$b$, 또는 회로 비용 계량 $g$가 자동으로 나온다는 문장은 어떤 출처도 입증하지
않는다. 특히 Gardner et al.의 topology 결과는 mechanism의 비식별 경계를 직접
보여 주며, Stringer et al.은 $D\ll N$의 보편화를 막는다.
