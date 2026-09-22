# 데이터 원장

다운로드 전에 여기서 보유 자료를 찾는다. [원장 본체](data_registry.jsonl)는 한 줄에 등록 기록 하나를 저장한다. 기록은 삭제하지 않으며 같은 자료·판본·파일·경로의 마지막 기록을 조회한다. 이 원장은 보유 상태를 관리한다. 과학적 적격성은 각 질문의 분석 기록에 남긴다.

기존 폴더는 위치만 등록했다. 원자료·코드·결과만 있는 폴더가 섞여 있으므로 파일 보유나 분석 가능성을 보장하지 않는다. [기존 재고 조사](../verify/Q-NPF-03/local_data_inventory.md)는 당시 질문에 대한 참고 기록이다. Randi OSF 자료의 두 폴더는 같은 자료 ID로 묶었으나 파일 단위 동일성은 아직 확인하지 않았다.

2026-09-20 기존 식의 정확도 재검토는 자료 ID `equation-accuracy-review`, 판본
`2026-09-20-v1`로 등록했다. `data/local/equation-accuracy-review-v1/`의 14개 파일
197,743 bytes이며 새 원자료 다운로드·적합은 없다. 기존 점수와 저장 RC 파형 재검산,
현재 연구 순서는 [정확도 검토 원장](existing_equation_accuracy_findings.md)을 따른다.

전기식 후속 입력과 계산은 `allen-synphys-analysis`의 `passive-port-input-v1`,
`passive-port-two-mode-v1`이다. 50 kHz 원표본 80행과 VC 학습→VC/IC 평가의 두 성분
비교를 보존했다. 파일·해시·단위·개발 분석의 한계는
[수동 포트 원장](passive_port_mechanism_findings.md)에 있다.

저장소 루트에서 실행한다.

```powershell
# 출처·자료 ID·판본·파일명·해시·경로 검색
.codex/hooks/python.cmd python .codex/hooks/data_registry.py find allen_synphys

# 필요한 파일만 해시 재검증
.codex/hooks/python.cmd python .codex/hooks/data_registry.py find synphys_r2.1_small.sqlite --verify

# 새 파일 등록: 실제 경로·출처·이유로 바꿔 실행
.codex/hooks/python.cmd python .codex/hooks/data_registry.py register --dataset DATA_ID --version VERSION --asset FILE --path LOCAL_FILE --source SOURCE_URL --reason "처음 수집"
```

폴더 또는 미완료 파일의 위치를 남길 때는 `register`에 `--location-only`를 붙인다. 판본이나 출처를 확인하지 못했으면 `unknown`으로 명시하고 후속 확인 때 새 기록을 남긴다. 같은 자료·판본·파일에 다른 해시는 자동 덮어쓰지 않는다. 먼저 손상이나 판본 변경을 확인한다. 원장 쓰기는 주 에이전트가 직렬로 수행한다.

| 조회 상태 | 뜻과 다음 행동 |
|---|---|
| `location_only` | 위치만 확인. 폴더 안 목록·수집 영수증을 먼저 확인 |
| `partial` | 미완료 파일 있음. 실행 중인지 확인하고 중복 다운로드 금지 |
| `unchanged_metadata` | 등록 당시 해시가 있고 현재 크기·수정시각이 같음. 현재 해시 일치를 재검증한 것은 아님 |
| `hash_match` | 이번 조회에서 등록 해시와 일치 확인 |
| `changed` | 파일 변경 감지. 사용 전에 판본·무결성 확인 |
| `missing` | 등록 경로가 없음. 다른 위치를 먼저 찾은 뒤 필요하면 재수집 |

도구는 네트워크 접속·다운로드·삭제를 하지 않는다. `find` 결과가 없더라도 다른 이름의 자료와 미등록 파일을 확인한다. 동일 해시 검색으로 다른 이름·위치의 복사본도 찾을 수 있다. 서버가 제공한 체크섬과 별도로 대조하지 않았다면 로컬 해시 등록만으로 서버 원본과의 일치를 주장하지 않는다.

## MaleCNS 보유 자료 (2026-09-14)

`.gitignore`의 `/data/` 때문에 일반 `rg --files`에서 빠지지만 실제 로컬 자료는 있다.
자료 ID `malecns`, 판본 `v1.0`으로 네 위치와 11개 파일을 등록했다. 새 다운로드는 없다.

| 위치 | 보유 내용 | 사용 전 구분 |
|---|---|---|
| `data/local/malecns-v1.0` | annotation, NT prediction, segment 연결표와 source lock | 원본 3개 해시를 기존 lock과 대조 |
| `data/local/malecns-v1.0-flat-connectome` | 공식 객체 11개, 31,318,683,398 bytes, generation별 manifest | 파일 존재·크기와 중복 핵심 3개 해시 확인; 31 GB 전량 재해시는 하지 않음 |
| `data/local/malecns-full` | 199,713개 non-Glia annotation의 incoming CSR | 미분류 body 포함, 게임용 부호 가정 |
| `data/local/malecns-neurons166k` | superclass가 지정된 166,700개 노드의 incoming CSR | 좌표 없음, 0 부호는 미확정 효과이며 연결 부재가 아님 |

성체 수컷 CNS 자료다. 공유 대화의 유충 Kenyon 64개 전사 부분망과 같은 표본으로 합치지 않는다.
파일·스키마·결측 및 전체 CNS 입력의 적격성은 별도 [MaleCNS 원장](malecns_inventory.md)에 정리했다.

## MaleCNS 후속 분석 (2026-09-14)

자료 ID `malecns-analysis`로 전체 행의 범주 집계 배열, 구조 결과, type source-LOO,
48회 label 대조, 실행 notebook·HTML·그림 3개를 등록했다. 원자료의 새 다운로드가 아니라
보유 MaleCNS v1.0에서 계산한 파생물이다. 배열은 `data/local/malecns-analysis/`,
작은 결과·소스·그림은 `verify/MaleCNS/`에 있다. 질문·수식·양성/음성 관측·해석 한계는
[별도 분석 원장](malecns_structure_findings.md), 서술은 [논문 결과 장](../paper/6_뇌/13_MaleCNS_전체망_기하와기억/05_실제전체망_첫관측.md)에 둔다.

후속 `raw-dyad-return-v1`은 전량 고유 dyad·역방향 연결·실제 ID 두 단계 경로를 계산한
캐시 3개, 결과 JSON, 실행 notebook·HTML·그림 2개를 보관한다. 중복 dyad는 0개이며
모든 원시 분절은 정렬 캐시에 남아 있다. 방법·분모·해석 한계는
[ID 경로 원장](malecns_dyad_return_findings.md)에 별도로 둔다.

2026-09-15 등록한 `hidden-walk-v1`은 같은 전량 연결의 active 희소 전이·terminal 경계·
source 사상·27쌍 probe 궤적의 NPZ 4개와 완료 JSON이다. `hidden-walk-companion-checked-v1`에
실행 notebook·HTML·검수 그림 3개를 따로 등록했다. 초기 그림의 공유 y축 잘림은 원자료나
수치 결과를 바꾸지 않고 교정했으며, 기존 5개 산출물은 `hidden-walk-companion-initial-v1`에
현재 읽기본으로 부적합한 이유와 함께 보존한다. 해시 등록은 파일 정체성 확인이지 과학적
적격성 판정이 아니다. 수치·음성 사례·관측 범위·검수 이력은
[숨은 경유와 미래 정보 원장](malecns_hidden_walk_findings.md)에 별도로 둔다.

