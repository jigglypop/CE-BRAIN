# 내용 전이와 같은 내용의 이야기 구별

2026-09-19 후속. 목표는 해마의 내용 재활성화와 사건 주소 지정을 관측상 구별하는 것이다.
[직전 판독](hippocampal_premention_readout_findings.md)의 VP→회상 확률 전이 실패를 보존한 채,
일부 회상 story에서 확률을 보정하고 학습에 넣지 않은 story를 평가한다. 같은 identity를
공유하는 두 story의 구별은 별도 질문이다. 이 단계는 CE의 공통 전기·이력·검색 구조 중
**검색 시 출력분포의 예측 조건**을 좁힌다. 생리학적 전달식이나 리만 계량의 완성을 뜻하지 않는다.

## 1. 실제 story 설계와 가능한 해석

[원논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC11781864/)의 네 story는 각각 다른 전체
문맥이다. R1/NR1은 같은 문맥의 두 identity가 아니다. 21세션 중5세션은 identity가
장소이고 두 story의 사람이 다르다. MAT에는 cue 이미지·사건의 when/where/who/what
내용·block ID·절대시각·story 사이 제시 순서가 없다. 저장 행의 시간 순서도 확정하지 않는다.
세션별 identity partition도 달라 실제 유닛별 R/NR story index를 사용한다.
구체적 근거와 보존 XML은 [공개 자료 원장](hippocampal_public_data_findings.md)에 있다.

따라서 이번 identity 전이는 같은 대상이 다른 story 조건에서도 구별되는지를 보는
같은 유닛·세션 안의 후향적 교차검증이다. 공유 문맥을 통제한2×2 요인 효과, 새 환자에
대한 전이나 독립 전향 실험이 아니다. Story 구별이 성공하더라도 고유 cue·발화 준비·
공통 입력을 해마의 사건 주소와 동일시하지 않는다.

## 2. 판독식과 분할

직전 고정 VP 모형의 회상 count에 대한 log odds를 s라 한다. 회상 학습 story에서만
계산한 class 동일가중 평균·표준편차로 z=(s−μ)/σ를 만든다. 비교 모형은

\[
P(Y=1\mid z)=\operatorname{sigmoid}(a z+b),\qquad a\geq0
\]

이며 VP에서 정한 반응 방향을 유지한다. 학습 목적은 두 class의 평균 log loss에
\(\|\theta\|^2/(2n_{train})\)를 더한 것이다. Intercept도 같은0 중심 패널티를 받는다.
상수 특징의 slope는0으로 고정한다. 정규화 강도·창·임계값 격자 탐색은 하지 않았다.
분류 순위의 우위를 확률의 정확성으로 바꾸어 부르지 않도록 log-score gain과 Brier를
함께 평가한다. 단순히0.5로 수축하는 것만으로도 기존 잘못된 확률보다 나아질 수 있으므로
동일확률 기준 대비 gain이 양수인지 먼저 확인한다.

Identity 검사는 각 유닛의 R 한 story·NR 한 story를 남기고 다른 두 story로 학습하는
4개 fold다. 각 시행이 두 번 평가되는 겹친 fold이므로 독립 실험4개로 세지 않는다.
비교는 고정 VP·보정 VP·log mention 시각만·보정 VP와 시각·단서 전 보정 VP·동일확률이다.
시각 계수는 양/음 모두 허용하고 VP 점수 계수만 비음수다. 모든 표준화·학습은 해당
training fold 안에서 수행하며, held feature·label을 바꾸어도 fit이 불변인지 검사했다.

같은 identity의 두 story 검사는 각 story의 저장 반복을 앞/뒤 절반으로 나누고 양방향으로
평가한다. 이때 slope 부호는 story 번호에 의미가 없으므로 제한하지 않는다. Spike count,
log mention 시각, 둘의 결합, 단서 전 count와 시각을 비교한다. 각 story에 최소4개의
적격 반복이 있어야 해 학습·평가에 각각 최소2개를 둘 수 있다. 이 규칙은 결과를 본 뒤
완화하지 않았다. `19:92:class4`, `19:93:class2` 두 편도체 유닛은 story3의 반복이2개여서
이 branch에서만 제외하고, identity 전이에는 그대로 포함했다. 제외 사유를 출력에 보존했다.

각 fold의 class→유닛의4fold→세션 안 유닛→환자 안 세션→환자를 같은 비중으로 평균한다.
시각만의 모형 대비 신경량 추가 이득은 **동일 held fold**의 log-score gain 차이다.
이것은 특정 선형 log-latency 보정 뒤 남는 예측 차이며 모든 행동 교란의 제거가 아니다.
Mention 정렬 자체가 나중에 알려지는 발화 시각을 사용하므로 실시간 온라인 예측기가 아니다.

## 3. 결과

