# CML: 같은 범주 안의 고정 부호화–회상 판독

2026-09-20. [첫 실제 신호 읽기](hippocampal_cml_native_pair_findings.md)에 이어
같은 목록·범주의 네 단어 중 실제 회상 단어를 구별하는 관측식을 한 번 실행했다.
결과는 **제시 순서 기준 대비 개선 실패**다. 이 실험은 피질 내용 관측량의 후보를
검사하며, 해마 이력이 피질 복원을 유도하는지 직접 검사하지 않았다.

## 입력과 사전 고정 범위

OpenNeuro ds004809:2.2.0, sub-R1004D/ses-0의 기존 native sample 계약을 조건으로
한다. [입력 계획](../data/local/hippocampal-reinstatement/cml-withincategory-input-plan-v1/within_category_input_plan.json)은
같은 목록 정답 회상15행·고유13항목, 후보 집합10개, 부호화 WORD40행을 고정했다.
각 후보 집합은 같은 목록·범주의 네 단어이며, 각 단어의 부호화 제시는 세션 내 한 번이다.
정답 목록·범주를 알고 구성한 후향 비교이므로 다음 회상 내용을 자유롭게 예측하는
온라인 과제가 아니다. 내용과 부호화 시점의 맥락도 이 설계만으로 분리되지 않는다.

기존 원 EDF12개 record를 재사용하고224개를 추가 수신했다. 29개 범위 응답은 모두
206이며 Content-Range/Length와 고정 ETag가 맞았다. 추가 본문은86,041,536B이고
96MiB 상한 이내다. 합집합236개 record의 raw TAL·120채널 단위·유한값을 확인했고
digital rail은0이었다. 수집은 session55047, exit0으로 완료됐다. 이전 조사까지
누적 CML 응답 본문은91,706,581B이며 전체 EDF 파일을 받은 것은 아니다.

[원 기록 결과](../data/external/hippocampal_reinstatement/cml_catfr1_withincategory_records_v1/records_result.json)의
원래 Temp 경로는 보존했다. [정본 record index](../data/external/hippocampal_reinstatement/cml_catfr1_withincategory_records_v1/canonical_record_index.json)는
동일 바이트의 정본 위치를 가리킨다. 독립 행동 동기화나 발화 artifact 부재는 미확인이다.

## 고정 관측식

[방법 결정](../data/local/hippocampal-reinstatement/cml-withincategory-method-review-v1/root_decision_supplement.json)과
[소스 검토](../data/local/hippocampal-reinstatement/cml-withincategory-readout-review-v1/review.json)를
새 집단 신호 특징·점수 계산 전에 보존했다. 앞선 SPARROW 단일 쌍의 raw 그림은 이미
열람했으므로 완전한 파형 맹검은 아니다. 이 노출은 별도 보충에 기록했다.

- 채널: 기존 bipolar 표에서 두 구성 접점도 ECOG인 모든 피질 쌍140개. 해마 depth
  접점은 이번 판독 특징에 포함하지 않는다. 겹치는 쌍을 독립 뉴런 표본으로 세지 않는다.
- 특징: 부호화 후0.25–0.75초, 회상 발화 전−1.0–−0.5초의 각800표본을 평균 제거하고
  Hann periodogram으로 계산한70≤f<150Hz 적분 전력의 자연로그. 120Hz±2Hz는 제외한다.
  Baseline 차감·PCA·회상 결과에 따른 채널 선택은 없다. 이 대역 전력은 ripple 검출값이 아니다.
- 부호화40행만으로 채널별 평균·모집단 표준편차를 고정한다. 모든140개 특징이
  변동성 조건을 통과했다. 정규화된 회상 벡터와 네 부호화 벡터의 cosine을 계산한다.
- 기준 확률 q0는 `softmax(beta*(serialpos-6.5)/6)`이다. beta는 평가 목록 전체를
  제외한 회상만 사용해 목록 균등 손실로 고른다. 후보는−4,−2,−1,0,1,2,4이며
  동률 우선순위는0,−1,+1,−2,+2,−4,+4로 고정했다.
- 신경 특징을 더한 q1은 `softmax(log(q0)+cosine)`이며 cosine 계수는1로 고정했다.
  주 평가는 정답의 `log(q1/q0)`를 목록 안에서 평균하고 아홉 목록을 균등 평균한다.

같은 항목의 첫 정답 회상 여부를 다른 적격 조건보다 먼저 판정했다. 직전 REC_WORD 또는
단어 없는 발화 시작과의 간격이1초 이하인 회상과 REC_START 이전 평가창을 제외한다.
결과적으로75행은 반복+1599표본 간격,77행은1157표본 간격,492행은 반복+1600표본
간격으로 제외됐다. 추가 REC_START 제외는 없었다. 남은 분모는 **12항목·9목록·1명·1세션**이다.
시작 간격은 발화 길이를 측정하지 않으므로 말하기 영향의 완전한 제거를 뜻하지 않는다.

