# 인간 해마 인접 iEEG endpoint 결과 원장

Status: FROZEN

Run: `CE_RUN=_workspace/ce/brain-human-hippocampal-theta-endpoint-recovery-20260825`

## 범위·정의·단위

- [정의] 분석 대상은 OpenNeuro `ds006065` v1.0.0 (commit `14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`)의 version-pinned 18개 객체이며, TS 4명과 PB 5명(중복 p17, p19)의 고유 7명 epilepsy-surgery participant이다.
- [정의] 관측량은 clean trial의 baseline-corrected P2P이며 단위는 µV이다. P2P, 각 participant의 post−pre 변화, 그리고 participant-equal contrast `D = mean(TS 변화) − mean(PB 변화)` 모두 µV이다. P2P는 trial 내 상수 baseline에 불변이나 mean-waveform 재현에는 baseline 보정을 유지한다.
- [정의] 시간 grid는 `t_j=j/499.5−0.5 s`; window index는 prestim `100..199`, early `258..274` (15–50 ms), late `275..374` (50–250 ms)이다. clinical과 local-bipolar reference, trial-mean과 mean-waveform 두 estimand를 전량 보고한다.
- [정의] `95% bootstrap interval`은 PCG64 seed `20260825`의 65,536 shared unique-participant exponential-weight draw에서 얻은 기술적 구간이며, `P(D>0)` 역시 그 draw 비율이다. 어느 것도 p-value가 아니다.
- [정의] LOO는 고유 7명 각각을 한 번씩 제외한 `D`이며 표의 부호열 순서는 `p16,p17,p18,p19,p20,UC004,UC005`다.
- [정의] primary는 clinical × trial-mean × late의 participant-equal `D`다. clinical mean-waveform late, 모든 early/prestim, local-bipolar, LOO 및 p17/p19 paired contrast는 고정 sensitivity/control이다.
- [정의] clean count의 정의역은 각 고정 cell에서 `n≥1`이다. 임의 `MIN10`/`MIN20` threshold는 사용하지 않았다. clinical zero-clean이면 `CLINICAL_PAIR_UNAVAILABLE`; bipolar zero-clean이면 clinical을 보존하고 bipolar bundle 전체를 생략하는 계약이다. 이번 결과는 clinical/bipolar zero cell 모두 0개다.

## 입력·거래 권위

| 항목 | SHA-256 / 상태 | 원장 판정 |
|---|---|---|
| predecessor selected-trace witness (36 arrays, 13,053,329 bytes) | `2a5a9328cab95f6a484a76af5c7e34deccbace52a9eb5a00241ee08f0d2e58ae` | [산출] exact input |
| predecessor raw result (18 records/files) | `cd3aaff53b1db1dba97f92812f529f066c870ac968bdd7a27f0b9ad4c0a8585d` | [산출] `RAW_COMPLETE` |
| predecessor terminal progress | `2a1f1e3a4730c04b3d79426d592c4b3c071fe4088c2953b2afa87dfefe11ae90` | [산출] `IMPLEMENTATION_STOP`; error `ModuleNotFoundError: No module named 'examples'`; 18 completed rows |
| predecessor analysis / execution lock | `a55e605fec8a8e84bf783dcec7ad853315207f6633b783c55ca2921d9c62d431` / `aefbec437279519bd568e77ffc0f5a01b1795b24843acb178abfdc9a1f57aa6b` | [산출] frozen predecessor bindings |
| recovery analysis / execution lock | `ecf9d0d7103ae5b64e313932e865fe62d96ae5f80078bac0085a98b3130b0347` / `0acea44be1fef668430b55fd492255b318127a9f437244d10f9aaf3c073123d1` | [산출] `ENDPOINT_RECOVERY1` binding |
| recovery validator, pre-COMPLETE / COMPLETE | `fc45875e740a92339d7d019691d83a9ff9a1f923fe8040af7a81180c1b436470` / `47272d2017fc3890bbe6c28ad206d36e0860e91ca849b2e9bae22392626dfe73` | [산출] both immutable checks present |
| recovery progress / receipt | `0603f396f8fcc83e00275a450c6c56b4e2e65fc37290a304000b9efc88ff4019` / `18907efed3b02beb000da2457e1254bb27e759a4d3c25d61e203cae4bd94e3d3` | [산출] progress `COMPLETE`; receipt `CONTENT_VALIDATED_NOT_STANDALONE_AUTHORITY` |

- [산출] 권위 쌍은 **원 H6 terminal journal `IMPLEMENTATION_STOP`을 변경 없이 보존**하고, recovery `COMPLETE` progress와 `RECOVERY_PAIR_REQUIRED` receipt를 함께 요구한다. recovery receipt 단독은 권위가 아니다.
- [산출] 독립 validator는 witness에서 dual-path QC, baseline, 두 P2P estimand, participant 변화, 12 endpoint, bootstrap, 7 LOO, p17/p19 paired를 다시 계산했다. recovery status 명령의 반환은 `COMPLETE`였다.
- [미완성] raw object→selected witness decoder는 단일 frozen decoder에 의존한다(provenance P2). raw decode 독립 parity는 이 권위 쌍으로도 제공되지 않는다.

