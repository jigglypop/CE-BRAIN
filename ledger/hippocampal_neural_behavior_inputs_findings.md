# 해마 복원 연구: 실제 발화·위치·선택 입력

2026-09-20. [세션 연결 단계](hippocampal_odor_place_cohort_findings.md)에서 정한23세션의
실제 spike 시각·위치·속도와 DIO·nosepokeWindow를 확보했다. 선택에는 신경 효과나
예측 성능을 사용하지 않았다. 이 단계는 실제 입력의 결합이며 신경 판독·기억 복원·
방향성의 기전 검증은 이 입력 단계에서 수행하지 않았다. 후속33세션 입력과
27세션 조건부 선택 판독은 [현재 결과](hippocampal_choice_readout_findings.md)에 둔다.

첫 참조 정정으로 전체 적격 세션은 **23→32개**가 됐다. 기존 검사에서 `.name=None`을
null 참조로 오판했으나38개 모두 실제 electrode 객체를 가리킨다. 기존 시행 범위와
냄새×정오답 네 칸 조건을 유지한 [정정 결과](../verify/Q-NPF-04/hippocampal_reinstatement/odor_place_region_reference_result.json)는
32개 중 기존23개의 유효성과 추가9개의 값 미확보를 구분한다. 이 문서의 수집 수치는
기존23세션 범위다. 이어 [정수의 의미를 정정](hippocampal_tetrode_region_findings.md)해
적격33개를 확인했고 현재33개 모두 확보했다. 아래 최초 수집 수치는 전체33개의 수치가 아니다.

## 실제로 받은 범위

고정 DANDI 판본 `001539/0.250815.1203`의 `/units/spike_times`,
`/units/spike_times_index`, Position의 data·timestamps와 같은 day의 원 Figshare
DIO·nosepokeWindow만 받았다. LFP·원래 pos/linpos 파일과 전체 NWB/ZIP은 받지 않았다.
HDF 네 배열은23개 모두 contiguous·비압축이며 저장 byte offset·dtype·shape를
기존 캐시에서 확인했다. 새 schema 조사 네트워크는0바이트였다.

수집 원본은 `data/external/hippocampal_reinstatement/odor_place_neural_position_values_v1`
의238파일·125,174,266바이트다. 이 크기는 파생 기록도 포함한 로컬 보유량이다.
네트워크 본문은124,515,536바이트이며160MiB 상한 안이다. 초기53,743,816바이트와
이어받은70,771,720바이트의 합이다. 161요청은 초기24·후속137로 나뉘며 모두206·
정확한 Content-Range·ETag·요청/수신 길이를 확인했다. 이 검사는 본문을 읽기 전에
수행했고 본문 수신 뒤 길이·SHA도 확인했다.

첫 collector는8세션 HDF를 받은 뒤 축약 ZIP 목록에 `local_header_offset`이 없어
행동자료 단계에서 실패했다. 원래 전체 `zip_members.json`을 조인한 후속 collector가
유효한 HDF32파일을 재사용했다. 그중8개 index 배열은 처음부터 기존 캐시에서
재사용한3,728바이트다. 초기24개 network payload와 합쳐32개이며 이중 수신하지 않았다.
초기 helper·닫힌 partial log·원본32개에서 보존본으로의 SHA mapping은
`data/local/hippocampal-reinstatement/odor-place-value-acquisition-attempt-v1`에 있다.

23세션 모두 HDF4배열과 행동 MAT2개를 확보했다. Final manifest의230 payload는
모두 용량·SHA가 일치하고, 행동 MAT46개는 원 ZIP의 크기·CRC32와도 일치했다.
전체 원격 파일 해시는 검증하지 않았으며 multipart ETag를 전체 SHA로 대신하지 않는다.

## 신경·시간축·위치 검사

총967유닛(CA1 677·PFC 290·OB 0), spike9,748,754개와 위치 표본1,437,649개다.
지역 수치는 원 tetrode 대응으로 정정했다. 초기398/494/75 집계는 표 행 해석 오류였다.
유닛·spike·시행 수를 독립 동물 수로 해석하지 않는다.

모든23세션에서 spike 값이 유한하고 unit별 시각이 감소하지 않으며, index는 단조이고
마지막 값이 전체 spike 수에 일치한다. Unit ID 수와 index 수도 같다. Spike extrema만으로
연속 기록이나 unit별 침묵 구간의 관측지원을 보증하지 않는다.

Spike index의 HDF `target`은 실제로 dereference하고 `/units/spike_times`의 object ID와
비교해23/23 확인했다. 참조된 객체의 `.name`이 None이어도 실제 객체가 같을 수 있다.
초기 보충의 이름 비교0건과 최종 객체 동일성23건은 별도 결과로 보존했다. 이름이
없다는 이유만으로 실제 null reference라고 단정하지 않는다.

Position은 각 표본의 `x(cm), y(cm), velocity(cm/s)` 세 열이다. 혼합 단위 문자열을
세 열에 같은 단위로 적용하지 않는다. Conversion1·offset0을 확인했고23세션 모두
유한값과 엄격히 증가하는 explicit timestamps가 있다. Reference frame은 center well이다.
명목30fps를 고정 간격으로 대체하거나 결측 시각을 보간하지 않았다.