[Manning 등(2011)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3150951/)의 부호화–회상
진동 패턴 비교가 참고가 되지만 주파수·창·전극·정규화가 다르므로 원 논문 재현이 아니다.
일치 항목의 유사성에는 내용뿐 아니라 시간적 맥락도 기여할 수 있다는 해석 경계를 유지한다.

## 한 번 실행한 결과

[고정 결과](../data/local/hippocampal-reinstatement/cml-withincategory-readout-run-v1/result/result.json)는
신경 특징을 더할 때 기준 확률보다 나빠졌다. 균등 네 후보보다 좋은 점수를 신경 특징의
추가 효과로 해석할 수 없다. 제시 순서 기준 자체의 개선이 더 크다.

| 점수 | 목록 균등, 주 집계 | 항목 균등,12행 직접 평균 |
|---|---:|---:|
| 신경 특징의 추가 log-gain, nats | −0.0176267661 | −0.0136537949 |
| q1의 균등 후보 대비 log-gain | +0.2519287536 | +0.2140597542 |
| q0의 균등 후보 대비 log-gain | +0.2695555196 | +0.2277135492 |
| 정답 순위, 작은 값 우수 | 1.5555555556 | 1.5833333333 |
| 1위 정답 credit | 0.5925925926 | 0.5833333333 |

순위와 정답률은 보조 기술통계이며 신경 정보의 독립 효과나 유의성을 입증하지 않는다.
Beta는11행에서−2, 목록25의 한 행에서−4였고 실제 선택에 최소값 동률은 없었다.
적은 단일 세션의 이 고정식이 개선하지 못한 결과이며, 해마 기억 검색 일반을 반증하지 않는다.
시간창·채널·계수의 후속 조정이나 재적합은 하지 않았다.

## 검증과 보존

관련 테스트 파일은5개 검사 통과다. 실제 분석은 고정 소스로 정확히1회, exit0,
추가 네트워크0B였다. [독립 검사](../data/local/hippocampal-reinstatement/cml-withincategory-readout-run-v1/independent_check.json)는
31개 원 block,90,650,904B의 크기·SHA와 출력 manifest를 모두 대조했다. 모든 후보 수4,
평가 목록·행의 prior 학습 유입0, 제외 행과 분모를 확인했다. 저장 cosine에서 별도로
계산한 log 확률의 최대 절대차는8.88e−16, 추가 gain·집계 차이는1.11e−16 이하다.
이 검사는 raw 신호에서 특징까지 전 과정을 독립 재구현한 검사는 아니다.

`equal_item`은12행 직접 평균이다. 앞선 검토 문구의 모호함은
[집계 설명 보충](../data/local/hippocampal-reinstatement/cml-withincategory-readout-run-v1/review_aggregation_clarification.json)에
명확히 했으며 소스나 결과를 바꾸지 않았다. 실행 명령·환경 override는 보존했지만
해당 분석에서 해석된 Python/NumPy 버전은 직접 기록하지 않았다. 수집기의 버전 기록을
분석 실행의 버전 증거로 대신하지 않는다.

결과 SHA는 `f6001a39ba0eada24127e1666a82266681e8904c5c2cacfe52e6f0de060fb172`,
소스 SHA는 `90f97372e56072e9774ea390d95a60a2385fa97c183d940263c3bb54b64ebe0f`다.
원 실행 경로·입력·소스·검사 영수증을 고정하고 정본 보존 경로를 별도로 등록했다.

## 해마 복원 가설에서 남은 질문

해마를 기억의 주소 지정·검색 구조로 보는 연구 목표는 유지한다. 이번 피질 관측식의
실패를 해마 효과의 부재로 바꾸지 않는다. 다음 내용 복원 검증에는 부호화의 독립 반복이나
별도 보류 자료에서 내용 구별성을 확인한 관측량이 필요하다. 해마 이력 검증에는
해마와 피질의 공통 시계 아래, 직전 피질 상태·발화 준비·목록/순서 기준을 넘어서는
미래 피질 반응의 추가 예측력을 검사해야 한다. 다음 발화 선택과 이미 알려진 회상
내용의 후향 재활성화는 [서로 다른 관측 질문](hippocampal_retrieval_observation_findings.md)이다.
관계 변화·물리 비용의 계량·현재 세계 표현 선택까지의 연결은 여전히 미확립이다.