같은 날 `observation-memory-v1`에 60출력·투영 기억의 결과 JSON과 NPZ를 등록했다.
검수 notebook·HTML·그림 3개는 `observation-memory-companion-checked-v1`, 초기 눈금
겹침을 보존한 읽기본 5개는 `observation-memory-companion-initial-v1`로 구별한다.
전량 관측 재현·이력 길이·초기항·음수 예측의 실패는
[관측과 이력 축약 원장](malecns_observation_memory_findings.md)에 둔다. 추가 원자료
다운로드는 없으며 기존 raw 연결·흡수 경계 연산자를 그대로 재사용했다.

후속 `connection-fisher-v1`에는 고정 초기분포에서 세 공유 log-efficacy 좌표를 바꾼
전량 Jacobian·endpoint Fisher·여섯 유한차분 대조의 완료 JSON과 NPZ를 등록했다.
정규화의 공통 배수 영방향, 관측별 수치 rank, terminal 압축 셀 수의 필드명 한계와
과학적 주장 범위는 [연결 효능 원장](malecns_connection_fisher_findings.md)에 둔다.
전체 연결을 보존한 세 좌표의 L0 분석이며 모든 연결을 독립 파라미터로 탐색한 것은 아니다.
검수 notebook·HTML·명칭을 명확히 한 summary·그림 3개는
`connection-fisher-companion-v1`에 등록했다. 코드 셀 4개와 PNG 시각 검수는 완료했지만,
사용 가능한 브라우저가 없어 HTML 브라우저 레이아웃 검증은 하지 않았다.

재다운로드는 누락·손상·다른 판본·재개 불가 등 이유를 기록하고 진행할 수 있다. 재검토도 가능하며 질문·이유·데이터 ID·이전/새 결과를 분석 기록에 남긴다. 자세한 기준은 [데이터 관리 규칙](../.codex/harnesses/data_policy.md)을 따른다.

## MaleCNS 이력 정보 계산 완료 (2026-09-19)

같은 원자료와 `connection-fisher-v1` 입력을 재사용해 54개 고정 초기분포의 인접 관측쌍과
전체 raw 경로 Fisher를 계산했다. `history-fisher-v1`에 결과 JSON·NPZ·소스·검사 4개,
`history-fisher-companion-v1`에 실행 notebook·HTML·summary·생성기·PNG 4개, 합계 12개를
등록했다. 새 다운로드는 없다. 입력·소스·검사·부모·배열 해시 12개를 재대조했고,
notebook 실행과 그림 4개를 검수했다. 전체 HTML의 브라우저 레이아웃은 미검수다.
판정은 접촉 정규화 모형의 L0이며 실제 가소성이나 기억량이 아니다. 원 질문·정확한
관측 범위·수치·산출물 해시와 다음 조건은 [이력 정보 원장](malecns_history_fisher_findings.md)에 둔다.

## Allen 회복간격 측정 진단 (2026-09-19)

`allen-synphys-analysis/recovery-baseline-extrapolation-v1`은 실험 `1574292898.139`의
보유 60개 NPZ와 NWB 캐시를 재사용한 후속 진단이다. 새 측정 소스·검사·결과와
실행 notebook·생성기·PNG, 합계 6개를 등록했다. 새 다운로드는 없다. 기존 480반응을
재현하고, 두 target의 40개 저장 명령과 200개 source 무자극 대조창을 확인했다.
짧은 pre 창의 선형 외삽은 전체 대조 RMS를 두 표적 모두에서 키웠으므로 기본 보정으로
채택하지 않는다. RMS는 생물학적 정답 대비 오차가 아니다. 질문·검증·정확한 수치와
범위는 [회복간격 측정 원장](allen_recovery_baseline_extrapolation_findings.md)에 둔다.

## Allen 순방향 파형과 기준선 감도 (2026-09-19)

`allen-synphys-analysis`의 `recovery-waveform-v1`과 `recovery-offset-sensitivity-v1`에
각각 소스·검사·결과 JSON·배열 NPZ 4개씩을 등록했다. 통합 실행 notebook·생성기·
PNG 3개는 `recovery-waveform-companion-v1`의 5개다. 합계 13개이며 새 다운로드는 없다.
50개 표적-시행을 시도해 입력이 확인된 43개를 포함했고 결손·자체 입력 7개를 보존했다.
첫 10시행의 초기 반응만 적합하고 뒤 10시행과 다른 회복 간격 3개를 예측했다.
공통 오프셋에서의 약화 후보 개선은 오프셋0 감도검사에서 회복 구간에 유지되지 않았다.
위상 민감도·검사·모든 분모와 생물학적 해석 한계는
[파형 비교 원장](allen_recovery_waveform_findings.md)에 둔다.

## Allen 무명령 상태와 조건부 예측 (2026-09-19)

`allen-synphys-analysis/recovery-causal-baseline-v1`에 소스·검사·결과 JSON·배열 NPZ
4개, `recovery-causal-baseline-companion-v1`에 생성기·실행 notebook·PNG 2개를 둔다.
합계 8개이며 앞 분석의 입력과 43/50 적격 표적-시행을 재사용했다. 새 다운로드는 없다.
무명령 앞 10시행만으로 교정한 기준선 위에서 고정·이력 효능을 비교했다. 양성 표적의
뒤 시행 회복은 상태만의 기준선보다 효능 후보들이 나빴다. 전체 파형 분석과 관측
예산이 다른 조건부 예측이며 실제 가소성이나 계량 추정이 아니다. 방법·수치·한계·
재현 명령은 [인과적 전압 상태 원장](allen_causal_voltage_state_findings.md)에 있다.

## Allen 발화 시각과 파형 대조 (2026-09-19)

`allen-synphys-analysis/recovery-source-timing-v1`과 `recovery-source-prefix-v1`에
각 소스·검사·결과 JSON·NPZ 4개를, `recovery-source-timing-companion-v1`에 생성기·
실행 notebook·PNG 3개의 5개를 등록한다. 합계 13개이며 기존 43/50 적격 표적-시행을
재사용했다. 같은 target 결과에서 source 시각과 과거 관측 허용 정책을 구별했다.
관측 차단으로 193/516 anchor가 20ms 이상 오래지는 문제를 별도 이전 관측 허용
조건으로 진단했고 원 결과를 보존했다. 새 다운로드는 없다. 초기·회복의 차이,
시각 대조·기전 계수의 불안정성·검증과 해시는 [발화 시각 원장](allen_source_timing_findings.md)에 있다.

## Allen 20Hz VC 전체 입력 확보 (2026-09-19)

`allen-synphys-ranges/r2.1-vc20hz-overlay-20260919`에 기존 캐시와 같은 원격 판본의
결손 139블록(9,109,504바이트)과 별도 manifest를 등록했다. 기존 캐시는 변경하지 않았다.
`allen-synphys-analysis/vc20hz-inputs-v1`의 소스·검사·결과 JSON·NPZ 4개와 합계144개다.
7시행42채널의 전체 배열과 명령을 확인했고, 실제 pulse 진폭은 시행·세포별60/120/150mV다.
DB access/QC 결합은 아직 불완전하다. 수집 근거·해시·검증·해석 한계는
[20Hz VC 입력 원장](allen_vc20hz_inputs_findings.md)에 있다.

## 해마 내용 재활성화 입력 진단 (2026-09-19)

