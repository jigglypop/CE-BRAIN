# Allen: 실제 source 전압과 target 전류를 결합할 새 기록

2026-09-20. [VC 명령 이력 비교](allen_vc20hz_command_history_findings.md)의 다음
질문은 source 명령과 실제 발화를 구별할 수 있는 기록을 확보하는 것이다. 이번에는
기존 후보 실험의 모든 electrode를 조회해 **IC source·VC target의 동시 기록**을
찾고, 세포·연결·pulse·반응 ID와 QC를 결합했다. 원파형이나 이력식은 아직 적합하지 않았다.

## 관측 조합을 실제 DB에서 확인했다

기존 pair별 조회에서 mixed mode가 없었던 결과는 그대로다. 그 결과를 실험의 다른
electrode 조합에 확대하지 않고, 이미 후보였던3338·3340·4863의 전체 sync recording을
조회했다. 공식 MIES는 headstage별 mode를 설정할 수 있지만 이것만으로 Allen의
실제 mixed 기록을 입증할 수는 없다. 이번 존재 판정은 released medium DB의 관측값이다.
[MIES 설정](https://alleninstitute.github.io/MIES/file/_m_i_e_s___acquire_data_8ipf.html).

| 실험 | 전체 시행 | IC 기록 | VC 기록 | mode 미상 기록 | 혼합 시행 |
|---|---:|---:|---:|---:|---:|
| 3338 | 110 | 637 | 80 | 0 | 0 |
| 3340 | 106 | 570 | 60 | 0 | 0 |
| 4863 | 103 | 430 | 74 | 0 | 24 |

3340의 시행104는 recording 자체가0개라 불완전 coverage로 남겼다. 이것을 기록은
있지만 mode가 미상인 경우와 합치지 않았다. 4863의 시행64–87은 매번 IC4개와 VC1개다.
IC devices0/3/5/6에서 VC device1로의96개 방향 후보가 있고, 양쪽 recording QC가
통과한 조합은64개다. 동일 시행·고유 recording/electrode를 확인하며 QC 탈락도 보존했다.
이 세 실험에서의 조사이며 전체 Allen 자료에 대한 전수 판정은 아니다.

## 네 연결을 모두 보존한 pulse 결합

실험은 `1630015960.701`, 표적은 electrode38822/cell24115/device1이다.
원장에 있던 small DB와 medium DB의 pair ID·실험·pre/post cell을 대조했다.
다섯 세포는 모두 VisP L5의 ex 표기다. 다음 네 방향을 보고된 연결 유무와 관계없이
전부 조사했다. `has_synapse=0`은 보고된 연결이 없다는 표기이며 연결 부재의 증명이 아니다.

| Source device / cell | Pair | 보고된 synapse | Pulse / response | count1 + 유한 발화시각 | 양 recording·반응 ex QC + 해당 시각 |
|---|---:|---|---:|---:|---:|
| 0 / 24114 | 121535 | 없음 | 288 / 288 | 215 | 155 |
| 3 / 24117 | 121551 | 없음 | 288 / 288 | 209 | 142 |
| 5 / 24118 | 121558 | 없음 | 288 / 288 | 196 | 141 |
| 6 / 24119 | 121566 | ex, synapse2989 | 288 / 288 | 263 | 172 |

각 방향의24개 source recording은 모두 recording QC를 통과했고 공통 target은
16/24 통과했다. QC 통과와 실제 막전압 제어·시냅스 전류 식별은 별도 조건이다.
Target의 저장 baseline potential은 전부 약−54.9948mV, baseline current는
약−1.398..−0.197nA다. 이는 PCR의 baseline 값이며 정확한 command setpoint나
pulse 중 실제 막전압으로 대체하지 않는다. Access/TP·보상 설정도 다음 결합에서 확인한다.

## 검출 수, 시각과 QC 열을 구별한다

1,152개 pulse의 `cell_id`와 `qc_pass`는 모두 NULL이다. 처음 구현은 pulse cell ID가
있어야 한다고 요구해7개 결손 블록을 수집한 뒤 중단됐다. 유효한 캐시는 보존하고
실제 recording→electrode→cell 및 pair 대응을 사용하도록 수정했다. Non-NULL의
다른 cell ID는 여전히 거부하고, NULL의 수를 결과에 명시한다. 결과를 출력하기 전에
실패했으므로 성공한 이전 분석을 덮어쓰지 않았다.

Pulse QC를 임의로 pass로 채우지 않는다. 해당 필드까지 모두1을 요구한 엄격한
카운트는 네 쌍 모두0이며 이는 pulse가 모두 실패했다는 뜻이 아니다. 위 표는 양쪽
recording QC, response ex QC, 저장 count1 및 유한 first-spike time을 결합한 별도
관측 조건이다. 두 집계를 모두 JSON에 남겼다.

[참조 producer](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/pipeline/multipatch/dataset.py)는
StimPulse 생성 때 qc_pass를 채우지 않고 검출 목록에서 n_spikes와 first-spike time을
채운다. Response는 발화가 없어도 생성하며,
[response 처리](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/data/data.py)의
QC용 spike 수는0/1로 축약된다. 따라서 response QC만으로 단일 발화를 보증하지 않는다.

실제 DB에는 count1이1,151개, count0이1개다. 그중 count1·유한 시각은883개,
count1·시각 NULL은268개다. Count0·시각 NULL은 시행86의 source device6 pulse8이다.
`n_spikes`는 실제 DB schema에서 기본값이 없는 nullable INTEGER였다.
이 차이를 SQLite 기본값으로 설명하지 않는다. 저장 검출값1과 유한 시각 역시 실제로
정확히 한 AP가 있었음을 보증하지 않으므로 source 원파형 확인이 필요하다.

참조 dataset.py의 ‘최대 한 발화 검출’ 주석과 달리, 별도 확인한 neuroanalysis
구현은 여러 event를 반환할 수 있다. 그 commit이 당시 DB를 생성한 dependency라는
연결은 확립되지 않았으므로 주석이나 현재 detector 비교로 과거 파형을 판정하지 않는다.

## 조건이 바뀐 뒤의 예측을 시험할 수 있는가

| 시행 | protocol | 초기8개 내부 간격 | Pulse7→8 onset 간격 |
|---|---|---|---|
| 64–76 | Y4_SRecovery_50H | 20ms | 126.52/251.52/501.52/1001.52/4001.52ms |
| 77–81 | Y5_SPulsTrn_20Hz | 50ms | 251.52ms |
| 82–87 | Y6_SPulsTrn_100H | 10ms | 251.52ms |

각 시행은 초기8개 뒤 회복4개다. 표의 긴 간격은 onset 사이 값이므로 off-gap과
같지 않다. 예컨대 저장 pulse 길이1.52ms를 포함한251.52ms onset 간격의 off-gap은
250ms다. 주파수와 시행 순서·세포 상태가 결합돼 있으며 독립 주파수 개입으로
단정하지 않는다. 현재 단계에서 반응 진폭을 보고 학습·평가 시행을 고르지 않았다.

다음은 이24개 시행의 실제 source 전압·target 전류·명령·공통 raw clock과 측정
상태를 결합하는 것이다. 먼저 AP와 검출 시각, 앞선 자기 자극·다른 세포 자극,
holding·access·보상·포화·관측 가능한 baseline을 확인한다. 그 뒤 같은 관측 예산에서
고정 전달과 과거 활동에 따른 변화의 보류 예측을 비교한다. 이 자료의 존재나172개
메타데이터 후보를 가소성·전도도·리만 계량의 확립으로 세지 않는다.

## 재현과 보존

- [Mode source](../verify/Q-NPF-04/allen_synphys/mixed_clamp_inventory.py),
  [검사](../tests/test_mixed_clamp_inventory.py),
  [결과](../verify/Q-NPF-04/allen_synphys/mixed_clamp_inventory_result.json): 6개 검사 통과,
  query plan328개에 SCAN0. 새37블록·2,424,832바이트.
- [Pulse source](../verify/Q-NPF-04/allen_synphys/mixed_clamp_pulses.py),
  [검사](../tests/test_mixed_clamp_pulses.py),
  [결과](../verify/Q-NPF-04/allen_synphys/mixed_clamp_pulses_result.json): 수정 후9개 검사 통과,
  query plan129개에 SCAN0. 새8블록·524,288바이트.

두 단계 모두 기존 frozen base/VC overlay를 변경하지 않고 별도 overlay를 쓴다.
Offline에서 결손 위치를 확인한 후 ETag·If-Match·206·Content-Range·수신 크기를
검사해 부족한 범위만 받았다. 각 overlay의8MiB 상한을 지켰다. 원격 medium DB는
11,125,997,568바이트이며 전체를 다운로드하지 않았다. 마지막 pulse 실행의 추가
65,536바이트와 앞선 실패 실행458,752바이트를 합쳐 누적524,288바이트로 기록한다.

Mode JSON SHA는 `0852aaa1ea1270965d25e2315d9d05a8d1b69e8340ba848196fad11854370cee`,
pulse JSON SHA는 `f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7`다.
정확한 source/test/manifest/block 해시와 위치는 [데이터 원장](data_registry.md)에 보존한다.
지정 실행기는 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`이며
각 스크립트는 기본 offline이고 기존 결과를 덮어쓰지 않는다.

## 후속 관측

[원파형·측정 상태 결합](allen_mixed_clamp_waveform_findings.md)에서240배열과120개
recording 상태를 확보했다. 시각 NULL인 count1 사건268개 모두 실제 전압의0mV 상향
통과가 있었으며 유한 시각883개는 raw 최대 상승 시각과 한 표본 이내였다. 이 후속
진단과 기존 메타데이터172개 조건은 구별해 보존한다. PSC·이력 효능·계량 변화는
아직 적합하지 않았으며 다음 단계는 작동점과 자기 자극 이력을 포함한 보류 예측이다.
