# CE-BRAIN Stage 8·9 분기 게이트 감사

Status: `ROUTE_AUDIT`

## Stage 8

매뉴얼 의사결정 트리는 Stage 7의 `memory trajectory 재구성?`이 YES일 때만 retrieval과 correction 분리로 내려간다. R1과 R2C 모두 encoding 및 replay 문턱을 실패했으므로 현재 Stage 8 확인 실행은 미허가다.

**[금지]** trajectory가 확립되지 않은 상태에서 recall 방향과 correction 방향의 cosine을 계산해 READ/WRITE subspace를 주장하지 않는다. 좌표계 자체가 충분히 정확하지 않으면 두 방향의 분리는 식별되지 않는다.

**[대체 분기]** 매뉴얼대로 `다른 memory code 탐색`으로 이동한다. 다음 후보는 trial·epoch 의미가 명시된 자료에서 정적 ensemble, 순서 없는 relational code, 방향별 state-space code를 경쟁시키되 새 test를 보존해야 한다.

## Stage 9

매뉴얼 작성 당시 자료군은 실시간 dopamine/ACh/NE/Ca²⁺와 memory update의 동시 관측이 부족했다. 2026-08-31 현재 공식 DANDI에는 새 후보가 있다.

- `001632` draft: 행동과 dopamine 기록, 보상 간격에 따른 학습. 126 subjects, 1,222 assets, 약 4.1GB.
- `001176@0.260610.2204`: cortical ACh sensor·axon·행동상태 동시영상. 기억 update 과제는 아니다.
- `001950` draft: LC-NE 전기생리/photometry와 dynamic foraging. 기억 궤적보다는 의사결정·조절 상태 후보이다.
- `000351`: NAcc dopamine photometry와 causal-association 행동. 규모가 크고 현재 핵심 학습률 질문에는 `001632`가 더 직접적이다.

**[판정]** `STAGE9_DATA_CANDIDATE_AVAILABLE_SCHEMA_PENDING`. Stage 9를 자료 없음으로 닫지 않는다. 단, `001632`는 draft라 전체 asset inventory와 수정시각을 매 실행 전 다시 검증해야 한다.

**[주장 상한]** `001632`가 통과해도 dopamine이 기억 전체의 화학적 원인이라는 주장이 아니다. 보상 간격·과거 행동을 통제한 뒤 기록된 dopamine 변수가 held-out animal의 학습률 예측에 추가 정보를 주는지까지만 묻는다. 인과 gate에는 별도 조작 또는 pharmacological intervention이 필요하다.