`hippocampal-reinstatement/rey2025-processed-v1`에 미보유 공식 MCW/Box 자료 두 파일
(1,777,642바이트, CC BY4.0)을 등록했다. 부호화에서 선택된33유닛 중 회상22유닛을
제공하며 raw voltage·환자 대응·시행별 정오답·관측지원 마스크는 없다.
`rey2025-input-audit-v1`에는 소스·결과 두 파일을 등록했다. 1,169 neuron-trials와
728개 행동 키의 시간축·구조를 독립 대조했으며 복원 효과나 CE 기전은 적합하지 않았다.
추출 형식의 예외와 명목상 trial 시간 밖 기록은 [공개 자료 원장](hippocampal_public_data_findings.md)에 있다.

## 해마 보조자료와 발화 전 내용 판독 (2026-09-19 후속)

`hippocampal-reinstatement/rey2025-support-v1`에 공식 보조PDF·저자 code ZIP·
Table S1의 세션–환자 대응표·획득 경위·Range 예외 header의5개 파일을 보존했다.
앞 절의 ‘환자 대응 없음’은 MAT 자체의 초기 진단이며, 새 보조표에서 전체9명의 대응을
확보했다. 과거 등록과 입력 진단은 덮어쓰지 않았다. 보존 PDF/ZIP은 기존 Temp 수신물을
재사용했다. 조사 중 Range 요청이 무시되어13,809,303바이트가 전송되고8MiB 상한을
넘은 예외와 임시 payload 삭제·해시 미확보도 원장에 명시했다.

`hippocampal-reinstatement/rey-premention-v1`은 새 소스·검사·결과 JSON·배열 NPZ다.
회상 유의성으로 선별하지 않은22유닛에서 VP로만 적합한 내용 판독기를 평가하고,
반응 시각을 맞춘 두 시행의 동일 단서 상대창을 별도 대조로 둔다. 표본은 유닛→세션→
환자 순으로 묶으며 정오답·획득 범위가 미상이라는 제한을 유지한다.
10개 검사가 통과했고, 내용 구별과 확률 전이 실패를 함께 보존했다.
표본·방법·원값·해시는 [발화 전 판독 원장](hippocampal_premention_readout_findings.md)에 있다.

## 해마의 내용 전이와 story 조건 구별 (2026-09-19 후속)

`hippocampal-reinstatement/rey2025-story-metadata-v1`에 기존 Temp 원논문 XML과
story 의미의 확인사항2개를 보존했다. 새 다운로드는 없다. 네 story는 각기 다른 문맥이며,
실제 cue 내용과 반복의 절대시각·block은 공개 MAT에 없다.

`rey-story-transfer-v1`의 소스·검사·결과3개는 기존 VP score를 training story에서만
보정하고 남긴 story를 평가한다. Identity는22유닛, 같은 identity의 story 구별은 최소반복
조건을 충족한20유닛이다. 해마16유닛은 두 검사에 모두 남는다. 과거 자료를 이미 검토한
후향적 교차검증이며 환자 모집단의 새 독립 검증으로 취급하지 않는다.

`rey-story-transfer-attempts-v1`의 직렬화 실패 부분파일1개는 `location_only`로 등록해
완료된 결과와 구별했다. 실패파일의 보존 해시는 분석 원장에 둔다.
`rey-story-transfer-companion-v1`에는 생성기·실행 notebook·PNG2개·
별도 시각화 의존성 설치 report의5개를 둔다. 기존 plot 디렉터리가 비어 있어 cached wheel을
격리 Temp 위치에 설치했으며 생물 자료나 프로젝트 Python 설치를 바꾸지 않았다.
새 등록은 합계11개다. 내용 전이의 확률 개선과 사건 조건 구별의 미지지를 함께
[story 전이 원장](hippocampal_story_transfer_findings.md)에 기록했다.

## Allen 20Hz VC 측정 상태 결합 (2026-09-19 후속)

`allen-synphys-ranges/r2.1-vc20hz-medium-overlay-20260919`에 medium DB 결손64KiB
블록과 별도 manifest를 등록했다. 원격 ETag가 같은 범위이며 기존1,479블록은 유지했다.
`allen-synphys-analysis/vc20hz-measurement-state-v1`의 새 소스·검사·결과3개와 합계5개다.
21개 시행-세포의 holding·QC·embedded TP·252개 양의 pulse를 결합했다.

DB timestamp는 실험 노트 entry 시각이라 raw 첫 표본 시각과 다른 것으로 확인됐다.
TP baseline 전류로 공식 보정 전위를21/21 재현했고 raw clock만 반응 정렬에 사용한다.
최종 offline 실행의 추가 수집은0바이트다. 초기 검사·결합 오류와 수정, 실제 저항값,
정확한 수식 입력·해시·남은 한계는 [측정 상태 원장](allen_vc20hz_measurement_state_findings.md)에 있다.

## Allen 20Hz VC 명령 이력과 보상 설정 (2026-09-20)

기존 raw42배열과 측정 상태21행을 재사용했으며 새 다운로드는0바이트다.
`allen-synphys-analysis`에 다음6개 판본, 합계21개 파일을 등록했다.

| 판본 | 파일 수 | 보존 내용 |
|---|---:|---|
| `vc20hz-command-history-v1` | 4 | 최종 모형 소스·검사·결과·예측 NPZ |
| `vc20hz-command-history-label-attempt-v1` | 4 | 초기 조건명의 소스·검사·결과·예측 NPZ |
| `vc20hz-compensation-v1` | 3 | 수치 노트와 acquisition 결합 소스·검사·결과 |
| `vc20hz-compensation-comment-attempt-v1` | 2 | 초기 comment-only 소스·결과 |
| `vc20hz-history-companion-v1` | 4 | 생성기·실행 notebook·PNG2개 |
| `vc20hz-input-inspection-v1` | 4 | 선행 기술통계 소스·결과·PNG2개 |

모형은 source120mV 시행2·3 초기8개만 적합하고 회복·다른 시행을 평가했다.
5·6시행 자기 명령 변경은 AD8에만 해당하므로 초기 조건명을 중립적으로 고치고
표적별 진폭·변경 여부를 추가했다. 초기286개 예측 배열과 최종 배열은 동일한 SHA다.
이력 항의 일관된 평가 우위는 없었고 모든 선택 τ는50ms 후보 하한이었다.

보상 설정은 짧은 comment만으로3행 Off·18행 미상이던 초기 결과를 유지한 채
수치 labnotebook의 acquisition 행에서 Rs/whole-cell Off를21/21 확인했다.
Fast/slow 보상 capacitance는 실제 막 C 측정값으로 사용하지 않는다.

모형11개·보상 설정3개 검사가 통과했고 notebook은 저장 예측의1,176개 시행별 점수와
672개 집계를 다시 계산했다. 시도 보존·정확한 관측 예산·표적별 결과·다음 관측 조건은
[명령 이력 원장](allen_vc20hz_command_history_findings.md)에 기록했다.

## Allen 혼합 기록과 해마 단서 라벨 (2026-09-20 후속)

기존 후보 실험의 전체 electrode를 조사해4863의 IC4·VC1 동시 기록24시행을 찾았다.
네 방향의 모든 pulse·response를 유지하고 NULL인 pulse QC를 통과로 채우지 않았다.
보고된 연결121566에는 양 recording·response ex QC와 count1·유한 검출 시각을 만족하는
172개 후보가 있다. 실제 단일 AP·PSC 파형 검증은 다음 단계다.
[혼합 기록 원장](allen_mixed_clamp_findings.md)에 조건·한계·재현을 기록했다.

