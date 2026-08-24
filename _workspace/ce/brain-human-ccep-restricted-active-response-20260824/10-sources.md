# BA-OBS-ID3 source lane — 인간 CCEP 능동 개입 자료

Status: COMPLETE

## 1. 출처 우선순위와 동결 상태

이번 lane은 논문 본문보다 먼저 공개 저장소의 판본·객체·동반 메타데이터를
source-lock하고, 생리학적 시간창과 측정 한계는 원 논문으로 교차 확인했다. 계약을
동결할 때 열어 본 것은 dataset metadata, events/channels TSV, BrainVision header와
marker, derivative README뿐이다. Primary derivative의 `.eeg` sample value는 열지
않았다.

| ID | 종류 | 출처 | 이번 run에서 고정한 사실 | 한계 |
|---|---|---|---|---|
| S1 | 공식 dataset 판본 | [OpenNeuro ds003708 v1.0.2](https://doi.org/10.18112/openneuro.ds003708.v1.0.2), [공식 GitHub mirror](https://github.com/OpenNeuroDatasets/ds003708/tree/1.0.2) | CC0 BIDS-iEEG, 단일 피험자·단일 CCEP run, 공개 derivative와 source tag | 저장소 공개가 분석의 생물학적 타당성을 보장하지 않는다. |
| S2 | dataset 원 논문 | Miller, Müller, Hermes (2021), [PLoS Computational Biology](https://doi.org/10.1371/journal.pcbi.1008710) | 휴식 중 약 $0.2\,\mathrm{Hz}$ bipolar single-pulse stimulation, $200\,\mu\mathrm{s}$ biphasic pulse, 주로 $6\,\mathrm{mA}$, CCEP 자료 생성 맥락 | 한 환자의 임상 electrode 배치이며 population 표본이 아니다. |
| S3 | CCEP 원 연구 | Keller et al. (2014), [Journal of Neuroscience](https://doi.org/10.1523/JNEUROSCI.4289-13.2014), [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4078089/) | 자극 뒤 첫 $10\,\mathrm{ms}$ artifact 제외, early $10$--$50\,\mathrm{ms}$와 late $50$--$250\,\mathrm{ms}$ 구분, 근접 전극 제외와 directed/asymmetric CCEP의 선례 | 별도 cohort의 관행을 ds003708에 적용하는 것이며 universal neural law가 아니다. |
| S4 | derivative 생성 기록 | ds003708 v1.0.2 `derivatives/preprocessed/README.md` | 각 64-channel cable block에서 자극 전후 분산이 가장 낮은 75% channel을 이용한 adjusted common-average reference(A-CAR) | reference transform은 원 neural response와 분리 식별되지 않는다. |
| S5 | BrainVision schema | 동결된 `.vhdr`와 `.vmrk` | 89 channels, multiplexed IEEE float32, $2048\,\mathrm{Hz}$, channel resolution $0.1\,\mu\mathrm V$; marker position은 BrainVision 좌표임 | header 단위 표기가 encoding 손상을 보이므로 수치 resolution과 dataset 설명을 함께 사용한다. |

S1의 tag `1.0.2`는 Git object
`1b7588b3b67d35a35a7c795a5167d10cb4eb1e60`으로 확인했다. Primary signal object는

`ds003708/derivatives/preprocessed/sub-01/ses-ieeg01/ieeg/sub-01_ses-ieeg01_task-ccep_run-01_ieeg.eeg`

이며 계약에 `ContentLength=2899637088`, multipart ETag
`9832a1868bff527620c3cec91df4bb81-3`, S3 `VersionId`를 함께 고정했다. Multipart ETag를
파일 SHA-256처럼 해석하지 않고, 각 실제 byte range에는 별도 SHA-256 receipt를 남긴다.
Eligibility와 raw offset에 쓰는 MNI electrodes TSV와 BrainVision marker도 각각
`6606045c8881d7ed1ef15990c9160e2884bec8789b59aeb9bd5dba709a4b6aec`,
`a2e09a018d1359aaf1e8d0bdb65586ec0e4f9611ab9455497d83b3b7b7cfca24`로 고정했다.

## 2. 메타데이터로 확인한 분석 가능 범위

동결된 events TSV에는 425개 stimulation event가 있고 그중 391개가 `status=good`이다.
동결된 channels TSV에는 89개 channel이 있으며, good channel은 ECoG 64개와 SEEG
12개다. `status=good`, 정확히 $6.0\,\mathrm{mA}$, site당 10회 이상, 두 contact 모두
good ECoG/SEEG, finite MNI coordinate라는 신호독립 규칙을 적용하면 24개 bipolar
stimulation site가 남는다. Shared contact와 midpoint distance $<15\,\mathrm{mm}$를
제외한 양방향 비교 후보는 245 unordered pairs다.

Events의 `sample_start`는 $\operatorname{round}(2048\,t_{\rm onset})$와 425/425 event에서
일치한다. BrainVision `.vmrk` position은 이 값과 같은 event가 201개, 1 큰 event가
224개다. `.eeg`와 같은 BrainVision export에 속한 marker를 canonical signal anchor로
삼아 **raw 0-based index = VMRK position $-1$**로 동결한다. Events는 marker와 행 순서로
one-to-one crosswalk하고 `raw_index - sample_start`가 정확히 $-1$ 또는 $0$인지 확인한다.
그 밖의 차이, event/marker count 불일치 또는 hash 불일치는 sample decode 전에
`SOURCE_METADATA_ALIGNMENT_STOP`이다. 구현 전 fixture는 이 off-by-one 규칙도 검사한다.

## 3. 측정모형이 허용하는 주장

자료가 직접 주는 것은 electrode reference가 적용된 유발전압이다. 이를 가장 좁게 쓰면

$$
V_{c\leftarrow s}^{\rm obs}
=C_{\rm ref}R_c[H_s*u_s]+a_{cs}+\eta_{cs}.
$$

따라서 관측 CCEP magnitude의 방향 비대칭은 neural propagation, electrode/volume
readout, reference, artifact와 noise의 결합 결과다. 반대로 관측 대칭성이 남더라도
self-adjoint brain metric을 식별한 것이 아니다. 이번 자료에는 합·차 자극 query나
여러 자극 세기가 없으므로 BA-OBS-ID2의 polarization tomography와 amplitude
linearity도 시험하지 않는다.

## 4. 출처 판정

- `DATA_PROVENANCE`: VERIFIED_FOR_LOCKED_SINGLE_SUBJECT_DATASET.
- `INTERVENTION`: VERIFIED_BIPOLAR_SPES.
- `REFERENCE_TRANSFORM`: VERIFIED_DERIVATIVE_A_CAR, matched bipolar readout required.
- `POPULATION_GENERALIZATION`: NOT_AVAILABLE.
- `AMBIENT_METRIC_OR_DIMENSION_IDENTIFICATION`: NOT_AVAILABLE.
- `CONSCIOUSNESS_SELF_HIPPOCAMPUS_AGI_VALIDATION`: NOT_AVAILABLE.
