# BA-OBS-HPC1 최종 보고서 — 실제 인간 해마 iEEG raw 재현의 측정 aperture 중단

Status: COMPLETE

Scientific disposition:
`STOP_MEASUREMENT_APERTURE / ACTUAL_RAW_INTEGRITY_VERIFIED_ONLY /
NO_ENDPOINT / NO_BIOLOGICAL_VERDICT / NO_RETRY_IN_THIS_VERSION`

## 질문과 판정

이 run은 공개 인간 iEEG에서 theta trough에 동기화한 lateral temporal cortex 자극이
phase-blind protocol보다 해마의 late SEP 변화를 크게 만드는지, clinical reference와
사전 고정 local bipolar reference에서 raw-derived로 다시 계산하려 했다. 자료는
OpenNeuro `ds006065` v1.0.0의 일곱 epilepsy-surgery participant와 18개 pre/post
BrainVision EP object였다.

판정은 생물학적 양성도 음성도 아니다. 사전 고정한 artifact·clean-trial aperture가
두 번째 객체의 첫 reference에서 실패해 endpoint 계산 전에 중단됐다. 계약의 falsifier가
의도대로 작동했으므로 cohort를 줄이거나 threshold·contact·window를 바꾸지 않았다.

## 실제 raw에서 확인된 것

18개 객체 전부에 대해 raw 접근 전에 annex SHA-256/size, S3 version ID/ETag,
BrainVision header hash, channel order·resolution·unit, sampling interval, trial-block identity,
고정 contact index를 잠갔다. 이 source lock의 SHA-256은
`0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58`이다.

attempt 1에서 실제로 완결된 raw object는 TS p16 `eppre` 하나다.

- object: `sub-p16/ieeg/sub-p16_task-eppre_ieeg.eeg`
- expected/observed SHA-256:
  `5c19f0453e114ffef850adbd95b6a05eab4bd72158f70abd8180a77fe41ef6cc`
- expected/observed bytes: `60,480,000`
- S3 version ID: `sVZSXO4kOS4MOrAF06Uzz5sAoSaE1vas`
- ETag: `"92cb4fc9003231b1fc907c67d02cee42"`
- header SHA-256:
  `cec6e1bc207941f43a5f708a0734f77da86c7ec5a2c5f5c35f61ab8a998c38dc`
- frozen clinical/local-bipolar contact indices: `141/142`

따라서 적어도 이 객체에 대해서는 public raw payload가 release annex pointer와 byte 단위로
동일하고, 고정 BrainVision multiplexing·contact aperture로 읽혔다는 provenance 주장이
성립한다. 이는 신경생리 효과의 증거가 아니라 실제 자료 무결성의 산출이다.

## 중단 지점

audit-approved raw 명령은 session `75271`에서 exit code `1`로 끝났다.
`artifacts/raw_progress.json`은 `ATTEMPT1 / RAW_STOP`이며 SHA-256은
`ce502e77ff83186359259e6129b06d6580c07187740a945a14c7310687a76934`이다.

첫 객체 다음의 고정 순서는 TS p16 `eppost`, clinical reference였다. 전체 객체를 읽은 뒤
`_clean_summary`가 `STOP_MEASUREMENT_APERTURE: clean-trial aperture failed`를 발생시켰다.
실패가 completion receipt 전에 일어나 clean count 자체는 남지 않았다. 이 때문에 어느
threshold가 통과할지 추정하거나 선택할 근거도 없다.

`raw_result.json`은 생성되지 않았다. 따라서 late/early/prestimulus P2P, participant-equal
$D$, participant-cluster interval, LOO, paired sensitivity, reference concordance,
published-model direction, status lattice의 실제 결과는 전부 부재한다. Nature Source Data도
열지 않았다.

## 두 실행 시도의 지위

- attempt 0: `ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`. baseline과 artifact 판정 순서가
  계약과 달랐음을 정적 감사에서 발견했고, endpoint receipt 없이 해당 process만 종료했다.
- attempt 1: 수정 코드·고정 source lock·독립 구현 감사·status audit를 모두 통과한 유일한
  허용 raw one-shot. `STOP_MEASUREMENT_APERTURE`로 종료됐다.

attempt 1 뒤 같은 판본의 재실행은 금지된다. 이 중단은 논문의 published result를 반박하지
않으며 CE history/reference robustness를 지지하지도 않는다.

## 형식 지위와 주장 상한

- 실제 raw object identity: **[산출: verified]** — 한 completed object에서 expected와
  observed full-object SHA-256/size가 일치했다.
- 18-object source/header aperture: **[산출: metadata verified]** — raw 전 고정 완료.
- theta-synchronized late SEP 효과: **[미완성: unmeasured in this run]**.
- CE history/reference robustness: **[미완성: no endpoint]**.
- 건강인 일반화, 기억 행동, 해부학적/축삭 경로, Riemannian metric, 의식·자아·해마 hash,
  AGI: **주장하지 않음**.

## 재개 조건

재개하려면 별도 successor contract가 필요하다. successor는 이 run에서 남지 않은 실패
clean count를 추정해 threshold를 고르면 안 된다. 먼저 저자 코드와 일치하는 artifact/QC
연산을 공개 코드만으로 고정하고, endpoint와 분리된 QC-only receipt를 설계하며, 파일별
clean count와 실패 reference를 항상 직렬화해야 한다. 그 뒤 새로운 audit와 명시된 실행
budget을 통과해야만 endpoint stage를 열 수 있다.

## 재현과 보존

- 구현: `examples/brain/ba_obs_hpc1_raw_replication.py`
- focused fixture: `tests/test_ba_obs_hpc1_raw_replication.py` — `4 passed`
- source receipt: `artifacts/source_lock.json`
- terminal raw receipt: `artifacts/raw_progress.json`
- 구현/검증 기록: `30-implementation.md`, `31-validation.md`

`raw-one-shot` 명령은 이 판본에서 다시 실행하면 안 된다. 안전하게 재실행 가능한 것은
focused fixture와 source-lock의 offline canonical/hash 검사뿐이다.
