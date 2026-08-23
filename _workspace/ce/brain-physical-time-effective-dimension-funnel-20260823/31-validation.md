# BA-SRM8 검증 기록: 후보 퍼널의 유효 범위와 중단

Status: COMPLETE

Execution outcome: STOPPED (`SYNTHETIC_DGP_STOP / REAL_ENDPOINT_UNOPENED`)

Date: 2026-08-23

## 검증의 의미

이 run은 식을 많이 시도하되, 비싼 행동 검증을 열기 전에 수학적 결함·관측 부족·합성 생성기 결함을 빠르게 구분하도록 설계했다. 따라서 F0와 F1의 통과는 오직 고정된 관측 연산자가 고정된 작은 합성 입력에서 fail-closed 규칙을 지켰고 clean/noisy 관측 사이의 $Q$를 복원했다는 뜻이다. 이 결과를 생물학, 의식, AGI, 시냅스, 방향성 loop, 해마 기능에 대한 증거로 읽을 수 없다.

F0-v3는 48개 manifest 후보를 검사했다. 12개 short-memory 후보는 `ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF`로 멈췄고, 36개는 PSD·인과성·무차원성·zero/nonfinite fail-closed 및 runtime gate를 통과했다. `ABSTAIN`은 정보가 부족하다는 판정이며 `INVALID_KILL`이나 성능 실패가 아니다. F0-v3 receipt의 SHA-256은 `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7`이다.

F1-v6에서는 네 개 고정 seed 모두에서 clean truth와 estimate가 동일한 관측 mask, $D$, 시계, 후보 규칙을 공유했다. promoted 32개는 중앙값 $\operatorname{NMAE}^Q$가 0.03946--0.05940, 중앙값 Spearman이 0.93657--0.98688이었다. 네 후보는 F1 gate를 통과했지만 동결된 32개 예산 상한 때문에 `DROPPED_BUDGET`이 되었으며, 12개는 F0와 같은 사유로 abstain이었다. F1-v6 receipt는 `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca`, runner는 `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7`이다.

이 두 단계의 정정 이력도 결과의 일부다. attempt-00과 F1-v2는 numerical rank, usable-list 70% 보정, clean/noisy 관측 불일치, range-NMAE 때문에 promotion-invalid였다. v3/v4/v5는 각각 full-$T$ 경계, ceil 경계, constant-truth/provenance 문제로 supersede되었다. valid F0-v3와 F1-v6만이 현재의 promotion source이며, audit는 이 분리를 확인했다.

## F2-A의 fail-closed 중단

F2-A는 32개 후보의 stress synthetic 단계였지만, 어떤 후보의 $Q$도 계산하지 않았다. JUMP scenario는 $U=I$ 상태에서 rank를 2에서 8로 올리는 DGP였고, prefix 구간의 채널 8--11이 모든 $E_A$ seed 8개에서 표준편차 0이었다. 이는 채널별 prefix 표준화와 noise scale이 요구하는 양의 분산을 만족하지 못하므로, 후보 순위·승격·상태를 계산하는 것은 fail-open이 된다.

정지 receipt는 `SYNTHETIC_DGP_STOP_ZERO_PREFIX_SCALE`을 기록하며, `completed_f2a_receipt=false`, `candidate_Q_run=false`, `candidate_status_or_promotion=false`, `behavior_loaded=false`, `model_fit=false`를 명시한다. receipt의 SHA-256은 `9103c458a196f893201ab11351f7a2e95719564bfcd0246e87effd0cd23ca4f7`이다. F2B/C/D, 독립 32-seed confirmation, F2R, neural-stage lock, SMALL/MID/LARGE/FINAL도 모두 열리지 않았다.

이 중단은 실제 데이터 불순도나 후보 공식의 가능성을 비교한 결과가 아니다. DGP의 관측 좌표가 rank-jump 전의 일부 잠재축을 정확히 0으로 보이게 한 생성기 문제다. successor는 dense fixed orthogonal sensor mixing을 새 계약·새 fixture·새 DGP audit로 먼저 고정하고, 모든 관측 채널의 prefix 분산이 양수임을 확인한 뒤에만 F2-A를 새 run으로 다시 시작할 수 있다. 현 run 안에서 mixing을 바꾸거나 threshold를 낮추어 재실행하는 것은 금지된다.

## 감사와 실행 경계

최종 수학·상태 감사는 F0-v3/F1-v6과 동결된 F2 입력에 대해 PASS였고, 동결 validation vector의 36개 배열 불일치는 0이었다. 다만 그 PASS는 F2-A를 열 수 있다는 조건부 허가였지, F2-A 성공 판정이 아니다. F2-A가 생성기 사전조건에서 멈췄으므로 이 run의 실질적 종점은 합성 DGP STOP이다.

검증에 사용한 경로는 `.codex/hooks/python.cmd python`의 정책 허용 Python entry point와 `git diff --check`의 문서 공백 검사였다. 이 문서에서 별도의 runtime을 새로 추정하거나 기록하지 않았다. contract·math·routes·audit의 SHA-256은 각각 `29b8507351f049fa3d5cf5ff6f4bc1135d12c3b499bc27a06fad081c48d2e158`, `dd9bb4f2c5680a26dd9f74fe748db77c6152a4985767010c46325ed0b78506d9`, `11a60afcedf333634f2cb19ec13fc6cd8adeb9bf602620a2124d9fbc2fc59099`, `bb09c75ebaa0442b71f6ae76245b1db4cf16b288fc2bd8df70820dc20d0e4e0c`이다.