| Dataset / version | 파일 수 | 내용 |
|---|---:|---|
| `allen-synphys-ranges/r2.1-mixed-clamp-medium-v1` | 38 | 새37개64KiB DB 범위와 manifest |
| `allen-synphys-analysis/mixed-clamp-inventory-v1` | 3 | Mode 소스·검사·결과 |
| `allen-synphys-ranges/r2.1-mixed-clamp-pulses-v1` | 9 | 새8개64KiB DB 범위와 manifest |
| `allen-synphys-analysis/mixed-clamp-pulses-v1` | 3 | Pair·pulse·response 연결 소스·검사·결과 |
| `hippocampal-reinstatement/dandi001539-0.250815.1203-header-v1` | 29 | 공식 API·부분 NWB header·진단 |
| `hippocampal-reinstatement/figshare19620783-v3-labels-v1` | 183 | ZIP 부분 범위·라벨53개·HDF5 root·수집/진단 기록 |
| `hippocampal-reinstatement/odor-place-trial-labels-v1` | 3 | Offline 시행 연결 소스·검사·결과 |

합계268개다. 기존 medium/VC 캐시를 보존하며 Allen 새 범위는2,949,120바이트다.
DANDI는 API18,254바이트와18범위279,496바이트, Figshare는 전체 network body714,575바이트다.
각각 원본 전체 DB·NWB·ZIP·MAT를 받은 것은 아니다. Figshare v3와 DANDI 고정 판본의
CS39 day6 시행23개가 시각까지 정확히 일치했으며 냄새 좌/우10/13, 정답/오답20/3,
CA1/PFC 유닛2/9를 연결했다. 신경 spike 값·LFP·위치는 분석하지 않았다.
[해마 입력 원장](hippocampal_odor_place_input_findings.md)은 부분 보유 범위·라이선스·
전체 해시 미검증 경계와 냄새/목표 혼동을 설명한다. 새로운 기전 검증으로 세지 않는다.

## 혼합 원파형·측정 상태와 해마 전체 관측 범위 (2026-09-20 후속)

이번 보존은 아래11판본이다. 기존 성공 결과와 원자료 캐시는 유지했으며 부족한 범위만
별도 overlay로 받았다. 원파형 입력, 파형 진단과 측정 상태의 차이는
[혼합 파형 원장](allen_mixed_clamp_waveform_findings.md), 전체 해마 metadata·라벨 연결과
보류 조건은 [해마 세션 원장](hippocampal_odor_place_cohort_findings.md)에 기록했다.

| Dataset / version | 파일 수 | 내용 |
|---|---:|---|
| `allen-synphys-ranges/r2.1-mixed-clamp-raw-v1` | 376 | 새375개64KiB 원파형 범위·manifest |
| `allen-synphys-ranges/r2.1-mixed-clamp-state-raw-v1` | 4 | 수치 노트용 새3범위·manifest |
| `allen-synphys-analysis/mixed-clamp-inputs-v1` | 4 | 240배열 NPZ·입력 소스·검사·결과 |
| `allen-synphys-analysis/mixed-clamp-waveform-audit-v1` | 3 | 1,152사건 원전압/전류 진단 소스·검사·결과 |
| `allen-synphys-analysis/mixed-clamp-measurement-state-v1` | 3 | 120recording 측정 상태·명령 이력 소스·검사·결과 |
| `allen-synphys-analysis/mixed-clamp-waveform-figure-v1` | 3 | 그림 생성기·입출력 기록·PNG |
| `allen-synphys-analysis/mixed-clamp-input-diagnostics-v1` | 11 | 초기 metadata 예산 보충·순회 중단·노트 실패 진단 |
| `hippocampal-reinstatement/odor-place-observation-scope-v1` | 49 | 기존53라벨 범위·공식 논문/코드·후속 행동3MAT와 수집 기록 |
| `hippocampal-reinstatement/dandi001539-0.250815.1203-cohort-metadata-v1` | 670 | 38asset metadata·부분 NWB 범위·원래 epoch/참조/행동 보충 |
| `hippocampal-reinstatement/odor-place-cohort-labels-v1` | 3 | SHA 고정 offline cohort 연결 소스·검사·결과 |
| `hippocampal-reinstatement/odor-place-task-support-diagnostic-v1` | 3 | 보류3세션의 task 종료 불일치 진단·manifest |

총1,129파일이다. Allen 새 NWB 범위24,772,608바이트는 원파형24,576,000바이트와
수치 노트196,608바이트의 합이다. 전자는 초기 metadata4194304바이트를 포함한다.
행동 MAT3개는 기존 Figshare ZIP의6범위32,028바이트이며 CRC/SHA를 확인했다.
DANDI 신규 API/범위 본문은9,388,755바이트다. 이는 각 단계의 네트워크 본문이며
로컬 파생 JSON·NPZ나 별도 논문/코드 HTTP 수집을 포함한 총 통신량으로 표현하지 않는다.

원전압을 보면 시각 NULL인 count1 사건268개에도0mV 상향 통과가 있다. QC를 임의로
채우지 않았으며 파형 진단을 정확한 AP 개수나 분리된 PSC로 해석하지 않는다.
해마는38개 시작 시각 라벨 조합이 유일하게 연결됐지만 whole-trial task 범위까지
통과한35개·3,500시행만 canonical 성공이다. 3개 실패는 그대로 남겼고 마지막1·1·2개
시행의 task 종료 초과를 별도 진단했다. 당시 table 참조11개를 null로 분류했으나 후속
객체 동일성 검사에서 이름 없는 유효한 객체임을 확인했다. 이 오판은 아래 새 판본으로
정정하며 초기 등록 파일은 보존한다. 당시에는 spike·LFP·Position 값을 읽지 않았다.

초기 scope report 뒤의 행동 수집, 최초 metadata manifest 뒤의 보충 결과와 broad TP
순회 실패 후 예산 보충을 각각 구별한다. 등록 JSONL은 파일별 용량·SHA·출처·이유를
보존하며 전체 원격 NWB/ZIP/DB의 다운로드나 전체 해시 검증으로 승격하지 않는다.

등록 후11판본1,129파일 전부의 용량·SHA를 다시 대조했다. 기존 raw/medium/VC overlay와
Figshare 라벨의 부모 manifest4개도 고정 SHA와 일치했다.

## 관측 AP 예측과 해마 실제 값·참조 정정 (2026-09-20 후속)

기존 입력을 재사용한 [AP 조건부 전류 비교](allen_mixed_clamp_ap_prediction_findings.md)와
[해마 발화·위치·선택 결합](hippocampal_neural_behavior_inputs_findings.md)을 보존했다.
이번10판본273파일의 용량·SHA를 등록 후 모두 실제 파일과 대조했다.

| Dataset / version | 파일 수 | 내용 |
|---|---:|---|
| `allen-synphys-analysis/mixed-clamp-ap-prediction-v1` | 4 | 예측 소스·검사·결과·52배열 NPZ |
| `allen-synphys-analysis/mixed-clamp-ap-prediction-figure-v1` | 3 | 그림 생성기·영수증·PNG |
| `allen-synphys-analysis/mixed-clamp-ap-prediction-diagnostics-v1` | 6 | 초기758후보와 최종767사건의 별도 진단 |
| `hippocampal-reinstatement/odor-place-neural-position-budget-v1` | 5 | 초기23세션 HDF 주소·dtype·shape와 ZIP 예산 |
| `hippocampal-reinstatement/odor-place-neural-position-values-v1` | 238 | 23세션 실제 배열·DIO/NP와 원본 범위·수집 기록 |
| `hippocampal-reinstatement/odor-place-value-acquisition-attempt-v1` | 3 | 첫 수집 중단 소스·닫힌 로그·재사용32파일 SHA 대응 |
| `hippocampal-reinstatement/odor-place-neural-position-postcheck-v1` | 5 | 최종 오프라인 객체 동일성·위치·실제 선택 진단 |
| `hippocampal-reinstatement/odor-place-neural-position-postcheck-attempt-v1` | 3 | 이름 비교를 잘못 적용한 초기 진단 보존 |
| `hippocampal-reinstatement/odor-place-electrode-reference-identity-v1` | 3 | 38 electrode 참조의 객체 ID·주소 재검사 |
| `hippocampal-reinstatement/odor-place-region-reference-v1` | 3 | 참조 정정 소스·검사·canonical 결과 |