Identity 전이는22유닛·14세션·6명이며88fold에서1,095개 neuron-trial을 각각 두 번
평가했다. 같은 identity의 story 구별은20유닛·13세션·6명,80fold에서1,053개
neuron-trial을 각각 한 번 평가했다. 해마는 두 검사 모두16유닛·11세션·5명이다.
행동 시행은 전체 identity 코호트에서680개이며 유닛·fold 중복을 새 표본으로 세지 않는다.

아래는 해마의 환자 동일가중 기술통계다. Log-score gain은 ln2−log loss로 양수여야
50:50 예측보다 좋고, Brier는 작을수록 좋다. Accuracy는 주어진 두 조건 판별이며
일상적 기억의 복원 성공률이 아니다.

| 다른 story의 identity 판독 | Log-score gain | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| 동일확률 | 0 | 0.2500 | 0.5000 | 0.5000 |
| 고정 VP | −0.4942 | 0.2745 | 0.6486 | 0.8107 |
| 일부 story로 보정한 VP | **+0.1802** | **0.1704** | 0.7383 | 0.8085 |
| 회상 시각만 | +0.0274 | 0.2324 | 0.5857 | 0.6114 |
| 보정 VP와 회상 시각 | +0.2248 | 0.1526 | 0.7846 | 0.8420 |
| 단서 전 VP 보정 | −0.0117 | 0.2552 | 0.4772 | 0.4845 |

보정 VP의 양의 점수는 무조건0.5로 수축한 것 이상의 예측 이득이다. 신경점수와 시각의
결합은 시각만보다+0.1974nats/trial 좋았고 환자5명 중4명에서 양수였다. P1은−0.0278로
나빴다. 전체6명에서도+0.1817,6명 중5명에서 양수였다. VP 방향 slope가0 경계에 있던
fold(≤1e−8)는 보정 VP14/88,VP와 시각13/88,단서 전 보정41/88이다. 모든 유닛이 같은 관계를
보이는 것으로 해석하지 않는다. 판정은 **후향적 같은 유닛 내 내용 전이의 확률 예측 지지**다.

| 같은 identity의 두 story 구별 | Log-score gain | Brier | Accuracy | AUC |
|---|---:|---:|---:|---:|
| 동일확률 | 0 | 0.2500 | 0.5000 | 0.5000 |
| 발화 전 spike count | −0.0357 | 0.2631 | 0.5519 | 0.5646 |
| 회상 시각만 | −0.0559 | 0.2692 | 0.5364 | 0.5660 |
| Count와 회상 시각 | **−0.0977** | **0.2823** | 0.5688 | 0.5961 |
| 단서 전 count와 시각 | −0.0871 | 0.2795 | 0.4990 | 0.5560 |

Story 조건에서는 count 추가가 accuracy를0.0325 높여도 proper log-score gain은
시각만보다0.0418 나빴다. 참가자별 증가분은5명 중2명만 양수였고 전체6명에서도
−0.0487,2명만 양수였다. **같은 내용의 사건 구별은 이 count 판독기에서 지지되지 않았다.**
이것을 전체 해마의 문맥 정보 부재로 확대할 수 없다. 선택된 유닛·단일유닛 count·짧은
회상 창·선형 모형·작은 반복수의 경계가 있고, 시간 패턴·집단 상호작용·관측하지 않은
뉴런은 평가하지 않았다. 주소 지정 기전의 증거도 얻지 못했다.

## 4. 계량과 검색 구조에 연결할 때의 조건

판독 점수를 연속좌표 z로 보는 **통계모형**에서 p=σ(aᵀz+b)의 score는 (Y−p)a다.
따라서 그 출력의 Fisher는

\[
g(z)=p(1-p)aa^T
\]

다. 이 식은 조건부 유도이며 뉴런의 물리적 상태 좌표를 측정한 결과가 아니다.
양의 slope 보정은 판별 순위를 유지하면서도 p와 g를 바꿀 수 있다. 그래서 AUC가
높다는 이유만으로 보정되지 않은 출력분포의 계량을 생물학적 구별성으로 채택하지 않는다.
좌표가 둘 이상이면 단일 이진 판독의 g는 rank가 최대1이어서 전체 상태공간의
양의 정부호 리만 계량을 식별하지 못한다. 관측 가능한 방향과 추가 독립 관측이 필요하다.

현재 결과가 좁힌 구조는 **내용의 재활성화 → 보정 가능한 내용 판독**까지다.
사건 색인과 내용의 결합, 이력에 따른 전기적 관계 변화, 검색의 방향성을 같은 자료에서
잇는 단계는 남아 있다. 다음에는 내용과 문맥을 함께 관측한 집단 자료와 동시 기록·
기록 범위·실제 cue 대응을 확인해야 한다. 이 코호트의 모형 수만 늘려 전체 기전을
확증하는 방향으로 진행하지 않는다. Allen의 작동점·명령·측정모형과도 아직 결합하지 않았다.

## 5. 검증과 보존

입력은 기존22유닛·1,095 neuron-trials·680 행동 시행과 시간 제한을 재사용했다.
원래 선별·시계·정오답·관측지원 한계는 유지된다. Frozen VP 소스·결과·배열의 해시와
각 count·posterior의 exact parity를 확인하는 코드를 포함한다. 이전 결과를 덮어쓰지 않는다.

