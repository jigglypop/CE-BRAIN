# 형식·상태 감사 — 구현 전 endpoint authority

Status: COMPLETE

Gate: PASS

Authorization: ENDPOINT_FULL1_ONLY

00/10/11/12 레인은 모두 COMPLETE이며, 구현 전 P0/P1은 남지 않았다.

선행 Stage-E의 endpoint-authority P0는 두 가지였다. 첫째, 저장된 trialwise P2P가
clean source trial에서 독립 재구성되지 않았다. 둘째, bipolar bundle 누락을
raw-derived availability에서 권위 있게 판정하지 못했다.

선택된 R1 경로는 이를 구조적으로 해결할 수 있다. `source_witness.npz`는 18개 고정
source object에서 selected QC tensor와 rejected trial을 포함한 clinical·bipolar
trace를 보존한다. 독립 validator는 witness에서 corrected dual-path QC mask, baseline,
trialwise P2P, mean-waveform P2P, participant contrast, bootstrap, LOO, paired sensitivity를
다시 계산해야 한다. clinical endpoint는 고정된 `q[:,0,:]`이며, bipolar availability는
18개 cell의 raw-derived keep mask에서 all-or-none으로 판정한다.

최종 구현 안정 스냅샷에 대해 수학·상태·적대적 구현 감사가 모두 `PASS`를 반환했다.
focused validation은 `7 passed`였고 compile 및 build gate도 통과했다. 실행 잠금
`aefbec437279519bd568e77ffc0f5a01b1795b24843acb178abfdc9a1f57aa6b`는 producer
`cfe53970f2d88473c946eb20feb1976fe5926f108899ace5cc88d36f4ca065e8`, validator
`40e78a2491c371fb638f21e19ea6e8ff2caff414010c409a7a7475f54a432197`, tests
`2142131018ccbd6ad7653229dcac0345bba31326a816b6186c93152f67a326d2`를 고정한다.
이전의 claim metadata 및 비-predecessor source provenance 연동 위조는 이제 거부된다.
따라서 동시 실행 없이 단일 통제 프로세스의 raw/network `ENDPOINT_FULL1` 한 번만
승인한다. 실행 뒤에는 별도 offline validator가 COMPLETE receipt를 다시 승인해야 한다.

raw-to-witness 추출 자체의 독립 decoder parity는 provenance P2 ceiling이다. 따라서
이후 결과의 허용 주장 범위는 witness-backed technical endpoint이며, 동일 공개자료의
사후 기술분석이다. exact MATLAB/FieldTrip/`fitlme` replication, causal stimulation
effect, general-population inference, memory, consciousness, CE 또는 AGI 증거로 승격하지
않는다. R3 literal parity는 계속 `BLOCKED`다.
