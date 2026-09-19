# Norman2019 해마 ripple 시각과 관측 이력의 경계

2026-09-20. 해마의 사건 검색과 내용 재활성화를 연결하기 위해, 기존 ZIP 목록에 있으나
보유하지 않았던 회상 조건의 ripple 시각 64개 파일을 수집했다. 사건 시각과 행동 시계의
대응을 확인한 단계다. 새 이력 모형이나 복원 효과를 적합하지 않았다.

## 확보한 입력과 검증

출처는 [Norman2019 공식 자료, 판본3259369](https://zenodo.org/records/3259369)다.
16개 기록 라벨×얼굴/장소×run1/2의 원 MAT64개이며, 원 ZIP 전체를 다시 받지 않았다.
[사전 보유 조사](../data/local/hippocampal-reinstatement/norman-event-input-inventory-v1/norman_event_input_inventory.json)를
거쳐 완료된 수집의 각 항목 크기·CRC32·SHA-256을 검사했고 보존 복사 전후에도 확인했다.

- 압축 본문 11,817,051바이트, 해제 MAT 합계 17,949,900바이트.
- 로컬 헤더 포함 네트워크 본문 11,849,819바이트로 16MiB 상한 이내.
- 범위 응답128개는206이며 Content-Range/Length와 ZIP 총크기를 확인했다.
  ETag/Last-Modified는 없었고 전체 ZIP MD5를 확인했다는 주장은 하지 않는다.
- [수집 결과](../data/external/hippocampal_reinstatement/norman2019_recall_ripples_v1/acquisition_summary.json)의
  SHA는 `0e724b7de640775269f8787edc0d15c9dd8eef74a0a66bdb3bae6fb43eb8fce5`다.

일반 SciPy `whosmat`은 anonymous MCOS 처리에서64개 모두 실패했다. 실패 기록을
보존하고, 해당 파일의 `FileWrapper__` 구조에 한정한 판독으로 표의 열 이름·행 수·숫자
배열을 확인했다. 이는 일반 MATLAB table 지원을 구현했다는 뜻이 아니다.
[시계 결과](../data/local/hippocampal-reinstatement/norman-ripple-clock-v1/clock-audit-v1/ripple_clock_audit.json)와
[독립 열 의미 검토](../data/local/hippocampal-reinstatement/norman-ripple-semantic-review-v1/ripple_semantic_review.json)를
각 소스와 함께 보존했다. 이 검사 당시 미확인이던 MVPA의 opaque RTA0/1/2는
아래 후속 판독에서 확인했다.

## 실제 시각과 공통 영역

64개 표는 `str, peak, fin, amplitude` 열을 가지며 총3,577개 사건이다. 모든 값은
유한하며 `str ≤ peak ≤ fin`을 만족한다. Duration은 약20–148ms로 모두 양수다.
Amplitude는 저자 코드상 중앙값 대비 dB다. 범위는 약−1.607..13.850dB이며 음수1개를
검출 오류로 취급하지 않는다.

각 파일의 `t_faces` 또는 `t_places`는−5초에서 시작하고 끝은154.442..155.160초다.
증분은 약0.002초로500Hz에 대응한다. Peak는−4.972..155초이고 파일 내 중복·정렬 오류·
비유한값·저장 시간축 밖 peak는 모두0이다. 저자 코드의 `EEG.times/1000−5` 정의와
함께 보면 이 값들은 해당 기록·범주·run에 대한 상대 초 단위다.

[행동 공통영역 검사](../data/local/hippocampal-reinstatement/norman-ripple-clock-v1/clock-audit-supplement-v1/behavior_domain_counts.json)는
저자의 회상 조건0≤t≤150초에 다음과 같이 대응한다.

| 범위 | 사건 수 |
|---|---:|
| 얼굴 run1 | 866 |
| 얼굴 run2 | 809 |
| 장소 run1 | 821 |
| 장소 run2 | 849 |
| **0–150초 합계** | **3,345** |
| 0초 이전 | 94 |
| 150초 이후 | 138 |

범위 밖232개도 원자료에 보존한다. −5초보다 앞선 이력은 알 수 없으므로 완전한
과거를 관측했다고 가정하지 않는다. 기록 라벨·범주·run과 상대 시각을 이용한 행동
정렬은 가능하지만, 이것만으로 동시 피질 사건 표현이나 숨긴 내용의 복원이 확보되지는 않는다.

## 후향 검출과 실시간 정보의 구분

보유한 [저자 검출 코드](../data/external/hippocampal_reinstatement/norman2019_metadata_v1/selected_members/Ripple_detection/detect_SWR_events_in_hippocampus.m)와
[사건 추출 함수](../data/external/hippocampal_reinstatement/norman2019_metadata_v1/selected_members/sub_routines_and_functions/ripples_detection_excluding_IED.m)를
검토했다. 다음 절차는 미래 표본이나 전체 구간 통계를 사용한다.

1. 여러 조건을 이어 붙인 실험 신호의 Hilbert envelope·클리핑·제곱·`filtfilt` 결과로
   ripple 정규화 평균/표준편차를 정한다.
2. 각 조건에도 전체 벡터 Hilbert와 앞뒤 방향 `filtfilt`를 적용한다. 잡음/IED 채널은
   해당 조건 전체의 평균/표준편차를 사용한다.
3. 잡음/IED 사건과 양쪽50ms 이내인 후보를 배제하고 종료점을 찾으며, 가까운 뒤쪽
   사건과 병합한 뒤 duration으로 거른다.

따라서 저장 시각보다 앞선 peak만 골라도 그 검출 여부는 미래 신호의 영향을 받을 수
있다. 이 timestamp는 **후향적으로 검출한 사건 시각**이다. 고정된 짧은 시간 간격을
띄우는 것만으로 전체 구간 정규화와 Hilbert의 미래 의존성이 사라지지는 않는다.

[검색 관측식](hippocampal_retrieval_observation_findings.md)의 실시간 정보집합
F_{t-}에 이 사건 이력을 그대로 넣을 근거는 아직 없다. 후향적 연관 분석에서는
처리 과정을 명시한 입력으로 사용할 수 있다. 실제 온라인 예측을 주장하려면 이전에
확정된 보정과 과거 표본만 사용하는 검출, 그때 이용 가능한 시각과 지연의 검증이 필요하다.
인과적 검색 기전의 입증에는 별도 대조·개입도 필요하다.

추가 후보인 `hippocampal_signal_for_ripple_detection.mat`은 미수신 상태이며 코드상
이미 band-filter된 세 신호다: 해마70–180Hz, common-average70–180Hz,
해마25–60Hz IED 대조. 이를 무필터 원전압으로 부르거나 새로 받기만 하면 인과적
전처리를 재구성할 수 있다고 가정하지 않는다.

## 전체 목표와 다음 조건

[항목 표현 전이](hippocampal_norman_template_transfer_findings.md)의 음수 결과는 그대로
유지한다. 이번 결과는 그 실패를 뒤집는 복원 증거가 아니다.
[후속 MVPA RTA 표 판독](hippocampal_norman_observation_boundary_findings.md)을 완료했으나
세 표는 채널·항목 라벨이며 개별 시각·피질 수치가 없었다. RTA2의 지원은 M2의
유한 지원과 정확히 같다. 기존 opaque 표를 다시 여는 작업은 반복하지 않고,
다음 입력에서는 사건별 피질 수치와 생성 규칙·공통 시계가 있는지 확인한다.

고정 뉴런의 전기 상태·이력→관계와 리만 계량 변화→해마의 주소 지정·검색→현재 표현
선택이라는 전체 연결은 미확립이다. 시각 일치나 대칭 관측 Fisher만으로 물리 비용,
검색의 방향성, 학습된 관계 변화까지 확인했다고 해석하지 않는다.