## 18개 객체 clean count

| # | protocol | participant | phase | clinical n | local-bipolar n |
|---:|---|---|---|---:|---:|
| 1 | TS | p16 | pre | 80 | 83 |
| 2 | TS | p16 | post | 38 | 52 |
| 3 | TS | p17 | pre | 34 | 24 |
| 4 | TS | p17 | post | 12 | 25 |
| 5 | TS | p18 | pre | 60 | 60 |
| 6 | TS | p18 | post | 58 | 58 |
| 7 | TS | p19 | pre | 54 | 54 |
| 8 | TS | p19 | post | 54 | 55 |
| 9 | PB | p17 | pre | 24 | 11 |
| 10 | PB | p17 | post | 25 | 22 |
| 11 | PB | p19 | pre | 58 | 56 |
| 12 | PB | p19 | post | 57 | 56 |
| 13 | PB | p20 | pre | 28 | 133 |
| 14 | PB | p20 | post | 34 | 128 |
| 15 | PB | UC004 | pre | 36 | 35 |
| 16 | PB | UC004 | post | 35 | 32 |
| 17 | PB | UC005 | pre | 39 | 39 |
| 18 | PB | UC005 | post | 40 | 40 |

## 전량 endpoint 산출

표의 `D`, CI, paired 및 LOO는 µV이며 3자리 반올림, `P+`는 6자리 반올림이다. `P+`는 `P(D>0)`이며 p-value가 아니다. LOO 부호열/범위는 7개 값을 압축 표시하고, 바로 아래 상세 표에 전 값을 적는다.

| reference | estimand | window | D | 95% bootstrap interval | P+ | paired p17/p19 | LOO 부호; 범위 |
|---|---|---|---:|---|---:|---:|---|
| clinical | trial-mean | early | 0.613 | [−15.585, 12.194] | 0.574982 | 14.153 | `+-+-++-`; [−3.792, 8.335] |
| clinical | trial-mean | late | 33.643 | [−5.492, 67.315] | 0.954697 | 58.258 | `+++++++`; [20.780, 52.614] |
| clinical | trial-mean | prestim | 2.714 | [−27.167, 31.972] | 0.574539 | 7.186 | `-++-++-`; [−8.198, 16.537] |
| clinical | mean-waveform | early | 1.452 | [−7.598, 11.405] | 0.645477 | 1.618 | `+++++-+`; [−1.742, 5.220] |
| clinical | mean-waveform | late | 36.196 | [10.020, 72.323] | 0.999512 | 56.411 | `+++++++`; [16.688, 46.095] |
| clinical | mean-waveform | prestim | 14.917 | [−1.313, 39.126] | 0.956741 | 33.933 | `+++++++`; [0.738, 19.903] |
| local-bipolar | trial-mean | early | −10.002 | [−21.775, −0.110] | 0.023239 | −13.200 | `-------`; [−14.427, −3.607] |
| local-bipolar | trial-mean | late | 2.532 | [−21.851, 23.595] | 0.604553 | 12.353 | `--++++-`; [−4.040, 14.489] |
| local-bipolar | trial-mean | prestim | −4.517 | [−27.070, 27.905] | 0.340454 | −30.146 | `-+-++--`; [−16.064, 4.399] |
| local-bipolar | mean-waveform | early | 8.243 | [−3.528, 18.562] | 0.918594 | 3.695 | `+++++++`; [3.952, 12.884] |
| local-bipolar | mean-waveform | late | 2.882 | [−26.969, 50.748] | 0.481934 | 42.617 | `----+++`; [−10.446, 14.808] |
| local-bipolar | mean-waveform | prestim | 21.098 | [−4.489, 62.128] | 0.920929 | 55.295 | `+-+++++`; [−1.706, 27.199] |

### Participant post−pre 변화 및 전체 LOO

TS 변화 순서는 `p16,p17,p18,p19`, PB 변화 순서는 `p17,p19,p20,UC004,UC005`다. 각 행은 [산출]이며 µV이다.

