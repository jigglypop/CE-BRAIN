# Allen 20Hz VC: 측정 상태와 두 시각 정의의 결합

2026-09-19 후속. [전체 입력](allen_vc20hz_inputs_findings.md)의 실험
`1574292898.139`, 0–6시행에 대해 `recording → patch_clamp_recording → test_pulse`를
결합한다. 목표는 전기적 이력 모형에 앞서 입력·작동점·측정 조건을 정의하는 것이다.
전달 반응을 새로 적합하거나 해마의 사건 검색과 이 기록을 동일시하는 단계는 아니다.

## 자료 확보와 식별

기존 medium DB 캐시는 1,479블록·96,927,744바이트이며 manifest SHA는
`8f7f88ae8b62f67312c9f34616bc2feb280cc7b24db62a59b5b8a7c44d057bab`다.
원장과 전체 블록의 크기·해시를 대조한 뒤, indexed recording 조회에 없던
`382337024–382402559`의 65,536바이트만 별도 overlay에 받았다. 기존 캐시는 유지했다.
원격 전체 11,125,997,568바이트를 내려받지 않았다. 새 overlay 상한은 128KiB다.
HEAD의 크기·ETag, GET의 If-Match·206·Content-Range를 확인하고 본문을 제한해서 읽는다.

- overlay: `data/external/allen_synphys_r21/vc20hz_medium_ranges/1574292898.139`
- block SHA: `f87d4129e527a3f2f5a7dacac3905bcd8d6d0158c10e40594dc06704c0516321`
- manifest SHA: `f447289e24e4eccf2b33333ac7bbe0ec97a9c73f42c7b628df0587c390f53325`
- 원격 ETag: `"d954cbad0d7c7b0002bf3a2879e40e90-1327"`

experiment3337의 sync_rec72618–72624와 electrode26623/26625/26626을 인덱스로
조회한다. 순서대로 device2/4/5이며 raw AD2/AD8/AD9와 DA2/DA4/DA5가 대응한다.
PCR과 TP는 LEFT JOIN하여 결측을 버리지 않는다. 실행계획에 table/index SCAN이
있으면 거부한다. Cell 테이블의 추가 다운로드는 하지 않았다.

## 확인한 명령과 측정 상태

21개 recording은 모두 VC이며 최소 QC를 통과했다. Holding Offset과 DB baseline
potential은 모두 같다. DB train을 전개한 252개 양의 pulse는 raw command와
시작 오차 최대5.103µs, 길이 오차10µs, 진폭 오차7.125nV 이내로 맞는다.
현재 100kHz 입력의 한 표본은10µs다. 판독 코드는 양자화에 두 표본의 허용치를 둔다.

| 세포/device | Holding 명령 mV | 시행 전체 quiet 전류 중앙값 pA | Access R 범위 MΩ | Input R 범위 MΩ |
|---|---:|---:|---:|---:|
| 2 / AD2 | −69.983535 | −274.969991 | 42.105–44.321 | 184.334–193.588 |
| 4 / AD8 | −70.013717 | 1.243749 | 45.455–53.691 | 166.549–175.265 |
| 5 / AD9 | −70.016384 | −40.033747 | 38.462–42.440 | 171.755–179.046 |

DA의 +60/+120/+150mV는 이 holding 위에 더하는 상대 명령이다. 따라서 양의 plateau
명령은 약−10/+50/+80mV다. 실제 막전압이나 source AP를 관측한 값으로 쓰지 않는다.
세포2→4→5의 자극 블록은 순차이며 서로 겹치지 않는다. 각 블록은20Hz 8회 뒤
250ms off-gap을 두고20Hz 4회다. 블록 사이에도250ms off-gap이 있다. Source인5번
자극 전에 target 자신의 자극이 있으므로 그 잔류 상태를 반응 모델에 포함해야 한다.

