# BA-SELF3-L3 최종 보고서: 채널별 affine-불변 QC의 held-out 전이 실패

Status: COMPLETE

Final disposition: `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER / R2_FAILED_AT_B1 / MODEL_ENDPOINT_UNOPENED`

이 실행이 다룬 질문은 자아가 한 순간의 상태인지, 아니면 그 상태들 사이를 잇는 과정의 길인지라는 존재론적 질문을 직접 판정하는 것이 아니었다. 더 좁게는, 현재 관측 EEG quotient와 현재값·미분·구간 통계·과제 조건을 이미 알 때, 순서가 있는 과거 경로의 2차 antisymmetric area가 100 ms 뒤의 관측 EEG 변화를 추가로 예측하는지를 묻도록 설계되어 있었다. 그러나 그러한 모델 비교에 들어가기 전에, 서로 다른 기록 구간에서 신호를 같은 관측 단위로 다룰 수 있는지부터 확인해야 했다. BA-SELF3는 그 장비 전이 관문에서 멈췄다. 따라서 이번 결과는 경로식, 자아, 의식, 해마의 해시 가설, 또는 무한차원 상태공간에 대한 반증이 아니다. 이 실행은 오직 고정한 R2 품질관리 규칙이 미개봉 held-out 창으로 전이하지 못했다는 결과다.

## 관측 장치와 R2의 범위

각 task/rest anchor에서 원시 5 kHz 기록의 3,001 sample을 정확한 HTTP range로 읽었다. ECG를 제외한 63 scalp channel에 common-average reference를 적용하고, causal 45 Hz FIR 뒤 250 Hz로 decimation하여 $126\times63$ 창 $X$를 만들었다. 이 처리는 관측량을 정의할 뿐 뇌 전체 상태나 무한차원 Riemannian metric을 복원하지 않는다. 뒤의 quotient rank $d\in\{2,3,4\}$는 이 관측 창에서만 정의될 저차 좌표이며, 의식의 차원 수라는 뜻이 아니다.

BA-SELF2의 공통 gain 정규화가 실패한 뒤, BA-SELF3는 각 channel에 따로 걸리는 상수 gain과 offset을 제거하는 R2를 새 계약으로 고정했다. 시간 중앙값 residual과 그 robust scale을

\[
R_{tc}=X_{tc}-\operatorname{median}_{u}X_{uc},\qquad
s_c=1.4826\operatorname{median}_{t}|R_{tc}|,
\]

한 단계 차분과 그 scale을

\[
D_{tc}=X_{t+1,c}-X_{tc},\qquad
r_c=1.4826\operatorname{median}_{t}|D_{tc}-\operatorname{median}_{u}D_{uc}|,
\]

로 두고, 창의 최대 꼬리값을

\[
Q_A^{\rm ch}=\max_{t,c}\left|R_{tc}/s_c\right|,\qquad
Q_D^{\rm ch}=\max_{t,c}\left|D_{tc}/r_c\right|
\]

로 정의했다. $X'_{tc}=a_cX_{tc}+b_c$, $a_c\ne0$인 channel별 상수 affine 변화에는 두 비율이 정확히 불변이다. 이 불변성은 각 채널의 상수 단위·gain·offset 차이를 제거한다는 뜻일 뿐이다. 시간에 따라 달라지는 gain, channel mixing 또는 montage 변화, 비선형 saturation, 넓게 퍼진 artifact, 그리고 생리적 차이는 제거하지 않는다. 특히 $Q_A^{\rm ch}$와 $Q_D^{\rm ch}$는 시간과 채널 전체의 최대값이므로, 한 채널의 짧은 tail도 창 전체를 탈락시킨다. 이 보수성은 숨기지 않은 설계 경계다.

## 모델 이전에 시행한 장비 관문

A1에서는 기존에 허용된 16개 창만 읽어 정의역을 점검했다. 결과는 `A1_APPARATUS_PASS`였고 nonfinite 또는 0/nonfinite channel scale에 따른 hard-domain 탈락은 없었다. A2에서는 별도의 64개 calibration 창만으로 cutoff를 한 번 고정했다. median $+6\,\mathrm{MAD}$ 규칙은 $Q_A^{\rm ch}=9.610396697909561$, $Q_D^{\rm ch}=11.350540283998544$를 만들었고, 이 역시 `A2_APPARATUS_PASS` 및 hard-domain 오류 0으로 끝났다. 이 두 단계는 장비 정의와 cutoff의 동결을 확인한 것이지 경로 예측을 평가한 것이 아니다.

모델에 쓰지 않을 B1은 과거에 보지 않은 D2 trial을 trial hash로 signal-blind 정렬하여 session마다 앞의 16 pair씩 배정한 32 pair였다. 통과 조건은 전체 24/32 이상이면서 각 session 12/16 이상이었다. B1의 실제 통과는 17/32, `ses-01` 10/16, `ses-02` 7/16이어서 세 조건 모두 충족하지 못했다. 이에 따라 고정된 판정 `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`가 발생했다.

