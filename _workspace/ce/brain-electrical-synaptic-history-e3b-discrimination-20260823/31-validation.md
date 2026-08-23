# BA-ERC1-E3b 검증: 고정 kernel 메뉴의 합성 판별

Status: COMPLETE

이번 검증은 실제 시냅스가 아니라, 사전에 고정한 event train에서 유한 지수 kernel 메뉴 $E_1,E_2,E_4,E_8$과 한 개의 compact $C^\infty$ bump $B$를 식별 장치가 올바르게 구별하는지 점검했다. one-shot attempt 0은 PASS였고 apparatus revision이나 재실행은 없었다. 최종 receipt SHA-256은 `0f96a49ead927620ecaca06d13bb1ab2ad26d7222a45935df45c29b370283d68`이며, post-run ledger SHA-256 `a71d1fc7a606411ddd5aad0c0d3dd60dfbf642168286861acdf8621b912b59fd`와 대조한 결과 source, predecessor, older-evidence, preflight archive, environment seal이 모두 일치했다.

검증기는 먼저 memory-only AST parse를 통과했고, 이후 bump의 인과적 지지·비음수성·정규화, 무차원 구성, 모든 출력의 유한성, calibration design의 full column rank, 정규화 condition number, negative와 positive confirmation, dense-kernel separation, reversed-bump adverse control을 모두 통과했다. receipt의 `failed_checks`는 빈 배열이다. 독립 status audit과 math audit도 PASS였으며, 후자는 지수 보조상태의 유한 실현, compact-bump 정리의 적용 조건, SVD 기반 선택 규칙과 수치 조건을 분리해 확인했다.

음성 패널에서는 $E_2$가 confirmation relative error $6.17410328886224\times10^{-16}$로 선택됐다. $E_2,E_4,E_8$의 development tie에서는 더 적은 계수 규칙이 $E_2$를 선택하므로, 이 결과는 finite generator에 대한 장치 특이성 검사다. 양성 패널에서는 $B$가 confirmation relative error $1.60615500530870\times10^{-16}$로 선택됐고, 가장 좋은 finite competitor $E_8$의 confirmation error는 $0.2270211315620434$, dense-kernel error는 $0.2891662558095040$였다. reversed bump의 confirmation error $0.5722092307645735$도 사전 기준 $5\times10^{-2}$를 넘었다. 모든 설계행렬은 full rank였고 최대 normalized condition number $403.493915735834$는 한계 $10^6$보다 작다.

무차원성 focused pytest는 cache 없이 실행되어 `19 passed in 0.35s`를 기록했다. 전용 dimensionless checker script는 exit 0, 출력 없음으로 끝났다. 전체 test suite는 실행하지 않았다. 이들은 구현과 단위 규율의 수치적 무결성을 말할 뿐, 생물학적 참이나 실제 시냅스의 상태 차원을 뜻하지 않는다.

정리의 정확한 범위도 제한한다. 0이 아닌 compactly supported $C^\infty$ regular impulse response는 pure delay나 distributed state가 없는 유한차원 causal continuous-time constant-matrix LTI로 정확히 실현할 수 없다. 이 문장은 continuum에서의 exact realization만 다룬다. 유한 grid에서의 근사 하한을 주지 않으며, 비선형·지연·Volterra·다른 매개화의 유한차원 모형 전체가 불가능하다고 말하지 않는다.

따라서 이번 PASS의 claim ceiling은 `SYNTHETIC_HISTORY_SYNAPSE_OBSERVATION_DISCRIMINATION / E3B_FIXED_MODEL_MENU_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`이다. E3b-3, cable/HH 재결합, 실제 뇌 자료, 무한한 생물학적 차원, 의식, 기억·해마, AGI는 모두 locked 상태다.