| reference / estimand / window | TS 변화 | PB 변화 | LOO: p16, p17, p18, p19, p20, UC004, UC005 |
|---|---|---|---|
| clinical / trial-mean / early | 1.853, 4.868, 4.932, 3.753 | −5.172, −14.513, 34.130, 11.262, −9.513 | 1.279, −1.829, 0.252, −3.792, 8.335, 2.618, −2.575 |
| clinical / trial-mean / late | 58.397, 33.024, 32.601, 1.321 | −51.510, −30.660, 20.111, 73.576, −23.052 | 24.623, 20.780, 33.221, 36.560, 39.248, 52.614, 28.457 |
| clinical / trial-mean / prestim | 44.359, −4.561, 8.725, −2.032 | 14.647, −35.612, 64.203, 18.379, −17.071 | −8.198, 9.543, 3.680, −3.865, 16.537, 5.081, −3.781 |
| clinical / mean-waveform / early | 1.506, 34.349, −2.694, 1.271 | 36.128, −3.745, 7.535, −5.623, 1.483 | 3.820, 0.115, 5.220, 1.173, 1.547, −1.742, 0.034 |
| clinical / mean-waveform / late | 42.267, 49.768, 22.300, 2.847 | −57.636, −2.570, 8.342, 18.136, −0.775 | 31.872, 16.688, 38.528, 46.095, 40.007, 42.455, 37.728 |
| clinical / mean-waveform / prestim | 1.459, 52.471, 11.019, 0.729 | −7.144, −7.523, 13.567, 9.176, −0.562 | 19.903, 0.738, 16.717, 17.890, 17.933, 16.835, 14.400 |
| local-bipolar / trial-mean / early | 5.843, −9.974, −2.574, 4.351 | 22.478, −1.700, 13.622, 8.704, 3.962 | −12.146, −3.607, −9.340, −14.427, −8.949, −10.179, −11.364 |
| local-bipolar / trial-mean / late | 22.531, −2.683, 2.234, −0.378 | −28.377, 0.609, 14.912, 50.720, −23.397 | −3.169, −2.583, 3.596, 3.896, 5.537, 14.489, −4.040 |
| local-bipolar / trial-mean / prestim | 37.889, 8.334, −2.227, −22.430 | 49.496, −3.301, 31.260, 8.365, −36.278 | −15.349, 4.399, −1.978, 1.454, 0.821, −4.903, −16.064 |
| local-bipolar / mean-waveform / early | 11.691, 11.943, −2.001, 13.241 | 23.339, −5.545, 0.841, −16.686, 0.430 | 7.252, 12.884, 11.816, 5.230, 8.334, 3.952, 8.231 |
| local-bipolar / mean-waveform / late | −5.174, −89.006, −6.331, 8.249 | −167.180, 1.188, 13.801, 21.759, 0.696 | −3.082, −10.446, −2.696, −0.773, 12.819, 14.808, 9.543 |
| local-bipolar / mean-waveform / prestim | 11.656, 28.500, −8.435, 0.422 | −76.996, −4.672, −2.206, 11.342, 7.220 | 19.891, −1.706, 26.589, 25.734, 23.812, 27.199, 26.169 |

## 주장 상태 및 금지 경계

- [산출] clinical primary는 `D=33.643 µV`, 95% 기술 bootstrap interval `[−5.492, 67.315] µV`, `P(D>0)=0.954696655`, p17/p19 paired `58.258 µV`다. 7개 LOO는 모두 양수다.
- [경험식: SAME_PUBLIC_DATA_POSTHOC] 위 primary와 나머지 11개 결과는 동일 공개자료 7명의 사후 기술적 author-intended measurement emulation 결과다. 독립 split/holdout은 없다.
- [산출] clinical late 결과와 local-bipolar late 결과는 일치된 endpoint 방향을 제공하지 않는다: local-bipolar trial-mean late `D=2.532 µV` (interval `[−21.851, 23.595]`), mean-waveform late `D=2.882 µV` (interval `[−26.969, 50.748]`). clinical primary를 local-bipolar sensitivity가 veto하지 않는 것은 사전 고정 규칙이다.
- [산출] controls/sensitivities에는 방향 불일치가 있다. 예: local-bipolar trial-mean early `D=−10.002 µV`, local-bipolar mean-waveform prestim `D=21.098 µV`; 모든 12개 endpoint를 위에 보존했으며 결과 뒤 threshold/window/reference/estimand를 바꾸지 않았다.
- [미완성] exact MATLAB/FieldTrip/`fitlme` replication은 이 결과로 충족되지 않는다(저자 archive PB 호출 결함, FieldTrip commit 미고정, MATLAB model engine 부재).
- [미완성] independent cohort 또는 independent data split confirmation은 없다. 따라서 causal stimulation effect, population/general-population inference, memory mechanism, consciousness mechanism을 주장할 수 없다.
- [미완성] `CE_DELTA=NONE`: CE 항·상수·뇌 알고리즘을 새로 적합하지 않았으며, 이 원장은 CE 또는 AGI의 증명이 아니다.
- [예측] 이 run에서 새 예측을 등록하거나 검증하지 않았다.
- [금지] 본 원장을 `bootstrap p-value`, causal proof, population proof, memory/consciousness proof, CE proof 또는 AGI proof로 재표기하지 않는다.

## 동결 메모

- [산출] 본 파일은 recovery 완료 artifact와 원 `raw_result.json`에서 read-only로 추출·대조한 논문용 claim map이다. 수치, status, status-label, threshold, window, reference, estimand 또는 claim ceiling을 이후 논문 작성 중 수정하지 않는다.
