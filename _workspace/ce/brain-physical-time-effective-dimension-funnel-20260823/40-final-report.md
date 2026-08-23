# BA-SRM8 최종 보고: 물리시간 유효차원 퍼널의 합성 생성기 중단

Status: COMPLETE

Verdict: `FORMALIZATION_COMPLETE / SYNTHETIC_DGP_STOP / REAL_ENDPOINT_UNOPENED`

Date: 2026-08-23

## 결론

BA-SRM8은 관측 이력의 가중 PSD 공분산과 resolvent 유효차원을 수학적으로 명시하고, 48개 후보를 행동 접근 전에 빠르게 좁히는 apparatus를 완성했다. 그러나 stress synthetic의 첫 관문 F2-A가 DGP의 zero-prefix-scale 조건에서 멈췄으므로, 이 run은 실제 신경 또는 행동 endpoint에 도달하지 않았다. 따라서 이것은 수식의 생물학적 성공도 실패도 아니며, 의식·AGI·시냅스 간선·방향성 loop·해마 hash에 대한 결론도 제공하지 않는다.

분석 장치는 현재와 과거의 관측값만 사용해 음이 아닌 물리시간 가중치로 $G_t\succeq0$를 구성하고, 표본수가 충분할 때 $S_t=\widetilde G_t(\widetilde G_t+I)^{-1}$에서 $Q_t=\operatorname{tr}(S_t)/r_{\star,t}$를 계산한다. 이로부터 $0\le Q_t\le1$이 따른다. 이 명제는 stated weight·유효표본수·양의 calibration scale 아래의 조건부 수학 성질이며, $Q_t$가 뇌의 고유 차원이나 리만 계량이라는 뜻은 아니다.

행동을 전혀 읽지 않은 F0-v3/F1-v6에서 48개 후보 중 12개는 유효표본 부족으로 `ABSTAIN`, 36개는 수치 검사를 통과했다. F1-v6의 고정 예산은 32개를 `PROMOTE`, 4개를 `DROPPED_BUDGET`으로 정했다. promoted 후보의 median $\operatorname{NMAE}^Q$는 0.03946--0.05940, median Spearman은 0.93657--0.98688이었다. 이는 clean/noisy 합성 관측의 동일한 operator 복원 지표이며, candidate $Q$의 F2 증거나 생물학적 모델 적합 결과가 아니다.

이 결과에는 부정적인 구현 이력도 포함한다. attempt-00/F1-v2의 rank·calibration-boundary·관측 공유·NMAE 오류와 F1-v3/v4/v5의 경계 또는 provenance 오류는 모두 보존하고 promotion source에서 제외했다. valid F0-v3와 self-contained F1-v6만 사용했으며, 결과가 좋아 보이는 판본을 고른 것이 아니라 고정 계약과 일치하는 판본만 남긴 것이다.

F2-A에서는 JUMP DGP의 rank $2\to8$ 전환을 점검하던 중, $U=I$인 축 정렬 관측 때문에 채널 8--11의 prefix 표준편차가 8개 seed 모두에서 정확히 0임을 확인했다. 이 조건에서는 prefix 표준화·noise scale을 정의할 수 없으므로 후보별 $Q$, candidate 상태, 승격을 아예 실행하지 않았다. 완성된 F2A receipt는 없고, F2B/C/D, F2R, 행동 load, 모델 적합, 실제 endpoint score도 없다. 정지 receipt [f2a-dgp-stop-receipt.json](C:/dev/ce/ce-agi-runtime/_workspace/ce/brain-physical-time-effective-dimension-funnel-20260823/artifacts/f2a-dgp-stop-receipt.json)의 SHA-256은 `9103c458a196f893201ab11351f7a2e95719564bfcd0246e87effd0cd23ca4f7`이다.

다음 단계는 이 run의 parameter를 바꾸는 재시도가 아니다. 새 run에서 dense fixed orthogonal sensor mixing을 source-lock하고, 새 fixture가 모든 관측 채널의 prefix 양의 분산을 보장하는지 DGP audit로 확인한 뒤 F2-A를 처음부터 시작해야 한다. 그 전에는 행동, 모델, real score를 읽지 않는다.

## 증거 경계

최종 근거는 F0-v3 `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7`, F1-v6 runner `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7`, F1-v6 receipt `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca`, F2 config/generator/fixture `9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47` / `12200f0f6d2d2db61d1000c40a39049123b5f1e2023ef439f9763ad69794f605` / `6346c57cbdc7c8b564b316aca0ba06008ac01c9e66035b7794f8c472612592bf`이다. 계약·수학·경로·감사의 SHA-256은 각각 `29b8507351f049fa3d5cf5ff6f4bc1135d12c3b499bc27a06fad081c48d2e158`, `dd9bb4f2c5680a26dd9f74fe748db77c6152a4985767010c46325ed0b78506d9`, `11a60afcedf333634f2cb19ec13fc6cd8adeb9bf602620a2124d9fbc2fc59099`, `bb09c75ebaa0442b71f6ae76245b1db4cf16b288fc2bd8df70820dc20d0e4e0c`이다.
