# MaleCNS 원시 ID 쌍과 두 단계 경로

문서 유형: 개발 분석 원장. 시작일: 2026-09-14.
사용자 목표는 추론한 연구 패턴을 실제 MaleCNS 전체 자료에서 찾는 것이다.
이 원장은 [범주 분포와 폐쇄 검사](malecns_structure_findings.md)의 다음 질문을 다룬다.
새 자료를 받지 않고 [데이터 재고](malecns_inventory.md)의 동일한 원자료를 재사용한다.

## 질문과 분석 단위

이전 범주 행렬은 서로 다른 중간 분절을 하나로 합칠 수 있다. 이번 질문은 실제 ID를
맞췄을 때 역방향 연결과 `assigned neuron -> middle segment -> assigned neuron` 경로가
얼마나 남는가이다. 모든 raw 행을 사용하며 낮은 weight, 교세포, 미분류, 미주석, self-loop를
캐시에서 제거하지 않는다. 분석 단위는 원시 분절의 **고유한 방향성 ID 쌍**이다.
공식 [full connection graph](https://male-cns.janelia.org/download/)의 배포명은
`connectome-weights-male-cns-v1.0-minconf-0.5.feather`다. 생산자가 이미 적용한 판본·confidence
범위 안의 전량이며, 이번 분석에서 추가 confidence·weight 문턱이나 top-K를 적용하지 않았다.

`(body_pre, body_post)`가 정렬되어 있지 않으므로 전체 행을 uint64 packed key로 정렬한다.
두 ID가 uint32 범위인 것을 확인한 뒤 `pre << 32 | post`로 부호화한다. 같은 key가 여러 번
나오면 weight만 합치고 연결 개수는 하나로 센다. 원자료 행 수와 weight 합은 이전 전량
결과와 대조한다. NT annotation이 아닌 raw source ID 자체로 인덱스를 만든다.

## 지표와 반례

자기 연결을 제외한 고유 방향성 연결 집합을 $E$, 연결 weight를 $w_{uv}$라 하자.
역방향도 존재하는 연결 집합은 $R=\{(u,v)\in E:(v,u)\in E\}$이다.
연결 기준 reciprocity는 $|R|/|E|$, weight 기준 두 지표는 각각
$\sum_Rw_{uv}/\sum_Ew_{uv}$와 $\sum_R\min(w_{uv},w_{vu})/\sum_Ew_{uv}$이다.
이 분모에는 미주석·미분류·교세포 연결도 들어간다. assigned-neuron끼리의 조건부 수치는
별도로 표시한다. 이전 범주 수준의 균형 weight 12.28%와는 단위·분모가 다르다.

주석 superclass가 지정된 27범주의 뉴런 집합을 $K$라 하자. 실제 중간 ID $v$에 들어오는
$K$의 고유 source 수를 $l_v$, $K$로 나가는 고유 target 수를 $r_v$라 하면, 두 연결 walk는
$l_vr_v$개다. 두 연결 각각의 self-loop는 제외한다. 이 중 $u=v$ 또는 $v=z$인 것은 없고,
$u=z$인 되짚기만 별도로 세어 빼면 서로 다른 세 ID의 경로가 된다. 중간 분절이 같은
범주이지만 ID가 다른 `u -> v`와 `v' -> z`를 곱하지 않는다. 경로 수는 고유 endpoint 쌍의
개수도, weight 곱도, 개별 synapse 연쇄의 개수도 아니다.

중간 ID는 assigned neuron, annotated glia, annotated unclassified, unannotated segment로
나눠 모두 보고한다. post-only ID는 전체 캐시에 남지만 원자료에 outgoing 연결이 없으므로
두 연결 walk를 매개하지 못한다. 이는 **이 판본에서 관측된 out-degree 0**이지 생물학적
종단 상태라는 판정이 아니다. 실제 경로 예시는 각 중간 집단의 큰 매개 count에서 뽑는
결정적 witness로, 대표 표본이나 확인 집합이 아니다.

## 구현과 진행 상태

[분석 소스](../verify/MaleCNS/dyad_return_paths.py)와
[작은 그래프 검사](../tests/test_malecns_dyad_return.py)의 독립 리뷰와 전량 실행을 완료했다.
리뷰에서 uint64 합계 overflow 반례를 발견해 개별 weight와 행 수의 선행 상한을 넣은 뒤
실행했다. 이는 현재 입력에서는 발생하지 않는 경계 결함이지만 일반 입력 방어를 수정한 것이다.
검사는 ID 부호화, 중복 weight 합산, 실제 중간 ID equijoin, self-loop, overflow·메모리
상한과 reciprocity의 weight 분모를 다룬다. 관련 검사 6개가 통과했다. 전량 실행은 입력 해시,
수지, 역방향 행렬 대칭과 witness의 실제 두 edge를 검사한 뒤 새 경로에만 산출물을 썼다.
이후 별도 검산에서도 정렬·양의 weight·총합·행렬 대칭·실제 경로 예시가 일치했다.
기존 봉인 소스와 산출물은 변경하지 않았다.

## 전량 결과

[기계 판독 결과](../verify/MaleCNS/dyad_return_result.json)는 151,856,684개 raw 행을 모두
보존했고 고유 dyad도 151,856,684개였다. 중복 key와 추가 중복 행은 모두 0이다.
정렬 전 입력이 비정렬인 사실과 정렬 뒤 key가 엄격히 증가하는 사실을 구분해 확인했다.
총 weight 311,833,243, 자기 연결 123쌍·weight 542다. 따라서 아래 전량 reciprocity의
분모는 nonself dyad 151,856,561개, nonself weight 311,832,701이다.

| 범위·지표 | 분자 | 분모 | 비율 |
|---|---:|---:|---:|
| 전체 raw, 역방향 있는 방향성 dyad | 8,871,458 | 151,856,561 | 5.841998% |
| 전체 raw, 역방향 있는 edge의 weight | 52,619,911 | 311,832,701 | 16.874404% |
| 전체 raw, 양방향 최소 weight의 방향별 합 | 23,044,118 | 311,832,701 | 7.389898% |
| Assigned neuron 양 끝점, 역방향 있는 dyad | 7,647,520 | 25,582,837 | 29.893166% |

양방향 unordered pair는 4,435,729개다. reverse edge가 존재해도 양 방향 weight가 같다는
뜻은 아니다. 위 수치는 한 graph의 전수 통계이며 독립 표본 효과크기·p값·신뢰구간이 아니다.

post-only target으로 가는 nonself dyad는 119,105,009개(78.432574%), weight는
177,619,313(56.959810%)다. 이 target들은 raw source 인덱스에 없으므로 관측된 역방향
연결이 있을 수 없다. target도 outgoing을 가진 ID인 경우로 조건화하면 reciprocity는
dyad 기준 27.087138%, weight 기준 39.206157%, balanced weight 기준 17.169761%다.
이는 전체망의 대체값이 아니라 분모 민감도다. post-only 상태와 annotation 유무는 서로
다른 축이며, 이 비율을 미주석 비율이나 물리적 신호 소실률로 바꾸지 않는다.

## 실제 ID를 맞춘 두 단계 경로

raw source ID 1,834,661개를 모두 인덱싱했다. 다음 표에서 양 끝점은 27개 superclass로
지정된 뉴런이며 중간 ID만 네 집단으로 나눈다. 자기 연결을 제외한 실제 두 edge가 모두
있을 때만 센다. assigned source가 165,665개인 것은 전체 assigned annotation 166,700개
중 outgoing이 없는 1,035개가 매개할 수 없기 때문이다.

| 중간 ID 집단 | Outgoing ID 수 | 양방향 구간 매개 ID 수 | 두-edge walk | 같은 시작 ID로 되짚기 | 서로 다른 세 ID 경로 |
|---|---:|---:|---:|---:|---:|
| Assigned neuron | 165,665 | 165,327 | 9,579,474,710 | 7,647,520 | 9,571,827,190 |
| Annotated glia | 2,021 | 741 | 64,621 | 1,053 | 63,568 |
| Annotated unclassified | 18,473 | 14,254 | 5,088,879 | 48,992 | 5,039,887 |
| Unannotated segment | 1,648,502 | 652,640 | 7,283,276 | 480,286 | 6,802,990 |

여기서 "양방향 구간 매개"는 assigned source에서 들어오는 edge와 assigned target으로
나가는 edge를 모두 가진다는 뜻이며 모든 edge가 reciprocal이라는 뜻은 아니다.
미주석 분절 경유 7,283,276개는 범주 행렬의 곱으로 만든 가짜 경로가 아니다. 다만 분절의
정체·주석 오류·synapse 판독과 생물학적 전달은 별도 문제다. 특히 Glia 주석을 경유하는
64,621개를 교세포의 신경 전달 또는 생리적 두 synapse 사슬로 해석하지 않는다.

예를 들어 `10231 -> 957741 -> 10029`는 미주석 중간 ID `957741`을 실제로 공유하며
두 edge weight는 각각 1이다. 미분류 중간 `519161`의 예시는
`10187 -> 519161 -> 10495`, weight 2와 51이다. 전체 JSON의 20개 witness는 각각
두 packed key·weight·집단·nonself 조건을 별도 검산했다. 높은 경로 수의 매개 ID를
고른 예시이므로 이들만으로 전체 자료의 품질이나 대표성을 판정하지 않는다.

## 산출물과 재현

원자료와 기존 whole-structure 결과의 해시는 새 JSON에 그대로 연결했다. 새 캐시 폴더는
`data/local/malecns-analysis/raw-dyad-return-v1/`이며 원본 dyad를 삭제하지 않은 정렬 파생물이다.

| 산출물 | Bytes | SHA-256 |
|---|---:|---|
| `dyad_keys.npy` | 1,214,853,600 | `b47963a29cd29d66628c45a38bf7e66d7355dc4b3f9b36bb4b13a3844124b1b3` |
| `dyad_weights.npy` | 607,426,864 | `fd9f6771a0b472ac787c479da6d01ff5850dae5e9efe16c36f45790924b7a65a` |
| `source_categories.npz` | 29,722,611 | `790d06402a4feb54b98699a3e13e744d91eee7a5db6c0effc4191d52ab19c909` |
| `dyad_return_result.json` | 64,566 | `42b0414279cd6e12ae0fd541ac8ced607fff47cde3b3cdd81b057b80e35b9239` |

분석 소스 SHA-256은 `329ac1529734752cde0255341597f611237b31337ab5aa880f11a59a1a6e5c05`다.
Python 3.14.4, NumPy 2.5.3, PyArrow 25.0.1의 승인 실행기를 사용했고 경과 시간은
111.774초다. 메모리 8 GiB는 보수적 배열 크기 검사 상한이며 측정된 peak RSS라는 뜻은 아니다.

```powershell
$env:CE_PYTHON='C:\Users\dongh\AppData\Local\uv\cache\archive-v0\-7582xpefQo_Gdq3\Scripts\python.exe'
.codex/hooks/python.cmd python verify/MaleCNS/dyad_return_paths.py `
  --whole-result verify/MaleCNS/whole_structure_result.json `
  --cache-dir data/local/malecns-analysis/raw-dyad-return-v1 `
  --result verify/MaleCNS/dyad_return_result.json --max-working-gib 8
```

기존 출력이 있으면 이 명령은 보존을 위해 멈춘다. 재분석은 질문·이유와 새 출력 경로를
지정한다. 원자료를 새로 다운로드하거나 기존 파일을 덮어쓰지 않는다.

## 읽기용 산출물과 검사

[실행 notebook](../verify/MaleCNS/dyad_return_companion.ipynb),
[HTML 읽기본](../verify/MaleCNS/dyad_return_companion.html),
[생성 소스](../verify/MaleCNS/build_dyad_notebook.py)를 함께 남겼다.
nbformat 4.5의 셀 9개 중 코드 셀 4개가 순서대로 실행됐고 오류는 0개다. 원형·캐시의
SHA-256을 대조하고 20개 witness를 다시 검사했다. 내장 그림 2개는 외부 PNG와 해시가
같으며, 외부 PNG를 직접 열어 분모·로그축·범례·수치의 가독성과 잘림 여부를 확인했다.

| 읽기용 산출물 | SHA-256 |
|---|---|
| `dyad_return_companion.ipynb` | `ccd728a387fa37d312f9210d36eb2c716e2659f654e5c4c61ff512d2d890f328` |
| `dyad_return_companion.html` | `966273ad7c39947d8b512ea1d4b88e830c63f5cce807cb70d95bbe79c81cedcb` |
| `figures/dyad-return/exact_reciprocity.png` | `4c08f0019fdce398031a3bfe458bc71f6544f0e7e923822263e6f43bcce20dab` |
| `figures/dyad-return/actual_id_two_edge_paths.png` | `4a11630a383f315c216d97e62b128404e68f7a05536b060f9ec4e1b7e0cbf535` |

그림은 기존 승인 Python 3.11.15·Matplotlib 3.10.8·NumPy 2.4.6 환경에서 계산했다.
nbformat 5.11.1·nbclient 0.11.0·ipykernel 7.3.0 의존성은 이전 companion과 같은
`C:/Users/dongh/AppData/Local/Temp/ce-malecns-notebook-deps-20260914`를 재사용했다.
커널은 `.codex/hooks/python.cmd`를 거친다. Windows ZMQ selector 경고는 있었지만 실행 오류는
없었다. 분석 환경과 그림 환경의 Python·NumPy 판본은 같다고 기록하지 않는다.
HTML 읽기본은 생성·내장 이미지 일치까지 검사했다. 브라우저 도구가 `No browser is available`을
반환해 브라우저 전체 페이지 배치는 확인하지 못했다. PNG 직접 시각 검사를 이 검사와 혼동하지 않는다.

## 주장 상한과 다음 조건

원시 EM 분절의 방향성 연결과 경로 존재는 범위가 명시된 구조 관측이다. 미주석 segment를
곧바로 독립 뉴런으로 부르거나 교세포 주석의 접촉을 신경 신호 전달로 해석하지 않는다.
구조 관측은 `BIO_EVIDENCE_L1` 구성요소, 여기서 정의한 walk의 신경 동역학·기억 해석은
`BIO_EVIDENCE_L0`이다. 양의 두 단계 경로만으로 비마르코프 기억·학습·가소성을 증명하지 않는다.

조건부로 더 좁은 결론은 가능하다. 원시 분절 전체에 접촉 정규화 전이
$P_{ji}=w_{ij}/s_i$, $s_i=\sum_jw_{ij}>0$를 공급하고, $s_i=0$인 분절에는 모형 가정으로
흡수 self-transition을 둔다. 이 보완은 원시 dyad의 추가 관측이 아니다. $K$를 raw에 등장한
assigned annotation ID, $H$를 나머지 raw ID로 나누면, 첫 숨은 경유 연산자 $P_{KH}P_{HK}$의
$(10029,10231)$ 성분은 실제 witness `10231 -> 957741 -> 10029` 때문에 적어도
$1/(s_{10231}s_{957741})>0$다. 여기서 행은 도착, 열은 출발이고 정규화 분모에는 모든
raw outgoing weight가 들어간다. 다른 양의 경로가 상쇄하지 못하므로 비영이라는 결론은
정확하지만, 현재 실행은 이 성분의 크기나 전체 기억커널·시간응답을 계산한 것이 아니다.
이 추론은 공급한 비음수 walk 안의 `BIO_EVIDENCE_L0` 산출이며, signed 전달·뉴런 통합·
상이한 관측에 그대로 옮길 수 없다. 구조적인 숨은 경유 항과 학습으로 생긴 생물학적 기억을
동일시하지 않는다.

다음 단계는 실제 ID 경계를 보존한 구조 연산자에서 숨은 상태의 경유와 관측 폐쇄를 비교하는
것이다. 분류체계와 해부학적 ROI를 동일시하지 않으며, ROI 조건화에는 별도 좌표·영역 join이
필요하다. 이번 경로 검사가 끝나도 전체 연구 목표가 완료된 것으로 판정하지 않는다.

## 작업 인계

저장소 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`.
HEAD와 이번 조회의 remote main tip은 `27c2c02e5e168732b7d24356c5b39925716cd415`다.
이번 단계는 dyad 분석·검사·companion·그림, 별도 원장, 논문 6장·목차·연구계획·PRD를
추가·갱신한다. 이전 MaleCNS 작업과 사용자 `AGENTS.md`, `.claude/` 삭제, MICrONS radial
미완료 파일을 보존한다. runtime 결함 수정과 MICrONS 재분석은 별도 미실행 작업이다.
커밋·push는 하지 않았다. 관련 검사 명령은
`.codex/hooks/python.cmd pytest tests/test_malecns_dyad_return.py`다.