전기 비교는 초기160사건만 적합하고607사건을 평가했다. 실제 AP+순서 항은 보고된
연결의 같은 시행 회복에서 개선됐지만20/100Hz로 전이되지 않았다. 지수 발화 이력도
일관된 우위가 없으며 생리 상수·가소성·기억의 부재나 계량 입증으로 해석하지 않는다.
예측 검사는8개 통과했고 그림은 고정 결과만 사용해 생성·확인했다. 새 전기 다운로드는0B다.

해마 값의 누적 네트워크 본문은124,515,536B(초기53,743,816+후속70,771,720)다.
161요청은 초기24+후속137이며206·Content-Range·ETag·길이를 본문 수신 전에 확인했다.
원자료238파일의 로컬 크기125,174,266B와 네트워크 본문을 구별한다. 전체 NWB/ZIP이나
LFP는 받지 않았다. 같은8세션의 HDF를 초기 실패 뒤 재사용했고 collector의 후속 행동
진단 IndexError도 보존했다. 새 최종 진단으로 원자료 수집과 진단 성공을 구분한다.

23세션의967유닛,9,748,754spike,1,437,649위치 표본을 확인했다. 당시 지역 집계
CA1 398/PFC 494/OB 75는 행 해석 오류였으며 후속 원 tetrode 대응은677/290/0이다.
2,454시행 NP 시작·종료와 위치 관측지원은 모두 맞았고 실제 선택은2,353시행이 연결됐다.
CS41_01의101시행은 DIO와 NP 시간 불일치로 미해결이다. 위치의 세션 전체12개 큰 gap을
침묵·정지·보간으로 채우지 않으며 단서 종료 이후 모든 분석창의 검증은 아직 남아 있다.

**참조 판정 정정:** HDF 객체 `.name=None`은 null reference의 증거가 아니었다.
기존 캐시만으로38개 electrode 참조의 non-null·객체 ID·주소 일치를 확인했다.
이 첫 정정 당시에는 CA1/PFC 동시 기록34개, 네 칸 적격32개로 집계했고 추가9개는
값 미확보였다. 아래 tetrode 의미 정정으로35/33개이며 현재33개 모두 확보했다. 이전 등록의 ‘null11’ 및
‘strict23’는 당시 오류가 반영된 기록이다. 이를 새 결과로 정정했고 기존 파일은 바꾸지 않았다.
초기 spike target 진단의0개도 이름 비교 오류였으며 실제 객체 동일성은23/23이다.

정정 결과 SHA는 `784bbd1190639255c6a403d6b8b17f941076440a86494d9913bc854e9c020cc1`이고
관련7개 검사와 오프라인 실행을 한 번씩 수행했다. 신경 내용 판독이나 복원 기전 검증은
아직 수행하지 않았다. 데이터 준비와 해마 검색 가설의 지지를 구분한다.

## 원 tetrode 대응과 첫 조건부 선택 판독 (2026-09-20 후속)

[지역 정정](hippocampal_tetrode_region_findings.md)과
[선택 판독](hippocampal_choice_readout_findings.md)의18판본221파일을 등록하고
전부 실제 용량·SHA로 다시 확인했다. 기존 성공 결과의 소스·검사·NPZ와 입력 SHA도
등록 전에 대조했다. Dataset은 모두 `hippocampal-reinstatement`다.

| Version | 파일 수 | 보존 범위 |
|---|---:|---|
| `odor-place-neural-position-pending9-v1` | 105 | 추가9세션 범위 수집·배열·행동·실패·별도 postcheck |
| `odor-place-cell-tet-info-v1` | 27 | 원 cellinfo/tetinfo16개와 초기 지역 진단 |
| `odor-place-cell-tet-attempt-v1` | 19 | 최초 완료본 및 잘못된 중단 status를 그대로 보존 |
| `odor-place-window-support23-v1` | 5 | 최초23세션 관측지원·창 중복·unit 관측 범위 진단 |
| `odor-place-window-support32-v1` | 3 | 32세션의 공통 창·선택 지연·예비 분할 진단 |
| `odor-place-window-verification-v1` | 1 | count360개·위치120창 독립 검산 helper |
| `odor-place-input-index-v1` | 2 | 최초32세션의 고정 입력 manifest·생성기 |
| `odor-place-cs39-05-values-v1` | 24 | 새 적격 세션의8유닛·22시행 값과 수집/검사 |
| `odor-place-cs41-source-axis-v1` | 4 | CS41 day7 단일 epoch 축의 실패본과 정정본 |
| `odor-place-input-index-v2` | 2 | 전체33세션의 입력 manifest·생성기 |
| `odor-place-windows-v1` | 4 | 최초32세션 창 소스·검사·결과·배열 |
| `odor-place-tetrode-regions-v1` | 3 | tetrode 의미 정정 소스·검사·결과 |
| `odor-place-windows-complete-v1` | 4 | 전체33세션 창 소스·검사·결과·배열 |
| `odor-place-choice-readout-v1` | 4 | 첫 조건부 선택 판독 소스·검사·결과·예측 |
| `odor-place-cs33-spike-identity-v1` | 7 | CS33 원 MAT·범위·receipt·수집/대조 소스·결과 |
| `odor-place-cell-tet-attempt-correction-v1` | 2 | 최초 collector 완료와 중복 수집 확정 진단 |
| `odor-place-region-failure-diagnostic-v1` | 1 | CS41 지역 확인 실패를 드러낸 진단 helper |
| `odor-place-readout-verification-v1` | 4 | 독립 검산 helper·보존 helper/대응·등록 helper |

추가9세션 본문은44,516,815B/63요청, CS39_05는609,034B/7요청이다.
최초23세션 본문124,515,536B를 합친 신경·위치·DIO/NP 값 수집은169,641,385B다.
별도 cellinfo/tetinfo는 최초 collector가 timeout 뒤 완료됐는데 중단으로 오인해 재수집했다.
첫559,112B와 재수집559,112B의 합1,118,224B가 실제 본문이며 중복은559,112B다.
원래 잘못된 중단 status와 receipt를 보존하고 별도 정정했다. CS33 원 spike 대조는
단일 실행의17,371,935B/2범위다. 이 세 부류 합188,131,544B는 해당 값·진단 수집의
본문 합이며 metadata·문헌·코드 HTTP를 포함한 전체 연구 통신량이 아니다.

38개 NWB의 객체 참조는 유효하지만 정수 열을 표 행으로 읽은 지역 판정은 잘못됐다.
원 tetrode 대응으로684유닛의 지역이 달라졌고 전체 CA1/PFC는915/508이다.
과제 연결35세션의1,305유닛은 원 cellinfo/tetinfo area가 일치했다. CS33 네 날은
113유닛·1,179,435 spike가 원 MATLAB의 task epoch2/tetrode/cell과 고유하게 정확히
일치해 정수의 의미를 직접 확인했다. 다른 rat의 직접 event 동일성까지 확인한 것은 아니다.

