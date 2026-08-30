# CE-BRAIN Stage 3A R5 삼각진단 불가 계약

Status: `SEALED_PRE_RESULT`

Schema receipt SHA-256은 `be74b966fbe664d00afd84486336fd5b3f0d08cfbc70c322f77f7f71be7e03fd`이고, 봉인 직전 R1~R5 집중검사 18개가 모두 통과했다.

R4는 후보 모델 적합과 점수 계산 뒤 결과 파일을 쓰기 전에 triangle coverage 문에서 중단됐다. 점수는 출력·저장되지 않았지만 계산은 됐으므로 R5 manifest에 `model_scores_computed=true`, `model_scores_observed=false`로 기록한다.

confirmation에서 3개 이상 동물에 반복된 directed pair는 102개, 이들로 구성 가능한 directed triad는 125개뿐이며 사전 문턱 1,000개에 못 미친다. R5는 삼각부등식 진단을 `NOT_IDENTIFIABLE`로 보고하고 위반 상한을 보수적으로 1.0으로 둔다. 나머지 R4 탐색 모델 경쟁과 결정 코드는 그대로 실행한다. 따라서 Riemannian-like 판정은 나올 수 없고, 모든 결과는 계속 `EXPLORATORY_`, `stage4_authorized=false`다.
