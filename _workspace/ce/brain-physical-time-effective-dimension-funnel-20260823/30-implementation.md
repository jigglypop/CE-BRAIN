# BA-SRM8 구현 기록: 물리시간 유효차원 후보 퍼널

Status: COMPLETE

Execution outcome: STOPPED (`SYNTHETIC_DGP_STOP / REAL_ENDPOINT_UNOPENED`)

Date: 2026-08-23

## 구현 대상과 경계

이 구현은 불규칙한 관측 시계와 결측이 있는 신경 신호에서, 한 시점의 관측 공분산이 몇 개의 연속적인 유효 자유도를 보이는지를 계산하는 분석 장치를 만들었다. 이 장치는 뇌의 리만 계량을 발견하거나 의식·AGI를 수량화하지 않는다. 특히 공분산의 축을 시냅스 간선, 방향성 루프, 해마의 해시값으로 해석하지 않았고, 행동값과 실제 신경-행동 모델은 끝까지 읽지 않았다.

각 시점 $t$에서 과거 표본 $j$에는 실제 경과시간, 품질, 불규칙 시계 보정을 함께 반영한 음이 아닌 가중치

$$
a_{tj}=K(u_{tj})q_j^{\gamma}\delta_j,
\qquad
w_{tj}=a_{tj}/\sum_{k\le t}a_{tk}
$$

를 주었다. 여기서 $K$는 후보별 시간 kernel, $q_j$는 관측 품질, $\gamma\in\{1,2\}$, $\delta_j$는 긴 시계 간격의 영향을 상한 3으로 제한한 보정이다. 따라서 결측 구간을 보간하거나 장벽으로 선언하지 않고, 과거 표본의 영향만 경과시간만큼 부드럽게 줄이는 `SOFT_GAP_DOWNWEIGHTING`을 사용한다.

표준화·마스크·품질 대각행렬을 포함한 관측 벡터를 $x_j$라 하면, 유효 표본수가 8 이상인 anchor에서만

$$
G_t=
\frac{\sum_j w_{tj}(x_j-\bar x_t)(x_j-\bar x_t)^{\mathsf T}}
{1-\sum_jw_{tj}^2},
\qquad
\bar x_t=\sum_jw_{tj}x_j
$$

를 계산했다. 음이 아닌 가중치 때문에 이 식은 PSD이며, 표본이 부족한 경우에는 0점이나 실패가 아니라 `ABSTAIN`으로 끝난다. 수치 rank tolerance는 쓰지 않고 $r_{\star,t}=\min(N,n_{+,t}-1)$를 사용했다. 학습 구간에서만 고정한 $c_G$로 정규화한 뒤, resolvent

$$
S_t=\widetilde G_t(\widetilde G_t+I)^{-1},
\qquad
Q_t=\operatorname{tr}(S_t)/r_{\star,t}
$$

를 계산하도록 구현했다. $Q_t\in[0,1]$은 이 관측 연산자의 정규화된 유효차원이지, 잠재 뇌 차원이나 생물학적 계량의 측정값이 아니다.

후보는 EXP·BIEXP·POWER·COMPACT의 여덟 시간 kernel, 두 품질 지수, identity·radial Huber·radial tanh의 세 robust map을 곱한 정확히 48개로 동결했다. 후보 manifest와 그 canonical content hash는 행동 접근 전에 고정되었으며, 후보 추가나 kernel·ridge·threshold 재조정은 허용하지 않았다. 이 설계는 많은 식을 싸게 탈락시키되, 짧은 kernel이 정보를 충분히 모으지 못한 경우를 수학적 반증으로 오해하지 않기 위한 것이다.

## 구현 순서와 수정 이력

퍼널은 48개 후보를 F0 정적 성질·runtime 검사, F1 작은 합성 복원 검사, F2 스트레스 합성 검사, 행동-비접근 실배경 주입(F2R), 그리고 2%·3%·2.5%·2.5%·20%의 시간 순서 실데이터 단계로 좁히도록 고정했다. 각 단계의 탈락은 후보 수와 계산비용을 줄이지만, 그 자체로 생물학적 결론을 만들지 않는다.