적격33세션1,284유닛(CA1 847/PFC437),13,227,318 spike,1,970,967 위치 표본을 확보했다.
3,414시행 중 실제 선택3,232개가 연결됐고 CS41_01/02의182개는 시간 불일치로 미해결이다.
네500ms 창이 모두 유효한2,522개 중 시간 분할의 학습 네 칸까지 만족한27세션2,364시행,
8마리를 평가했다. 단서 종료 후의 현재 CA1/PFC 합동 모형은 행동 기준 대비
rat 동일가중0.040395nats/trial 개선됐지만 직전 시행 이력 추가는 네 창 모두 악화됐다.
유의성·내용 복원·인과·리만 계량은 미확립이다. 결과 JSON SHA는
`b8935bb96a307f485073ec22bc5c2372ae9949d0d39e2a3017b82a3a0d28743e`다.
관련 검사35개와 독립 gain432개·outer fold540개 검산을 구분해 보존한다.

## 목표 접근에서 단서로의 고정 판독 전이 (2026-09-20 후속)

[전이 원장](hippocampal_phase_transfer_findings.md)의5판본18파일을 등록하고 실제 용량·SHA를
전부 확인했다. Dataset은 `hippocampal-reinstatement`이며 원자료 신규 다운로드는0B다.
기존33세션을 재사용한 새 분석이다.

| Version | 파일 수 | 보존 범위 |
|---|---:|---|
| `odor-place-approach-support-v1` | 3 | 독립 관측지원·원 epoch별 적격 분모 진단 |
| `odor-place-transfer-method-review-v1` | 2 | 원문/운동 혼동과 readout Fisher 식별 조건 검토 |
| `odor-place-approach-windows-v1` | 4 | 접근창 소스·검사·결과·NPZ |
| `odor-place-phase-transfer-v1` | 4 | 단일 고정 전이 소스·검사·결과·예측 |
| `odor-place-phase-transfer-validation-v1` | 5 | 독립 점수/분할/원 특징 대조·보존/등록 helper |

3,414시행 중2,120개에서 선택 직전500ms와 단서 전후 네 창을 함께 사용할 수 있었다.
선택 미해결182개와 nosepoke/종료 뒤 창 겹침1,112개는 제외했다. 같은 원 source/task
epoch에서5개 시간 블록과±1 제외·학습 네 칸 조건을 적용하면26구간·18세션·1,817시행이다.
정상 길이 미로의 실제 평가 동물은4마리1,277시행이고, 짧은 stem의 CS44는540시행이다.

Approach만 적합한7개 모형의 같은 단계 보류 점수는 모두 단서 기준보다 좋았지만,
단서 전·초기·후기·종료 뒤로 그대로 옮긴 점수는 모두 나빴다. 신경을 더한 모형이
motion-only보다 덜 나빴다는 차이를 복원 근거로 채택하지 않는다. 단서/fold 내부 AUC와
오답의 실제 선택/지시 목표 점수는 별도 보존했고 기억 정보 전체의 부재를 주장하지 않는다.

새 검사5+8개와 독립 원 특징·분할·예측 검산을 완료했다. NPZ1,066배열의 지표와 계층
집계, source-train 정규화/계수의 전량 재적용 결과는 오차0이었다. Target 좌표/logit은
유한하므로 큰 손실을 수치 overflow로 처리하지 않는다. 결과 JSON SHA는
`966fd04f45c50910d95e881fc1c9cf4c33519c026f2129f70b116ee294829e52`,
독립 검산 SHA는 `e15decacf86aee4bded930f1a302c7550a37a281b22d43f03fa8b8b158d91987`이다.
조건부 Bernoulli Fisher의 rank1 결과는 관측식의 식별 한계이며 생물학적 리만 계량의 확증/반증이 아니다.

## 사람 해마 공동 시행 지원 (2026-09-20 후속)

[공동 시행 진단](hippocampal_population_support_findings.md)은 보유 Rey2025 MAT·README·
참가자 대응·입력 진단을 재사용했다. 새 다운로드와 모형 적합은 없으며,
`hippocampal-reinstatement`의 다음2판본6파일244,268바이트를 SHA 검증 후 등록했다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `rey-population-support-attempt-v1` | 3 | 121,915 | VP 필드 존재 출력 오류가 있는 초기 소스·결과·manifest |
| `rey-population-support-v2` | 3 | 122,353 | 실제 MAT 철자·참가자 SHA·덮어쓰기 거부를 적용한 진단 |

회상 해마16유닛·11세션·5명 중 공동 후보는3명·5세션이며 각2유닛이다. 공동282시행의
story별 배열 길이·mention 시각이 정확히 일치했고 기존 시간 조건 후보는276개였다.
초기/수정 판본의 분모는 동일하다. 세션3의 두 유닛은 같은 내용 선호이고4/7/8/18은
상보적이다. 이는 처리배열 결합의 지원이며 동시 획득 구간이나 독립 정보 차원의 증명은
아니다. Cue/내용 대응·정오답·coverage가 없어 숨긴 내용의 복원 판정은 미확립이다.
최종 결과 SHA는 `510610232a430a991b3548fdac13613fdba7a9e4e2e7d35bf65bb61ddef25a4c`다.

## Norman2019 회상 자료의 범위 수집 (2026-09-20 후속)

[Norman 입력 원장](hippocampal_norman_inputs_findings.md)은 미등록이던 공식
Zenodo3259369/FreeRecallSWRv1.0.0을 확인하고 작은71항목을 확보했다.
Dataset은 `hippocampal-reinstatement`이며 다음 판본은 실제 보유 파일의 SHA를 검증했다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `norman2019-metadata-v1` | 82 | 2,351,872 | 작은 원항목71개·README·ZIP목록·범위 영수증·수집 소스 |
| `norman2019-http-attempts-v1` | 6 | 10,393 | 초기403/본문0바이트 두 시도의 소스·상태·로그 |
| `norman2019-schema-attempts-v1` | 22 | 2,347,601 | 탐색용 schema 출력·소스와 직렬화 실패 기록 |
| `norman2019-mvpa-v1` | 7 | 402,471,286 | 완료된 MVPA MAT·범위 영수증·상태·수집/보존 소스·manifest |
| `norman2019-mvpa-chunks-v1` | 24 | 402,445,264 | 원 수신 위치에 보존한 압축 항목 조각 |
| `norman-mvpa-schema-v1` | 12 | 892,831 | MAT 변수·작은 metadata·상위 struct prefix, 두 실패 상태와 각 소스 |
| `norman-event-structure-v1` | 10 | 91,006 | DATAbyChannel 전체 typed 구조·F 대응·opaque table 경계와 첫 실패 |
| `norman-item-support-v1` | 3 | 277,751 | 사진 원 이름·제시 run·기록 묶음별 M2 유한 지원 |
| `norman-item-transfer-v1` | 5 | 289,387 | 고정 prototype 전이 소스·결과·manifest·명령·실행 로그 |
| `norman-event-input-inventory-v1` | 2 | 35,157 | 원 사건 시각64멤버의 보유 여부·범위·후보 조사, 네트워크0B |
| `norman2019-recall-ripples-v1` | 71 | 18,106,129 | 회상 원 MAT64개·범위 수집 기록·소스·보존 manifest |
| `norman2019-recall-ripple-parts-v1` | 129 | 11,870,409 | 수신한 로컬 ZIP 헤더·압축 본문128개와 manifest |
| `norman-ripple-clock-v1` | 6 | 161,298 | 제한 MCOS 시계 판독·행동 공통영역 검사·실패 기록·manifest |
| `norman-ripple-semantic-review-v1` | 3 | 44,890 | 사건 열·duration·amplitude 의미의 독립 검사와 manifest |
| `norman-mvpa-rta-tables-v1` | 8 | 83,246 | MCOS 구조·slot·RTA0/1/2 전체 문자열 판독과 manifest |
| `norman-rta-support-v1` | 3 | 9,430 | RTA2–M2 유한 지원의 정확 비교와 라벨 반복 수 검사 |
| `norman-transfer-scale-audit-v1` | 3 | 73,472 | 고정 부호화 평균·회상 스케일·α=0 원인 범위 진단 |
| `norman-event-observations-v1` | 5 | 1,354,895 | 공통 block 사건표·고정 소스·manifest·독립 원행 대조 |
| `norman2019-cortical-rta-attempts-v1` | 2 | 10,163 | 네트워크 전 inventory 키 오류의 실패 소스·상태, 본문0B |
| `norman2019-cortical-rta-pending-v2` | 2 | 소스9,712B + 위치 | all-visual 피질 RTA 단일 collector와 진행 폴더 |
| `norman2019-cortical-rta-v1` | 7 | 431,860,437 | 완료 MAT·collector·수신/실패 상태·영수증·manifest |
| `norman-cortical-rta-schema-v1` | 14 | 203,674 | 전체 typed 구조·RTA 표·A/B·설정·독립 보존 manifest |
| `norman2019-cortical-rta-parts-v1` | 28 | 431,865,433 | 원 수신 위치의 압축26조각·local header·manifest |