NWB trial은 nosepoke의 시작–종료 구간이다. **2,454개 전부**에 직접 위치 표본이 있고
해당 구간 내부의 timestamp gap은100ms 이하라는 관측지원 검사를 통과했다.
그러나 전체 Position 시계열에는100ms 초과 gap12개와 최대2,607.607s의 gap이 있다.
구간 사이의 큰 간격을 연속 획득이나 정지 행동으로 처리하지 않는다. 이 검사는
단서 종료 이후 선택까지의 모든 분석창을 이미 검증한 것은 아니다.

## 실제 단서 종료와 선택

23세션에 해당하는 원래 MATLAB source epoch35개의 순서를 유지했다. NPwindow 첫열은
원래 odorTriggers 및 NWB start에 정확히 일치하고, 둘째열은2,454개 모두 NWB stop에
정확히 일치한다. 냄새 방향 라벨과 선택 방향은 별도 변수로 유지한다.

실제 선택은 NP 종료 뒤이면서 다음 NP 시작 전인 좌/우 reward-well DIO state1의
첫 진입으로 정의했다. **2,353개 시행을 연결했고**, 선택 방향과 단서 방향의 일치 여부는
저자의 정오답 라벨과 모두 맞았다. 보상 유무로 실제 선택을 역추정하지 않았다.

CS41_01의101시행은 미해결로 남겼다. 보유 DIO의 유일한 slot은121.994–1284.638s를
담지만 해당 NP는1530.385–3001.009s다. 저자 코드에 단일 slot을 실제 epoch로 옮기는
예외가 있으나 이 자료에서는 시간 일치가 성립하지 않는다. Slot을 자동 복제하거나
다른 시간의 선택을 대입하지 않았다. 따라서 행동 source는34/35 적격,1개 미해결이다.
다음 NP의 선택을 이전 시행에 배정하지 않도록 시간 제한을 유지한다.

초기 collector의 offline 행동 진단은 이 cell 구조에서 IndexError로 중단됐고 실패
원문을 수집 receipt에 남겼다. 수집 성공과 진단 성공을 구별한다. 초기 이름 기반
참조 진단3파일은 별도 attempt 폴더에, 최종 offline 진단은
`data/local/hippocampal-reinstatement/odor-place-neural-position-postcheck-v1`에 보존했다.
최종 JSON SHA는 `e32682238b2c3a32674bd99b4eecc053e3edfa530288875f949be88f10eb3919`다.

## 복원 가설에 적용할 다음 비교

이 자료에서는 냄새 방향과 학습한 목표가 결합돼 있다. 같은 냄새 안에서 실제 선택을
구별하고 위치·속도·시간 정보를 조건으로 준 뒤 CA1·PFC 활동의 추가 예측량을
평가해야 한다. 단서 이전·표본화 중·단서 종료 이후의 창은 각각 관측지원과 움직임을
확인한 뒤 정한다. 날짜가 다른 unit ID를 같은 뉴런으로 간주하지 않으며 session·rat
단위의 의존성을 보존한다.

이 입력으로 사건 색인과 내용 재활성화를 곧바로 동일시하지 않는다. 실제 신경·행동
자료의 결합은 준비됐고, 내용 복원·검색 방향성·현재 표현 선택의 검증은 남아 있다.
전기 이력의 conditional current 후보와 해마의 검색을 하나의 생물학적 리만 구조로
연결하는 전체 목표는 계속 미완성이다.

사용자가 말한 ‘복원 포인트’는 여기서 **부분 단서 → 사건을 가리키는 해마 활동 →
연결된 내용의 재활성화**라는 가설로 다룬다. 사람 연구에서 단서·목표에 없던 사건 요소의
피질 재활성화가 해마 활동과 관련됐다는 결과가 이 비교를 뒷받침한다
([Horner 등, 2015](https://www.nature.com/articles/ncomms8462)).
이 근거를 현재 냄새–목표 자료의 복원 성공으로 옮기지는 않는다. 현재 자료에는 CA1과 PFC가
있고, CA3 내부의 패턴 완성이나 과거 뇌 상태 전체의 복구를 직접 관측한 것은 아니다.

## 검증과 작업 인계

참조 정정은 보존 실행기 `C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd`로
`pytest tests/test_odor_place_region_reference.py`7개 통과 후
`python verify/Q-NPF-04/hippocampal_reinstatement/odor_place_region_reference.py`를 한 번 실행했다.
결과 SHA는 `784bbd1190639255c6a403d6b8b17f941076440a86494d9913bc854e9c020cc1`다.
독립 검토가 확보23개와 정정된 적격32개의 분모·수치 및 미해결 경계를 대조했다.
전기 예측의8개 검사와 이번7개 검사는 코드 조건의 확인이며 신경 복원 성공의 증거는 아니다.
이번10판본273파일의 용량·SHA도 [데이터 원장](data_registry.md)과 실제 파일에서 일치했다.

저장소는 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`이다.
HEAD와 로컬 origin/main 참조는 `fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`이며
이번 단계에서 fetch·commit·push는 하지 않았다. 원격 실시간 tip은 확인하지 않았다.
변경 범위는 AP 예측 소스·검사·결과·그림, 해마 값과 진단 보존본, 참조 정정 소스·검사·결과,
관련 원장·논문04/11과 gitignore다. 기존 `.codex` 삭제와 reality_stone 분리 변경은 유지했다.
당시 다음 단계였던 추가9세션과 새로 적격인 CS39_05 확보, 분석창 검사와 첫 신경 판독은
[후속 원장](hippocampal_choice_readout_findings.md)에서 완료했다. 내용 복원과 전체 연구 목표는 미완성이다.