첫 실행은 story별 최소4반복 조건에 막혀 출력 없이 종료됐다. 이후 부적격 branch만
명시적으로 제외하도록 수정했다. 두 번째 실행은 NumPy 정수의 JSON metadata 직렬화에서
실패했다. 불완전266,532바이트 파일을 별도 `.json.part`로 보존했으며 SHA-256은
`b69912267987baeb2cc0f190f73c4421cb3278a27c62233cdd282a7ff9b87d31`이다.
이 파일은 유효한 분석 결과가 아니다. 최종 코드는 Python 정수로 변환하고 파일 생성
전에 전체 직렬화를 끝낸다. 두 구현 실패를 과학적 가설의 실패나 성공으로 세지 않는다.

최종 [소스](../verify/Q-NPF-04/hippocampal_reinstatement/rey_story_transfer.py)와
[검사](../tests/test_rey_story_transfer.py)는 관련11개 검사가 통과한 뒤 실행했다.
분할의 교집합·평가 횟수·held data 변경에 대한 fit 불변·상수/역방향·극단 logit·
class 동일가중·계층집계·반복 부족·직렬화를 포함한다. 독립 검산에서 frozen source/result/
NPZ 해시, count와 posterior의88개 exact 배열 비교, 모든 fold의 train/test 분리와 평가
중복 횟수가 일치했다. 고정 VP의 집계도 이전 결과와 일치한다.

[결과 JSON](../verify/Q-NPF-04/hippocampal_reinstatement/rey_story_transfer_result.json)은
3,392,764바이트이며 각 fit·held key·label·예측 확률을 보존한다.

| 파일 | SHA-256 |
|---|---|
| 최종 소스 | `2c987c55f309d862870e98b9ddc4a0b7757102398afd5f842bb0496dd6b2a354` |
| 최종 검사 | `48043f0e3e2985e0acfabd8f02fee176f9c2a9ed12d490f808eefbb1fe99d973` |
| 최종 결과 | `3ca0c24580cd6360a884189c6f3802bdb64123d0647d74ed2a88f2896e7f2ca6` |

실행은 보존 실행기 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`의
`pytest tests/test_rey_story_transfer.py -q`, 이어서
`python verify/Q-NPF-04/hippocampal_reinstatement/rey_story_transfer.py`다.
Python3.11.9,NumPy2.4.6,SciPy1.17.1이며 기존 결과 덮어쓰기를 거부한다.

[실행 notebook](../verify/Q-NPF-04/hippocampal_reinstatement/rey_story_transfer.ipynb)은
코드4셀을 순서대로 실행했고 오류 output이 없다. 모형을 다시 적합하지 않고760개
저장 예측 배열의 확률합·log loss·Brier를 검산했다. [확률 점수 그림](../verify/Q-NPF-04/hippocampal_reinstatement/figures/rey_transfer_proper_scores.png)과
[참가자별 추가 이득 그림](../verify/Q-NPF-04/hippocampal_reinstatement/figures/rey_transfer_incremental.png)의
축·범례·부호·가독성을 직접 확인했다. 작은 점은 참가자 요약이며 신뢰구간이 아니다.
저장 notebook을 계산 재실행 없이 Temp HTML로 변환해 headless Chrome으로 렌더링했고,
요약·방법·지표 표·두 그림·결론의 한글과 잘림을 확인했다. 검토용 미리보기는
`ce-rey-story-notebook-preview-20260919-cropped.png`이며 영구 계산 증거를 대체하지 않는다.

Notebook 실행에는 보존된 `ce-malecns-notebook-deps-20260914`의 nbformat5.11.1,
nbclient0.11.0,ipykernel7.3.0을 재사용했다. 과거 plot 의존성 디렉터리는 실제 모듈
파일이 없어 사용하지 못했고, [Matplotlib3.10.6](https://pypi.org/project/matplotlib/3.10.6/)과
NumPy2.4.6 및 의존성을 `ce-rey-story-plot-deps-20260919`라는 별도 Temp에 설치했다.
pip는 cached wheel을 사용했으며11패키지의 URL·해시·버전은
`data/local/hippocampal-reinstatement/rey-story-transfer-companion-v1/plot_install_report.json`에 보존했다.
프로젝트 설치를 변경하지 않았다. 생물 입력은 모두 기존 보유 자료다.

생성기 실행 시 `PYTHONPATH`에 위 notebook/plot 두 경로를 지정하고
`CE_PYTHON_WRAPPER`는 같은 보존 실행기로 둔다. Windows에서 중간 wrapper를 통해
전달된 Jupyter parent HANDLE이 유효하지 않아 kernel이 종료되는 문제를 확인했다.
정책 실행기는 유지하며 kernel의 HANDLE polling 대신 NotebookClient의 수명 관리와
Jupyter message 프로토콜을 사용했다. 최종 실행 뒤 kernel 잔류는0개였다.
