# CE-BRAIN Stage 3A R4 탐색 모형경쟁 계약

Status: `SEALED_PRE_RESULT`

Schema receipt SHA-256은 `be74b966fbe664d00afd84486336fd5b3f0d08cfbc70c322f77f7f71be7e03fd`이며, 봉인 직전 R1~R4 집중검사 16개가 모두 통과했다.

R3는 과학 판정 전 사전등록 coverage 문에서 중단됐다. 관측된 적격 수는 development 10,766행, confirmation 4,631행, common-pair 1,686행, unseen-source 1,121행이었다. 이는 원래 문턱 20,000/10,000/5,000/1,000 중 세 항목을 충족하지 못한다.

R4는 결과 확정이 아니라 다음 실험 설계를 위한 **탐색 분석**이다. 모델 점수를 보기 전에 최소 실행문을 development 10,000, confirmation 4,000, common-pair 1,500, unseen-source 1,000으로 고정한다. R1~R3의 endpoint, 모델, bootstrap, 승리 규칙은 그대로 사용하지만 모든 결정 앞에 `EXPLORATORY_`를 붙이고 `stage4_authorized=false`로 고정한다.

R4 봉인 전에 confirmation의 coverage와 양성 간선 수까지 이미 계산됐으나 후보 모델 점수와 승자는 보지 않았다. manifest에 `confirmation_scientific_endpoints_opened=true`, `confirmation_model_scores_opened=false`로 기록한다. 따라서 R4는 독립 확인 증거가 아니며, 새 데이터에서 재등록 복제할 후보를 고르는 용도다.