초기 attempt-00과 F1-v2에는 수치 rank 사용, usable-list 기준 70% 보정, clean/noisy 마스크·$D$ 불일치, range-NMAE 문제가 있었다. 이 산출물은 보존했지만 승격 근거에서 제외했다. 이어진 F1-v3/v4/v5도 각각 전체 길이 경계, ceil 경계, constant-truth 및 provenance 문제로 대체되었다. 최종 승격 근거는 valid F0-v3와 self-contained F1-v6뿐이며, 이 수정은 더 좋은 결과를 찾기 위한 재시도가 아니라 계약의 fail-closed 조건을 구현에 맞춘 정정이었다.

F0-v3는 48개 모두를 검사해 12개를 `ABSTAIN`, 36개를 `PASS`로 분류했다. `EXP_theta2`와 `COMPACT_L4`의 각 robust·품질 조합은 calibration에 쓸 유효 표본을 만들지 못했으므로 탈락이 아닌 abstention이다. 나머지 36개에서는 모든 유효 공분산의 최소 고유값, 인과성, 무차원 입력, zero/nonfinite fail-closed 경로, 기준 후보 대비 micro-runtime 비율을 확인했다.

F1-v6는 $N=8$, $T=192$, 4개 고정 seed에서 clean truth와 noisy estimate가 같은 mask·$D$·clock·candidate를 쓰도록 하였다. 각 쪽은 자기 원본-index 첫 70%에서만 $c_G$를 적합했고, 회복 anchor에서 $\operatorname{NMAE}^Q=|A|^{-1}\sum_{t\in A}|\widehat Q_t-Q_t^{\rm truth}|$와 average-rank Spearman을 계산했다. 36개 수치 통과 후보 중 budget 상위 32개만 `PROMOTE`, 4개는 `DROPPED_BUDGET`으로 고정했다. 승격 후보의 median $\operatorname{NMAE}^Q$는 0.03946--0.05940, median Spearman은 0.93657--0.98688 범위였으며, 이는 같은 관측 연산자의 clean/noisy 복원 성능일 뿐 후보 $Q$의 실측 증거나 신경·행동 모형의 성능이 아니다.

F2-A에 들어가기 전에 config, generator, fixture를 따로 동결했다. 그러나 rank $2\to8$ JUMP 생성기는 $U=I$와 축 정렬 관측을 함께 사용해 prefix에서 채널 8--11이 정확히 영인 표준편차를 만들었다. 8개 $E_A$ seed 모두에서 같은 결함이 나타났으므로, 후보별 $Q$, 상태, 승격을 계산하기 전에 실행을 중단했다. 이 중단은 후보의 실패도, 실제 뇌 데이터의 실패도 아니다. 다음 run은 dense fixed orthogonal sensor mixing을 source-lock하여 모든 관측 채널의 prefix 분산이 0이 아님을 먼저 보장해야 한다.

## 재현 경로

구현의 최종 동결 입력은 contract `29b8507351f049fa3d5cf5ff6f4bc1135d12c3b499bc27a06fad081c48d2e158`, 수학 문서 `dd9bb4f2c5680a26dd9f74fe748db77c6152a4985767010c46325ed0b78506d9`, route 문서 `11a60afcedf333634f2cb19ec13fc6cd8adeb9bf602620a2124d9fbc2fc59099`, audit `bb09c75ebaa0442b71f6ae76245b1db4cf16b288fc2bd8df70820dc20d0e4e0c`이다. valid F0-v3 receipt는 `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7`, F1-v6 runner와 receipt는 각각 `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7`, `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca`이다.

정책상 Python 호출은 `.codex/hooks/python.cmd python`만 사용했고, 문서 변경 뒤에는 `git diff --check`로 공백 오류만 확인했다. F2-A의 정지 기록은 [f2a-dgp-stop-receipt.json](C:/dev/ce/ce-agi-runtime/_workspace/ce/brain-physical-time-effective-dimension-funnel-20260823/artifacts/f2a-dgp-stop-receipt.json)에 있으며 SHA-256은 `9103c458a196f893201ab11351f7a2e95719564bfcd0246e87effd0cd23ca4f7`이다.
