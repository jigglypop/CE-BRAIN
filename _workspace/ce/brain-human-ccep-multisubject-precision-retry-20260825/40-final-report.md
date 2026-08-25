# BA-OBS-DISC2R 최종 보고서: 인간 CCEP에서 단순 거리 감쇠의 제한된 예측 이득

Status: COMPLETE

## 초록

본 실행은 74명의 서로 겹치지 않는 환자에서 592개 자극 source와 9,472개 target의 human SPES CCEP 관측 kernel을 분석했다. 사전에 고정한 bipolar, baseline-subtracted endpoint에서 시간·연령 기준식에 유클리드 거리 감쇠를 더한 `SC`를 D0에서 선택하고 D1·D2·D3 held-out 환자 집단에서 검증했다. D3 평균 개선은 $0.0173522$, 97.5% participant-bootstrap 하한은 $0.0102676$, 양의 개선 참여자는 23/30명, geometry permutation $p=1/4096$였다. matched prestimulus 대조는 통과하지 않았다. 이 결과는 단순 유클리드 거리 감쇠가 이 관측 endpoint의 예측에 유익했다는 경험적 결과이며, 뇌의 리만 계량·축삭 geodesic·무한차원 상태공간 또는 의식 이론의 검증은 아니다.

## 문제와 비유

도시의 두 지점에서 같은 시간대의 소음 크기를 예측한다고 하자. 거리가 멀수록 소리가 약해질 수 있지만, 실제 음량에는 건물, 바람, 마이크의 위치와 감도도 섞인다. 거리 항이 예측을 조금 고친다고 해서 도시의 모든 길·벽·공기 흐름을 복원한 것은 아니다. 본 연구의 source와 target 전극도 같다. 자극 후 전압에는 neural response뿐 아니라 reference, volume conduction, stimulation artifact와 noise가 섞인다. 따라서 질문은 “뇌의 진짜 길이를 찾았는가”가 아니라 “고정한 관측 사슬에서 거리 항이 시간 기준식보다 새 표적의 반응을 더 잘 예측하는가”다.

## 사전 고정된 관측식

열 개의 깨끗한 trial을 source마다 사용했다. contact baseline median을 빼고 bipolar difference를 만든 뒤, pooled $1.4826\,\mathrm{MAD}$로 scale한 열-trial 평균의 다섯 post-stimulus RMS를 $E$라 정의했다. 분석값은 $z=\log(E+10^{-6})$다. 시간 좌표 $x$와 중심화 연령 $\widetilde A_i$를 사용한 기준식은 다음과 같다.

$$
T_i^\star(x)=\beta_1\log x+\beta_2x
+\gamma_1\widetilde A_i\log x+\gamma_2\widetilde A_i x.
\tag{1}
$$

source마다 anchor trial에서만 추정한 offset $b_s$를 더해 자극·전극별 수준 차이를 흡수했다. `SC`는 여기에 거리 $r$의 단조 감쇠를 붙인다.

$$
\widehat z_{ist}=T_i^\star(x_t)+b_s-a r_{s\to q},\qquad a\ge0.
\tag{2}
$$

식 (2)의 $r$는 fsaverage/MNI305 기반 등록 좌표에서 잰 단순 유클리드 거리다. 따라서 $a$는 해부학적 전도도나 축삭 path length의 추정치가 아니라 이 관측 좌표계의 예측 계수다. D3의 추정값은 $a=0.8427201$이었다.

## 실행 설계

선행 BA-OBS-DISC2는 crosswalk histogram을 lookup으로 잘못 해석하여 첫 raw request 전에 중단됐다. 재시도 BA-OBS-DISC2R는 그 linkage만 고치고 과학적 입력을 byte-for-byte 상속했다. 새로운 run-lock은 `d70f83387143145bb1c40258c1f1a3974c168c30c677d2f67cc5819ffdccd291`이며, 이전 실패 record는 endpoint 관측값을 전혀 만들지 않았으므로 재시도에 데이터를 통한 선택 기회가 없었다.

D0는 24명에서 후보를 선택했고, D1·D2·D3은 각 8·12·30명의 미관측 환자에게 순차 적용했다. 모든 source에는 4 anchor와 12 query target이 있고, 모든 stage는 exact version-locked raw range를 사용했다. 원시 payload는 저장하지 않았으며 합계 5,920 range의 provenance와 endpoint hash chain을 독립 감사와 post-run validator가 확인했다.

## 결과