성공 수신 본문은576,700바이트로8MiB 상한 이내이며71항목의 해제 크기·CRC·SHA를
확인했다. 전체3,458,065,961바이트 ZIP의 MD5는 검증하지 않았다. 공식 license 표시가
비어 있어 임의로 라이선스를 붙이지 않는다. 직접 README와 ZIP 내부 README는 다른
파일로 보존했다. 민감 HTTP 헤더는 별도 가림 판본에만 정리했고 원본 로그는 유지했다.

회상 annotation·제시 item·검색 구간과 처리 ripple raster를 확보했지만 새 복원 효과를
적합하지 않았다. 약402MB MVPA 단일 항목도 조각 수집과 해제 검증을 완료했다.
사진별 내용 대응, 환자별 채널과 원 사건 단위를 확인한 뒤 사용한다.

후속 집중 진단은 `norman-behavior-support-attempts-v1`6파일596,539바이트와
`norman-behavior-support-v3`3파일331,394바이트로 구분했다. 정본은 고정51개 입력의
SHA/용량을 검사하고1,792개 제시 순서, Prompt 제외391개 recall 행의 다중집합을
확인한다. Mask64개는 미래 발화 시작3초 전부터 끝까지의 합집합과 XOR0이다.
이를 온라인 예측 입력으로 사용하지 않는다. 중복 초과량136과 현재 run 미일치8은
실제 시간순 반복이나 저자 오류 표지가 아니다. 결과 SHA는
`a02e3b122d5cc6380a7bedc45e0e1958d204781dd7bcd0b88f65e0ca6e11188a`다.

큰 MVPA의 진행 폴더/collector2개는 `norman2019-mvpa-pending-v1`에 별도 등록했다.
폴더는 수신 당시 `location_only`로 등록했다. 같은 exec handle64566이 exit0으로
끝나 MAT 크기·CRC·SHA를 확인한 후 위 완료 판본을 추가했다. 수신 본문은
402,445,776바이트이며 MAT SHA는
`7c776aafe3a44310e25946a36d7528cef15b7540b956bad69bec2c0e6e89ec70`다.
과거 진행 기록은 덮어쓰지 않으며 새 다운로드로 중복 시작하지 않는다.

MAT 구조에서212채널의16기록 라벨→15명 대응을 확인했다. M2는106×212×28이며
별도 사건 축이 없다. 초기 검사 당시 항목 집계 규칙과 DATAbyChannel 중첩 사건/시계
지원은 미확인이었다. Prefix 상위 필드의 키 부재만으로 내부까지 단정하지 않았다.
이번25개 범위 응답에는 ETag/Last-Modified가 모두 없으므로 이전 metadata 수신의
Last-Modified와 일치 검증했다는 주장도 하지 않는다.

후속 [사건 지원 검사](hippocampal_norman_event_support_findings.md)는 DATAbyChannel
전체를 순차 파싱해21개 숫자형 조건 집계 필드에 개별 event/run/item 축이 없음을 확인했다.
당시 미확인이던 RTA0/1/2는 [후속 판독](hippocampal_norman_observation_boundary_findings.md)에서
channel/item 문자열만 담고 있음을 확인했다.448개 원 후보 중 정확 이름
392개, B 접미사 미해결56개이며 정확 대응 중 M2 유한204·NaN188이다.
현재 후보 집합의 run은 부호화 run이고, 회상 당시 run의 배정이 아니다.

[고정 항목 표현 전이](hippocampal_norman_template_transfer_findings.md)는204관측·15명에서
주 평가창의 사람 균등 log-gain−0.123684 nats로 균등7후보보다 개선하지 못했다.
소스/결과를 그대로 보존했고 새 시간창이나 회상 자료 보정은 하지 않았다.

[후속 ripple 시계 검사](hippocampal_norman_ripple_clock_findings.md)는 원 사건3,577개와
행동0–150초 영역3,345개를 확인했다. 수집은 완료됐고 원 파일64개 모두 크기·CRC·SHA를
검증했다. 검출 코드가 미래/전역 신호를 사용하므로 온라인 predictable history는
미확립이다. 새 이력 효과나 복원 모형은 적합하지 않았다.

RTA2 고유3,176쌍과 M2 유한 지원은 정확히 같지만 개별 사건값·시계는 표에 없다.
고정 scale 진단은 M0의4반복 평균 정합성을 확인했고 α=0인16task가 부호화CV에서부터
균등 후보를 선호했음을 확인했다. 후속 보정·모형 적합 없이 기존 실패를 보존한다.

[공통 사건표](hippocampal_norman_event_observations_findings.md)는64개 block의
3,577개 ripple와470개 행동 주석을 원행 ID·시각·값 그대로 보존했다. 독립 대조는
입력66개와 신경/행동 원행 전량을 확인했다. Ripple와 기억 내용의 원인 배정은 하지 않았다.

별도 all-visual 피질 RTA는 기존 ZIP의 미보유 항목이다. 첫 preflight는 목록 키를
잘못 가정해 수신 전0B에서 끝났고, 수정 collector의 live session9502로 이어갔다.
진행 폴더는 `location_only`이며 완료 MAT나 해시 검증 결과가 아니다. 완료 여부는
실제 handle과 후속 완료 기록으로 확인하며 관측 timeout으로 새 수신을 시작하지 않는다.

후속 [피질 RTA 완료 검사](hippocampal_norman_cortical_rta_findings.md)에서 session9502의
실제 short-body 종료를 확인하고 session58748로 누락15,100B만 재개해 완료했다.
본문431,857,990B, 해제 MAT431,836,315B의 CRC·SHA를 확인했다. MAT SHA는
`095f8a3166e4f17385a9b8e74a4c612d52efef82a1d41ce4e335ef22cfe6bf01`다.
조건 집계·문자열 표와 A/B 숫자 벡터는 있지만 원 사건과 시각을 연결하는 typed key는
없었다. 수집은 완료됐으며 개별 ripple–피질 값의 연결은 여전히 미확립이다.