TP21개는 동일 recording/electrode에 연결되고 분석창 `[0,2500)`이 실제 음의 command
`[750,1751)`를 포함한다. 이 index는 TP 분석창이며 음의 펄스 자체 경계가 아니다.
실제 −10mV pulse의 시작·길이·진폭도 stim_meta와 일치한다. 따라서 이번에는 embedded
TP를 확인했지만, 일반적으로 nearest TP의 recording_id 일치만으로 이를 판단할 수 없다.
[공식 reader](https://github.com/AllenInstitute/neuroanalysis/blob/bbe61c4047de592984b4e7089d0803a7d4101c7f/neuroanalysis/miesnwb.py)는
inserted TP를 우선하고 없으면 labnotebook 시각과 가장 가까운 TP를 택하며 최대 시간차를 제한하지 않는다.

## 전위 보정의 정확한 입력

[공식 producer](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/pipeline/multipatch/dataset.py)의 식은

\[
\widehat V_{baseline}=V_{holding}-R_{access,lowpass}\,I_{TP,baseline}.
\]

전류는 **test_pulse.baseline_current**다. 시행 전체 quiet 구간의 대표값인
`patch_clamp_recording.baseline_current`와 다르다. TP 전류를 사용한21개 재계산은
저장 `access_adj_baseline_potential`과 float 수준에서 정확히 일치한다.
초기 구현은 두 baseline current를 혼동해 최대0.344514mV 차이가 났다. 이를 판본·정밀도
문제로 결론짓지 않고 producer 원문으로 바로잡았으며, 검사에서 두 전류를 다르게 두어
다시 혼동하면 실패하도록 했다. 과거 고정 산출물은 수정하지 않았다.

이 식은 baseline IR-drop 추정이다. Pulse 중 실제 막전압, 전도도나 하드웨어 series
compensation을 재현한 식은 아니다. 이 DB table에는 해당 compensation 설정이 없다.
21행의 capacitance와 time_constant는 전부 NULL이므로 막 C·τ의 측정값이 확보됐다고
하지 않는다. QC는 최소 전류·잡음 검사이며 큰 access R이나 세포 건강을 보증하지 않는다.
정의는 [공식 QC](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/qc.py)에 따른다.

`access_resistance_lowpass`는 electrode별 유효 TP들의5점 median filter이며 미래 TP도
포함할 수 있다. 시행 전체 quiet current도 미래 표본을 사용할 수 있다. 둘은 이 단계의
측정 진단용이며 다음 인과적 반응 예측의 시행 시작 시점 입력으로 자동 허용하지 않는다.

## DB 시각과 원파형 시각을 구별한다

0시행을 기준으로 DB 시각 간격에서 NWB 첫 표본 간격을 뺀 값은
`[0, −37, −56, −41, −68, −69, −43]ms`다. 각 시행 세 device의 차이는 동일하다.
처음 구현은10µs 이내 일치를 요구하여 여기서 중단됐다. 이후 두 필드의 생성 경로를
확인했다. DB `recording.start_time`은 reader의 labnotebook `TimeStamp`를 쓰며,
현재 입력의 NWB `starting_time`은 `/session_start_time` 기준 첫 표본 시각이다.

[MIES 노트 정의](https://alleninstitute.github.io/MIES/labnotebook-descriptions.html)는
TimeStamp를 노트 entry 작성 시각으로 설명하고,
[NWB1 정의](https://alleninstitute.github.io/MIES/IPNWB/doc/nwb1.html)는 표본 시각을 별도로 둔다.
기존 [고정 raw 결합 검산](../verify/Q-NPF-04/allen_synphys/raw_binding_validation.json)에서도
노트 시각−첫 표본 시각은 `[5.258,5.221,5.202,5.217,5.190,5.189,5.215]s`로,
위 상대 차이와 일치한다. 상수 timezone 차이는 상대 차이에서 소거된다.

따라서 이를 신경 전달 지연이나 clock drift로 해석하지 않는다. 실제 전류·명령6채널의
NWB clock은 시행 안에서 정확히 공통이다. 반응 정렬과 시행 간 시간 계산은 이 clock을
사용하고 DB timestamp를 대입하지 않는다. 최종 결과에는 상대 시각 잔차·불일치 flag를
그대로 보존한다. 노트 작성 지연이 변하는 구체적 원인은 추가로 식별하지 않았다.

## 검증과 다음 조건

[소스](../verify/Q-NPF-04/allen_synphys/vc20hz_measurement_state.py),
[검사](../tests/test_vc20hz_measurement_state.py),
[결과](../verify/Q-NPF-04/allen_synphys/vc20hz_measurement_state_result.json)를 보존한다.
입력 JSON·NPZ와 의존 소스의 해시를 확인하고 기존 결과 덮어쓰기를 거부한다.
초기 in-memory fixture의 foreign key affinity가 실제 DB와 달라 index scan이 선택돼
검사가 실패했다. Fixture를 실제 INTEGER 타입으로 고쳤으며 scan 거부는 유지했다.
의존 SHA 전사 오류도 네트워크 시작 전에 차단돼 수정했다. 두 경우 새 결과·다운로드는 없었다.
시각 동일성 검사는 이후64KiB 수집 뒤 중단됐고, 확보한 overlay를 다음 offline 실행에 재사용했다.

실행기는 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`다.
`pytest tests/test_vc20hz_measurement_state.py -q`의10개 검사가 통과한 뒤
`python verify/Q-NPF-04/allen_synphys/vc20hz_measurement_state.py`를 offline 실행했다.
Python3.11.9에서21행을 만들었고 최종 실행의 추가 다운로드는0바이트다. 독립 검산에서
QC·12개 양의 pulse·embedded TP가21/21 확인됐고 IR 보정 잔차는 전부0V였다.
DB/raw 시각 불일치18건은 그대로 남고 다른 진단 문제는 없었다.

| 파일 | 바이트 | SHA-256 |
|---|---:|---|
| 결과 JSON | 332781 | `6880651a236236d1f80576b228f03131b34d158f454541e31dae07ac82ab3e85` |
| 소스 | 14745 | `055db380bf1760661d96c95aa9ea479f1bba254952aa4d4dc4bf9cbf88810444` |
| 검사 | 6139 | `66e761eb4eb280f8c3f947e22aa2bde2a58d7c38555db46e572dc142cba6a121` |

소스·검사·결과는 `allen-synphys-analysis/vc20hz-measurement-state-v1`,
신규 블록·manifest는 `allen-synphys-ranges/r2.1-vc20hz-medium-overlay-20260919`에 등록했다.
문서5개와 등록 파일5개의 링크·해시를 확인했고 기존 문서 문제38개 대비 추가 문제는0개다.

다음 전기 축은 이 raw clock과 순차 명령 위에서 pre-source 관측 상태·자기 자극 잔류·
측정 회로를 포함한 반응 예측을 정하는 것이다. Hardware compensation과 관측 가능한
막 상태를 먼저 확인하고, 설명되지 않은 전류를 바로 시냅스 전달·이력 가소성으로 이름 붙이지 않는다.
해마 축의 [내용 전이와 사건 구별](hippocampal_story_transfer_findings.md)은 별도 실제 자료의
근거로 유지한다. 두 축을 공통 CE 기전·리만 계량·검색 방향성으로 연결하는 일은 아직 남아 있다.

## 2026-09-20 후속: 원본 보상 설정과 조건부 전류 예측

위의 DB table에 없는 hardware compensation은 원본 NWB 수치 노트에서 별도로
확인했다. Rs와 whole-cell compensation은21/21 Off다. Acquisition comment만으로는
3행 확인·18행 미상이어서 두 출처를 분리했다. 실제 막 C·τ 결측은 그대로이며,
보상 capacitance 설정을 막 측정값으로 대체하지 않는다.

[명령 이력 비교](allen_vc20hz_command_history_findings.md)는 직전 전류로 기준선을
정하고 [2,40)ms 파형을 예측했다. 같은 명령의 초기 구간에는 작은 개선이 있었지만
회복과 다른 조건에서 이력 항의 우위가 유지되지 않았다. 네 τ 선택 모두 후보 하한50ms다.
이 결과와 새 관측 조건을 후속 원장에 보존하고 이전21행 DB 결합은 수정하지 않았다.
