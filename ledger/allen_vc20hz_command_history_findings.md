# Allen 20Hz VC: 조건부 전류 예측에서 명령 이력의 기여

2026-09-20 후속. [측정 상태 결합](allen_vc20hz_measurement_state_findings.md)의
동일 실험 `1574292898.139`, 시행0–6을 사용했다. 질문은 **현재 반응 직전의 전류를
관측한 뒤에도 과거 source 명령이 다음 전류 파형의 예측을 개선하는가**이다.
이력 항의 일관된 평가 우위는 얻지 못했다. 이 결과는 생물학적 가소성이 없다는
증명이 아니며, 추정 계수를 시냅스 전도도나 리만 계량으로 대입하지 않는다.

## 입력과 측정 회로

기존42개 배열과21개 recording/TP 결합을 재사용했다. 이번 단계의 추가 다운로드는
0바이트다. Source는 device5/AD9, 표적은 보고된 연결의 device4/AD8과 보고된 연결이
없는 device2/AD2다. 코드의 positive/negative는 이 연결 표기이며 전류 부호·흥분성/
억제성이나 연결 부재의 확정을 뜻하지 않는다. Source Vm/AP 채널은 없다.

파형을 먼저 관찰한 후향적 탐색이다. 모든 시행을 미리 보았으므로 적합에서 남긴
시행을 새로운 맹검 생물학적 검증으로 부르지 않는다. 원전류10,623,942표본은 모두
유한했다. 극값은1–2회 출현하고 같은 값의 최장 반복은7표본이었다. Flat rail의
뚜렷한 흔적을 찾지 못했지만 아날로그 clipping이 없다고 보증하지 않는다.

AD8에서 source 명령 시작과1.5ms 종료에 큰 반대 부호의 경계 반응이 보였다.
12개 pulse를 평균한 원파형과 점수화한0.5ms 평균을 별도 그림으로 보존한다.
경계 뒤 [2,10)ms 평균 변화는 AD8 약−0.452pA, AD2 약−0.015pA였다. 이 작은
평균과 명령 경계만으로 시냅스 전류를 식별하지 않는다. 자기 자극 직후의 큰 회복도
존재하며, AD8 자신의 마지막 pulse 종료에서 source 시작까지는250ms다.

DB에 없던 하드웨어 설정은 같은 NWB의 acquisition과 수치 labnotebook에서 확인했다.
21개 acquisition 모두 fast/slow capacitance 설정은 있지만 표준 Rs/whole-cell
보상 dataset5종은 `missing_fields`로 표시된다. 결측을0으로 해석하지 않았다.

수치 노트는1,024×172×9 구조다. 선택한 시행의51개 raw row 중 `EntrySourceType=0`
35개만 acquisition 설정으로 사용하고 type1의16개는 섞지 않았다. 각 시행·device의
필드별 유한값을 모으고 중복 모순은 오류로 처리한다. Global 열의 유한값이 있으면
우선하며 원래 row index도 결과에 남긴다. 선택한51행의 EntrySourceType에는 결측이 없다.