실패 양상은 단순한 amplitude tail보다 difference tail이 우세했다. 탈락 15 pair 가운데 $Q_D^{\rm ch}$ 초과가 포함된 것은 14 pair였고, $Q_A^{\rm ch}$ 초과가 포함된 것은 7 pair였다. 겹친 6 pair를 분리하면 $Q_D$ 단독 8, $Q_A$ 단독 1, 둘 다 초과 6 pair다. 즉 이 held-out 구간에서는 짧은 시간 차분의 채널별 최대 꼬리가 주된 제한 요인이었다. 이는 관측기록의 빠른 변동이 R2의 고정 cutoff와 맞지 않았다는 사실이지, 그 변동이 artifact라는 판정도 아니고 신경 동역학의 원인 규명도 아니다.

## 열지 않은 과학적 종점

B1은 apparatus 전이만을 위한 subset이므로 quotient coordinate $z$, 100 ms 미래 target, ordered-area feature, $M_0/M_1$ loss, ridge 선택, reverse/shuffle control을 계산하지 않았다. receipt는 `scientific_endpoint_opened=false`, `model_outcome_opened=false`, `model_outcome_computed=false`를 기록한다. D2-M 및 독립 `sub-03`의 C1/C2/C3는 모두 개봉하지 않았다. 따라서 `STOP_NO_ORDERED_HISTORY_GAIN`도 아니며, 경로 가설이 baseline보다 못했다는 결과도 없다.

이 경계는 자아 질문에도 중요하다. 유한 길이의 과거를 상태에 포함시키면 경로 예측기를 확장된 상태 함수로 다시 쓸 수 있고, 유한 EEG 관측은 관측 kernel을 나눈 quotient일 뿐이다. 그러므로 장차 예측 이득이 관측되더라도 그것만으로 자아가 ‘순간 상태’인지 ‘이어지는 길’인지, 또는 어느 것이 더 근본적인지 판정할 수 없다. 반대로 여기서 장비 QC가 실패한 것은 그 존재론적 가능성들 중 어느 하나에도 불리한 증거가 아니다.

## 후속 조건과 재현 기록

B1은 소진되었다. 같은 32 pair를 다시 열어 cutoff를 완화하거나 R2를 다시 맞추는 것은 허용되지 않는다. 후속은 새 계약의 R2b여야 하며, 변경할 QC 정의·calibration·allocation·gate를 신호 접근 전에 고정하고, 이번 B1과 겹치지 않는 새로운 held-out subset에서 apparatus 전이를 다시 확인해야 한다. 그 새 B1-equivalent가 전체 24/32 및 session별 12/16을 만족할 때에만, 그 계약이 남겨 둔 D2-M에서 최초의 path-model 개발을 시작할 수 있다. 새 장비 관문도 통과하지 못하면 해당 route는 모델 단계 없이 종료된다.

이 보고서는 동결된 원장을 읽기 전용으로 사용했다. 원장 SHA-256은 `1265db747905b1c08f2bd12fe458d7fe8e264d3e6d73849203ed8e31416fe98b`이다. 계약·출처·수학·경로·감사 문서 SHA-256은 각각 `765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`, `a4be903d20a0f6e1391cde907c7f727b8804b62cd6ace02ab9be1fd9572012a7`, `87778e0738961a7c8b49004b01684f55b92e35368fb06c6a457625094232ec02`, `041b0bcf1c58dc8d49437819d776647520ba1c50c627a7b131cc6bf5f03afad9`, `64384d9d8c80b6b1e6abf16adf21553c90941cf91b4d4b86df5170b7e2f48259`이다. 구현과 focused validation 문서는 `da33e27e4ade65c43bfcf35afae203b53090adb789b47e2eaa845bb88fb3de1c`, `c9d689513af34219038aadcb6c08436e040e594e560e191bdc2e49bdc88cf0bb`이며, A1/A2/B1 receipt는 각각 `219aabf504deb6c16db719fb9f19da9a09a5f464dae4791ce3735f378bbfe21e`, `8270f31272ff21814c0c0ed5614d74dd29acd8f2045bc645baaa68e41a4d28d8`, `d3b7319804206b3ddcc6f35260706dfe4d4b961e0053db80c1c16c9569ead362`이다. signal-blind allocation은 `91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2`, apparatus code는 `e3713b2b9533d7523a903901c04808901eba79724c7b4822d2673877b72e8f0b`, focused synthetic test는 `32298856c0859b10ea9185ee74941c64096b3eaeca3b80335fbb6a754eb23328`이다. focused test는 Python 3.11.9와 NumPy 2.4.6에서 `10 passed in 0.93s`였으며, 이는 R2 구현과 fail-closed 경계의 재현성 검증이지 인간 뇌 기전의 증거가 아니다.