## CML catFR1 실제 EDF 표본과 시계 출처 (2026-09-20 후속)

[CML 입력 원장](hippocampal_cml_input_findings.md)은 OpenNeuro ds004809:2.2.0의
sub-R1004D/ses-0 metadata와 실제 EDF1초를 확인했다. Dataset은
`hippocampal-reinstatement`이며 snapshot commit은
`2af9e88db8d4517883dd71733b5be654aa80f088`, license는 CC0다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `cml-catfr1-metadata-v1` | 22 | 369,859 | 공개 고정판 metadata·공식 접근 경로·수집 소스 |
| `cml-catfr1-edf-probe-v1` | 9 | 502,708 | EDF 헤더·record250·전압 보정·원 TAL 보충 |
| `cml-clock-consistency-v1` | 4 | 28,995 | 사건739행과 EDF 시각 범위·native sample 비교 |
| `cml-clock-source-audit-v1` | 12 | 233,986 | 과거/후속 변환 코드와 시계 경계·정정 포인터 |

보존된 응답 본문은 합계955,590B다. EDF 전체2,074,246,832B나 전체파일 해시는
검증하지 않았다. 신경120채널 이름·순서·uV 보정은 확인했지만 사건표의 onset과
native sample이 다른 시계이므로 회상 전후 신호로 곧바로 해석하지 않는다.
과거 변환 코드와2026년 공식 onset 수정은 이 불일치를 설명한다. 정확한 snapshot
생성 코드 연결과 원 sample 정렬은 미확정이다. 원 annotation prototype 오류 및
list26 설명/정정 포인터 오류는 별도 보충으로 남기고 고정 결과를 덮어쓰지 않았다.

후속 [native sample과 내용 지원](hippocampal_cml_content_support_findings.md)은
공식 cmlreaders의 snapshot 이전 후보 코드까지 추적했다. Source EEG sample0부터
무crop·무resampling으로 EDF를 만드는 경로와 corrected eegoffset 보존을 확인했다.
Dataset의 원 correction 행·source identity·정확한 실행판 연결은 없으므로 독립
sync 확인과 구분해 native sample 계약 아래 제한적인 신호 읽기를 진행한다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `cml-sample-origin-audit-v1` | 11 | 125,178 | 역사적 cmlreaders·correction·sample0 출력 경로·원장 |
| `cml-content-support-v1` | 8 | 76,471 | 내용/목록/atlas 전량 지원·첫 쌍·입력 SHA·초기 실패 |
| `cml-edf-reader-v1` | 3 | 12,337 | 영구 판독 소스·관련 테스트·독립 실행 영수증 |

추가 source 수신100,087B 외에 내용 지원 분석은 네트워크0B다. REC_WORD24회 중
same-list15회/고유13항목, 이전 목록 침입6회, 목록 밖 침입3회를 구분했다.
111개 REC_WORD_VV는 모두단어 `<>`다. 같은목록 첫SPARROW 부호화/회상 쌍을
신호 열람 전에 고정했다. EDF+C reader는 보유 원 record250에서4검사를 통과했다.

[첫 실제 부호화–회상 읽기](hippocampal_cml_native_pair_findings.md)는 두 범위의
4,609,368B를 추가 수신하고120채널×각8,000표본을 추출했다. 모든12개 raw TAL이
기록 번호와 맞았고 유한값 실패·digital/physical rail은0이었다. 별도 코드가
선택5차신호×두구간의80,000값을 원 바이트에서 bit-exact 재구성했다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `cml-native-pair-readback-v1` | 9 | 5,484,854 | 고정 native 두 구간·120채널 요약·차신호 NPZ/PNG·수집/실행 기록 |
| `cml-native-pair-independent-check-v1` | 4 | 19,201 | 독립 byte parser·전량 재구성·원행 대조 |

Source-origin 조사와 이번 신호 수신까지 누적 보존 응답 본문은5,665,045B다.
Collector는 exit0으로 끝났고 진행 중 수신은 없다. 원 바이트/그림/metadata 대응의
검증이며 독립 행동 동기화나 기억 재활성화 효과의 검증은 아니다.

[같은 범주 안의 고정 판독](hippocampal_cml_withincategory_findings.md)은 입력 계획과
방법을 고정하고224개 EDF record를 추가 수신했다. 기존12개와 합쳐236개 record이며
새 본문86,041,536B, CML 누적 응답 본문91,706,581B다.29개206 응답을 모두 검증했고
수집은 exit0으로 완료됐다. 전체 EDF를 받거나 전체 파일 SHA를 검증한 것은 아니다.

| Version | 파일 수 | 바이트 | 범위 |
|---|---:|---:|---|
| `cml-withincategory-input-plan-v1` | 4 | 81,272 | 회상15행·부호화40행·후보4개·원 record 계획 |
| `cml-withincategory-method-review-v1` | 5 | 25,891 | 방법 검토·root 고정 결정·소스·manifest |
| `cml-withincategory-readout-review-v1` | 8 | 26,764 | 영구 소스/테스트·5검사 통과·검토·사전 파형 노출 보충 |
| `cml-withincategory-records-pending-v1` | 2기록 | 11,383의 소스 및 위치만 등록 | 수집 전 소스와 location_only 경로; 완료 파일 판정 아님 |
| `cml-withincategory-records-v1` | 38 | 86,187,285 | 완료 raw records·수집 영수증·정본 record index |
| `cml-withincategory-readout-run-v1` | 14 | 145,903 | 단회 실제 결과·특징·독립 확률/분모 검사·원 실행/보존 기록 |

실제 판독은1명·1세션·9목록·12항목이다. 피질140쌍 특징을 더한 확률의 목록 균등
추가 log-gain은−0.0176267661 nats로 제시 순서 기준을 개선하지 못했다. 정확히1회
실행했고 수정·재적합 없이 실패 결과를 보존했다. 해마 신호는 이번 판독 특징에
들어가지 않았으며 해마 검색의 인과 효과나 계량을 검증한 결과가 아니다.

## Bergmann 2026 KC 칼슘 가공표 (2026-09-23)

CE-BRAIN 게시본(`research/ce_brain_publication_20260919/`)은 이 CSV의 해시만 기록했고
로컬 사본·원장 기록이 없었다. 곡률 계량 검사(`research/ce_brain_curved_metric_20260923/`)를
위해 고정 커밋에서 처음 받았다. 자료 ID `bergmann-2026-kc`, 판본은 커밋 해시다.

| 항목 | 값 |
|---|---|
| 출처 | `aclinlab/bergmann-et-al@0b2da3f9c865626f8858881a468394c8eff68fa7:CorrelationAnalysis/all KC values.csv` (raw.githubusercontent.com, 공백은 `%20`) |
| 위치 | `data/external/bergmann_2026_kc/all KC values.csv` |
| 크기 | 17,682 bytes |
| SHA-256 | `5733b69eda14e5c557e784e96da917091877dc86a3a4a9c6026eae2520c8765a` |
| Git blob | `965d7e038fa23ba4226cda865d8802157f0d18c8` |

SHA-256·크기·Git blob이 게시본 `source_manifest.json`과 모두 일치했다. 유효값 1,540개,
완전한 7조건 벡터 220개, 음수 39개이며 42개 게시 목표 평균을 오차 0으로 재현했다.
저자 가공 칼슘 평균이며 새 동물·원시 영상·스파이크 자료가 아니다.
