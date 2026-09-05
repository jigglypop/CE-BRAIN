# kinetics 유효 범위 문제의 기존 분석 영향

## 판정

[최종 kinetics 전달 검사](Q_NPF_04_Allen_시냅스kinetics_영역전달.md) 이후 실제 사용 경로를 확인했다. **기존 상호 연결 구조 집계는 kinetics·적합 표 접근을 금지해도 동일하게 재현됐다.** 고정 개체 후보 5개와 개발 세포쌍의 IC kinetics에도 이번 영역 밖 입력 문제는 없었다. 따라서 이번 발견만으로 이 구조 집계나 해당 원파형 비교를 폐기할 근거는 없다.

이는 **L0 의존 경로 감사**이며 저장소 전체 분석의 독립성 증명은 아니다. 구조 집계가 사용하는 제작자 연결 표지 자체의 검출 편향과 독립 해부학적 정답 부족은 여전히 남는다.

## 실제 접근 제한 검사

읽기 전용 small DB에서 SQLite authorizer로 `synapse`, `poly_synapse`, `avg_response_fit`, `resting_state_fit` 읽기를 금지했다. 그 상태에서 [기존 구조 SQL과 집계 함수](../../verify/Q-NPF-04/allen_synphys/population_reciprocity.py)를 실행했고 저장된 분석 결과와 정확히 일치했다. 실행 중 읽은 표·열 목록을 영수증에 남겼다.

이 검사는 해당 집계가 최종 kinetics를 직접 소비하지 않음을 입증한다. 제작자 연결 판정이 어떤 상류 관측·수동 판단에 의존했는지까지 제거하는 개입 실험은 아니다. 따라서 구조 관측은 기존 주장 상한을 유지하며, 생물학적 인과 증거로 승격하지 않는다.

## 고정 후보와 실제 사용값

[기존 선택 SQL](../../verify/Q-NPF-04/allen_synphys/separate_experiment_selection.py)은 양성 연결 표지와 양수 IC 상승시간·감쇠시간·지연에 조건부다. 같은 SQL로 전체 후보 5개 ID가 이전 기록과 일치함을 확인했다. 후보를 교체하거나 조건을 완화하지 않았다.

| 세포쌍 | IC 최종 영역 | VC 최종 영역 | 최종 kinetics에 기여한 영역 밖 QC 통과 평균 |
|---|---|---|---|
| 104272, 개발 입력 | 안 | 안 | 없음 |
| 104345 | 안 | 안 | 없음 |
| 104436 | 안 | 안 | 없음 |
| 116053, 다른 개체 비교 | 안 | 누락 | 없음 |
| 121538, 다음 개체 비교 | 안 | 안 | 없음 |
| 121566 | 안 | 안 | 없음 |

116053의 VC kinetics는 NULL이며 영역 안으로 간주하지 않았다. 121538의 −70 mV 개별 평균 적합은 영역 밖이지만 QC 실패로 최종 가중 집계에 들어가지 않았다. 따라서 해당 개별 평균의 문제와 최종 VC kinetics의 상태가 다르다.

[개발 deconvolution 코드](../../verify/Q-NPF-04/allen_synphys/producer_deconv_comparison.py)는 pair104272의 IC 상승시간·감쇠시간을 수치 연산에 사용한다. 당시 저장 입력이 현재 DB 값과 정확히 같고 유효 범위 안임을 확인했다. 이전 비교에서 남은 수치 불일치는 이번 결과로 지우거나 통과로 바꾸지 않는다.

[고정 원전류 대비 함수](../../verify/Q-NPF-04/allen_synphys/different_donor_vc_response.py)는 원전류·발화시각·고정 시간창을 사용하며 PSP/PSC kinetics를 직접 읽지 않는다. 그러나 후보 선정은 IC kinetics 존재와 알려진 양성 표지에 조건부다. 측정 함수의 직접 의존성이 없다는 사실을 표본 선택의 독립성으로 확대하지 않는다.

## 기록과 다음 작업

[계약](../../verify/Q-NPF-04/allen_synphys/kinetics_analysis_impact_contract.json), [코드](../../verify/Q-NPF-04/allen_synphys/kinetics_analysis_impact.py), [결과](../../verify/Q-NPF-04/allen_synphys/kinetics_analysis_impact_result.json)에 접근 제한, 실제 읽은 열, 후보 ID와 매개변수 상태를 기록했다. 재실행 결과가 같았고 신규 다운로드는 없었다. 파생 결과는 [데이터 원장](../../ledger/data_registry.md)에 등록했다.

이번 유효 범위 문제에 대한 국소 영향 추적은 여기까지 확인됐다. 다음 연구에서는 기존 구조 관측과 독립 구조 자료의 검증 범위를 다시 연결하되, 같은 입력 감사만 반복하지 않는다. 추가 kinetics 분석을 시작할 때만 전수 조사에서 남긴 입력·최종 영역 구분을 적용한다. 전체 뇌 구조와 동일 단위의 통합 인과사슬은 미확립이다.

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/kinetics_analysis_impact.py --verify`.