이 수치 노트에서 **RsComp Enable=0, Whole Cell Comp Enable=0이21/21**이었다.
짧은 acquisition comment는 시행0의3행만 이를 명시하고 나머지18행에는 해당 항목이
없다. 결과는 comment의3 False/18 null과 수치 노트의21 False를 따로 보존한다.
시행0의 설명을 뒤 시행에 단순 전파한 판정이 아니다. 설정 의미는
[MIES 필드 정의](https://alleninstitute.github.io/MIES/labnotebook-descriptions.html)를 참조한다.

Rs correction/prediction 설정도0이다. 비활성 whole-cell capacitance/resistance
숫자를 실제 막 C나 access R로 쓰지 않는다. Fast/slow capacitance 값은 보상 설정이고
독립적인 enable 항목은 확인하지 못했다. Rs bandwidth의 저장값1.02047998046875도
물리적 cutoff로 대입하지 않았다. 앞선 DB의 실제 막 C·τ 결측은 그대로다.

## 모형과 평가 분할

Source120mV의 시행2·3, 각 초기8개 pulse로만 template를 적합했다. 시행4는 같은
명령의 뒤 시행, 시행5·6은 뒤 시행 묶음, 시행0·1은 앞선60mV 명령 조건이다.
5·6에서 자기 명령이150mV로 바뀐 표적은 AD8뿐이다. AD2 자기 명령과 source는
120mV를 유지한다. 명령 크기와 시행 순서가 결합돼 있어 독립적인 진폭 개입이 아니다.

각 pulse의 [−10,−2)ms를0.5ms로 평균해 일정 수준(`level`) 또는 선형 외삽(`linear`)
기준선을 만든다. 두 정책은 각각 보고하며 평가 후 좋은 정책만 골라 성공으로 세지
않는다. 현재 pulse 이후의 전류로 자기 기준선을 맞추지 않는다. 다만 앞 pulse의
늦은 반응이 다음 pre-window에 들어갈 수 있어 명령만으로 하는 예측은 아니다.

점수창은 [2,40)ms의76개 bin이고 짧은 [2,10), 긴 [10,40)ms도 보존한다.
[0,2)ms의 경계 반응은 점수에서 제외하지만 모든 측정 artifact가 제거됐다는 뜻은
아니다. 초기8개와250ms off-gap 뒤4개를 별도 집계한다.

\[
u_n=\Delta V_n/(0.12\mathrm{V}),\qquad h_0=0,\qquad
h_n=e^{-(t_n-t_{n-1})/\tau}(h_{n-1}+u_{n-1}).
\]

\[
\widehat I_{fixed,n}(r)=B_n(r)+u_n a(r),\qquad
\widehat I_{history,n}(r)=B_n(r)+u_n[a(r)+h_n b(r)].
\]

각 lag의 계수는 부호 제한 없는 최소제곱으로 적합한다. 이력은 시행마다0으로
초기화하며 명령을 절반으로 줄이면 고정 항은1/2, 이력 항은1/4이 된다는 수송 가정을
포함한다. τ 후보는50/150/500/1500ms다. 시행2와3 중 하나로 적합하고 다른 하나의
초기8개·전체 점수창을 평가하는 내부 교차검증으로 τ를 고른 뒤 두 시행에 재적합했다.
회복4개와 다른 시행은 계수·τ 선택에 쓰지 않았다. Training/initial은 적합값이며
training/recovery만 같은 시행 안에 남긴 반응이다.

## 실제 평가 결과

아래는 일정 수준 기준선과 전체 [2,40)ms의 RMSE(pA)다. 각 집계는 시행별 MSE를
같은 비중으로 평균한 뒤 제곱근을 취한다. 동일 세포의 pulse와 겹치는 창을 독립
동물 표본이나 독립 성공 횟수로 세지 않는다.

| 표적·시행 | 구간 | 기준선만 | 고정 template | 이력 template |
|---|---|---:|---:|---:|
| AD8, 4 | 초기8 | 2.2428 | 2.2222 | 2.2082 |
| AD8, 4 | 회복4 | 2.8144 | 2.8906 | 2.9262 |
| AD8, 5–6 | 초기8 | 1.5859 | 1.6624 | 1.6690 |
| AD8, 5–6 | 회복4 | 1.0610 | 1.1999 | 1.2147 |
| AD8, 0–1 | 초기8 | 1.0187 | 1.0446 | 1.0491 |
| AD8, 0–1 | 회복4 | 0.9016 | 0.9119 | 0.9415 |
| AD2, 4 | 초기8 | 0.8488 | 0.8696 | 0.8802 |
| AD2, 4 | 회복4 | 0.8399 | 0.9141 | 0.9467 |
| AD2, 5–6 | 초기8 | 0.8809 | 0.9055 | 0.9321 |
| AD2, 5–6 | 회복4 | 0.9011 | 0.9196 | 0.9302 |
| AD2, 0–1 | 초기8 | 0.8077 | 0.8129 | 0.8200 |
| AD2, 0–1 | 회복4 | 0.7917 | 0.7859 | 0.8091 |

AD8의 같은 명령 초기 구간만 작은 개선이 있었고 회복과 다른 명령 조건으로
일관되게 이어지지 않았다. 선형 외삽에서는 일부 개선이 있지만, 예컨대 시행4 회복의
기준선6.8412→이력6.0366pA도 일정 수준 기준선2.8144pA보다 크다. 전체 결과는
[JSON](../verify/Q-NPF-04/allen_synphys/vc20hz_command_history_result.json)에 있다.

두 표적×두 기준선 모두 τ=50ms, 후보 하한을 선택했다. 하한 선택을 실제 막 시정수나
시냅스 회복 상수의 측정으로 해석하지 않는다. 여기서 격자를 다시 넓혀 성능을 찾는
단계로 넘어가지 않았다. Local baseline은 자기 자극 잔류·숨은 회로·실제 막전압을
모두 설명하는 생물학적 상태모형이 아니므로 이 실패를 가소성 부재로 일반화하지 않는다.

## 재현과 시도 보존

- [모형 소스](../verify/Q-NPF-04/allen_synphys/vc20hz_command_history.py)와
  [11개 검사](../tests/test_vc20hz_command_history.py)는 pre-only 관측, 정확한 bin 중심,
  과거 명령만 쓰는 이력, 회복 간격·진폭, 평가 자료 변형에 대한 적합 불변성과 합성 정답을 확인한다.
- [보상 설정 소스](../verify/Q-NPF-04/allen_synphys/vc20hz_compensation.py),
  [검사](../tests/test_vc20hz_compensation.py),
  [설정 결과](../verify/Q-NPF-04/allen_synphys/vc20hz_compensation_result.json)를 별도로 둔다.
- [실행 notebook](../verify/Q-NPF-04/allen_synphys/vc20hz_command_history.ipynb)은
  부모 입력과 소스 해시를 대조하고, 저장 예측으로1,176개 시행별 점수와672개 집계를
  다시 계산한다. 재적합 없이 원파형과 평가 오차 그림을 만든다.

초기 모형 결과의 `later_changed_target_command`라는 이름은 AD2도 자기 명령이
바뀐 것처럼 보일 수 있었다. 초기 소스·검사·JSON·배열을 보존하고 최종 이름을
`later_sweeps_5_6`으로 바꿨다. 최종 JSON은 표적별 실제 source/own 진폭과 학습 대비
변경 여부를 기록한다. 수정 전후286개 예측 배열은 같은 SHA이며 수치 결과는 바뀌지 않았다.
보상 설정도 comment만 읽었던 초기 소스·결과를 따로 보존했다. 이는3행 Off/18행 미상인
좁은 결과이며, 수치 노트를 결합한21행 확인과 구별한다.

실행기는 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`다.
Python3.11.9·NumPy2.4.6·h5py3.16.0과 기존 격리 notebook/plot 의존성을 재사용했다.
결과·배열·소스·검사의 최종 해시와 파일 위치는 [데이터 원장](data_registry.md)에 등록했다.

최종 등록은6개 판본·21개 파일이다. 모형11개·보상 설정3개 검사가 통과했고,
notebook code4개는1–4 순서로 실행되어 error output이 없었다. 두 내장 PNG는 외부
PNG와 byte 단위로 같고, 원파형·평가 그림의 축·범례·표시는 직접 확인했다.
저장 notebook의 markdown·출력·내장 그림을 임시 HTML로 표시해 마지막 해석까지
확인했다. 임시 미리보기는 MathJax가 없어 수식을 raw TeX로 보이며 notebook 자체는
수식 원문을 보존한다. 등록21개 파일의 크기·해시와 관련 문서5개의 링크를 확인했다.
보존 repository harness의 기존38개 문제 대비 추가 문제는0개다.

| 산출물 | 바이트 | SHA-256 |
|---|---:|---|
| 최종 예측 JSON | 725293 | `cd5db80771b16d53e042643768ff2d93876982397c606791e2a7a5f9b40d5991` |
| 최종 예측 NPZ | 1352175 | `23536eac7480b8b084e42791f74095db61156bed9068b697acf8aaee69824ac9` |
| 보상 설정 JSON | 79409 | `ea307afca9e840828bd327df558a3d4ad7791c9b36e98665aa53b9e94395dbb5` |
| 실행 notebook | 1224877 | `0aff8128bc7ccbce6f8c92032b9f67b39b15838fd2bce27c47ddb964ce6b5aab` |

선행 기술통계의 `direction` peak는 연결 표기에 따라 고른 기술적 요약일 뿐 EPSC/IPSC
극성이 아니다. 보존 JSON에는 양쪽 min/max가 있으며 최종 모형과 notebook은 전류
부호를 그대로 사용한다. 선행 입력 점검을 했다는 사실과 그 한계를 함께 보존했다.

## 다음 관측 조건과 전체 목표

다음 전기 단계는 **실제 source AP와 target current, 동시 측정 상태**를 확인한
조건에서 이력 항의 추가 예측력을 구별하는 것이다. 보유 inventory에서 experiment4863
pair121538은 VC/VC10·IC/IC66, experiment4251 pair116053은 VC/VC10·IC/IC5이며
동일 시행 mixed mode는 없었다. Experiment3337의 보유 acquisition metadata에서
시행0–6은 세 채널 모두 A,7–96은 모두 V였다. 다른 electrode 조합이나 후보 실험의
mode까지 음성으로 확정한 것은 아니다. 후보 DB의 indexed inventory와 raw 보유 여부를
확인하는 것이 다음 진행 조건이며, 대규모 다운로드나 새 적합은 이번 단계에서 하지 않았다.

확인한 pair의 근거는 [4863 recording inventory](../verify/Q-NPF-04/allen_synphys/next_donor_recording_inventory_result.json),
[4251 반복 기록](../verify/Q-NPF-04/allen_synphys/different_donor_protocol_repeats_result.json),
[3337 acquisition inventory](../verify/Q-NPF-04/allen_synphys/same_cell_intrinsic_inventory_result.json)다.

해마의 [내용 전이·사건 조건 구별](hippocampal_story_transfer_findings.md)은 별도
생물 자료의 결과로 유지한다. “복원포인트” 가설은 부분 단서에서 사건 색인을 고르고
그에 연결된 내용을 재활성화하는 과정으로 시험한다. 현재 내용 정체성의 판독 신호가
있어도 사건 주소·검색 방향성·계량 변화까지 확립한 것은 아니다. 전기 이력, 관계 변화,
리만 계량, 해마 검색을 하나의 실측 기전으로 연결하는 전체 목표는 아직 진행 중이다.

## 작업 인계

저장소는 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`이다.
HEAD와 로컬의 origin/main 참조는 `fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`다.
이번 작업에서 fetch·commit·push를 하지 않았으므로 원격의 실시간 tip은 미확인이다.
기존 `.codex` 삭제와 reality_stone 라이브러리 분리 변경은 보존했다.

이번 범위는 위 두 소스·두 검사·두 JSON, notebook 생성기·실행본·그림2개,
등록된 초기 시도·입력 점검 파일, 데이터 원장, 본 문서·측정 상태 후속·논문04/11과
관련 `.gitignore` 예외다. 검사 명령은 보존 실행기의
`pytest tests/test_vc20hz_command_history.py -q`,
`pytest tests/test_vc20hz_compensation.py -q`이며, 추가 결과는 새 파일로만 생성했다.
문서 검사는 보존 `repository_harness.py`의 `check_repository(root)` 결과를
분리 작업 전38개 문제와 비교했다. 커밋·배포는 이 연구 단계의 범위에 포함하지 않았다.

2026-09-20 [후속 mixed-mode 조사](allen_mixed_clamp_findings.md)에서는 기존 pair에
국한하지 않고 후보 실험의 전체 electrode를 조회했다. 4863의24시행에서 IC source4개와
VC target1개의 동시 기록을 확인했으며, 보고된 연결121566의 메타데이터 후보172개를
얻었다. 앞선 pair별 음성 판정은 유지한다. 다음 조건은 후보 존재 확인에서 실제
source AP·target current·공통 raw clock·측정 상태의 결합으로 이동했다.