D0에서 `SC`는 평균 **상대 CV 개선** $0.0638202$, 6/6 fold win으로 선택됐다. `SAC`의 상대 CV 개선 $0.0640458$은 더 컸지만 사전 tie band $0.005$ 안이어서 단순한 `SC`가 우선했다. 이 선택을 고정한 뒤 D1은 평균 **절대 Huber-loss 개선** $0.0203434$, 7/8명 양의 개선, $p=1/512$를 보였고 D2는 평균 절대 Huber-loss 개선 $0.0168684$, 10/12명 양의 개선, 80% LCB $0.0127012$, $p=1/1024$를 보였다. 마지막 D3은 평균 절대 Huber-loss 개선 $0.0173522$, 23/30명 양의 개선, 97.5% LCB $0.0102676$, $p=1/4096$로 모든 사전 gate를 통과했다.

자극 전 구간에 같은 계산을 적용한 negative control은 통과하지 않았다. 평균은 $0.0000445$, 97.5% LCB는 $-0.0001462$, permutation $p=0.0568848$였으며 양의 참여자는 16/30명뿐이었다. contact-mean diagnostic은 `REFERENCE_CONCORDANT`였다. 따라서 발견된 이득은 적어도 무자극 baseline의 일반적인 거리 패턴과는 구별되지만, reference와 volume conduction의 모든 효과를 제거했다는 뜻은 아니다.

| Stage | 독립 환자 | 결과 | SHA-256 |
|---|---:|---|---|
| D0 | 24 | `PASS_SELECTION_ONLY` | `d357dce969476f352758790c8a7cb2d212967186de9ede61765376cf94ca5919` |
| D1 | 8 | `PASS_INTERMEDIATE` | `9b9ff8cbcec56790975690c7934bf0a5db4e14e9efb6e64c61926796a85098f3` |
| D2 | 12 | `PASS_INTERMEDIATE` | `67140450e3c8f6634dda7d8516c53b36f71e976004bc81185d0782ff2d9f1b91` |
| D3 | 30 | `PASS_FINAL` | `1e85eb3979b338f8927a35ce1e739468980ce1fa56f259d742577eadef6b85fa` |

## 해석과 한계

이 결과가 보여 주는 것은 하나다. 이 frozen patient-disjoint multi-subject human SPES CCEP observed-kernel prediction에서 단순 유클리드 거리 감쇠 `SC`가 지정된 temporal baseline보다 나았다. `artifacts/21-final-audit.md`에 연결된 최종 독립 감사 receipt `434a9a977440b29c4878d9878859235a66a3ce28170887a2966dfbe988afc09b`와 primary hardened v2 post-run validation receipt `743f54b7cb35f206b505b8b8f5ebd31e4db5aba5626138dfce220c8fd8b4efeb`(validator `85e4d2b07a18819018a179783e96d6a4e010376eca5cec2823b217004c8995cc`)는 실행 무결성을 보장하는 증거이지 더 넓은 기하학적 주장을 증명하는 증거는 아니다. v1 receipt `b3f3f9a1d50f52337fe867f7ab9a1e99174bfcd74b6dd4802325763c2859c3be`는 lifecycle 수준의 역사적 검증으로 보존한다.

특히 좌표는 등록공간 proxy이고, 실제 axonal path·directional transfer·conductance tensor·개인별 구조 연결을 측정하지 않았다. source offset과 bipolar endpoint의 선택도 이 관측량의 일부다. 그러므로 “리만 metric이 발견됐다”, “고차원 latent state가 확인됐다”, “현재 세계 manifold나 자아·해마 hash·AGI가 입증됐다”는 해석은 이 결과와 논리적으로 연결되지 않는다.

## 다음 독립 실험

이 자료의 D0–D3를 다시 쓰는 일은 확인 실험이 아니다. 후속 실험은 새 계약, 독립 dataset 또는 새 환자 allocation, endpoint-blind split과 새 독립 감사를 먼저 고정해야 한다. 그때에만 고정된 Euclidean `SC`를 생물학적으로 제약한 tract/geodesic 또는 conductance 모델, 혹은 부호를 보존한 transfer-function 모델과 경쟁시킬 수 있다. 새 모델이 held-out prediction과 prestimulus·reference 대조를 함께 이기지 못하면 해당 기전 해석은 중단해야 한다. 그것이 이 작은 거리 결과를 더 큰 뇌 이론으로 과장하지 않는 방법이다.
