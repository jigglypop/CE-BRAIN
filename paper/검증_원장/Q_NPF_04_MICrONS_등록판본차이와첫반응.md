# MICrONS 등록 판본 차이와 첫 반응 구간

## 결론

기존 좌표 후보 한 건의 불일치는 공식 등록 판본 간 차이로 확인됐다. 과거 v343의 연결을 담은 NWB를 보존하고, 이번 분석에 사용할 v1412 수동 등록을 별도로 적용했다. 이 기준으로 대상 **53개 세포의 첫 1,250프레임**을 확보했다. 66,250개 값이 모두 유한하고, 53개 신호 모두 상수가 아니었다.

이는 구조와 실제 반응을 비교하기 위한 입력 확인이다. 연결 강도·인과 기전·뇌 전체 구조를 밝힌 결과는 아니다. 이번 판정은 `BIO_EVIDENCE_L0`다.

## 불일치의 출처

검사를 첫 스캔의 v1412 등록 1,322행으로 넓혔다. NWB와 같은 field·정수 EM 좌표로 유일하게 연결된 314건 중 313건의 mask가 v8 ScanUnit과 같았다. 나머지 1,008건은 좌표 후보가 없거나 유일하지 않아 이 검사로 대응을 평가하지 못했다. 차이가 난 것은 이전에 발견한 한 건뿐이었다.

| 근거 | 해당 좌표의 연결 |
|---|---|
| v343 `functional_coreg` | 등록 ID 7657, unit 3148 |
| v8 ScanUnit의 unit 3148 | field 4, mask 598 |
| 실제 NWB mask 598 | 같은 좌표와 CAVE ID 7657 저장 |
| v1412 `coregistration_manual_v4` | unit 3151 |
| v8 ScanUnit의 unit 3151 | field 4, mask 601 |

공통 좌표는 `[180160, 137664, 21669]`이며 좌표 단위는 원표의 EM voxel 좌표다. NWB mask 601의 과거 CAVE 표지는 비어 있다. 실제 NWB의 등록 ID와 공식 v343 표가 일치하므로, 전체 행 순서가 밀렸다고 해석할 근거는 없다. 두 공식 판본이 다른 ROI를 가리킨다는 것은 확인했지만 어느 ROI가 생물학적으로 더 정확한지는 원영상으로 독립 판정하지 않았다.

이번 반응 추출은 **v1412 등록 + v8 ScanUnit**을 명시적으로 사용한다. unit 3151은 mask 601로 읽고, 과거 mask 598을 최신 등록인 것처럼 바꿔 쓰지 않는다. 과거 표와 신규 결과를 모두 보존했다. [공식 판본 안내](https://tutorial.microns-explorer.org/materialization-version.html)의 정적 아카이브에서 v343 원본 285,960바이트와 헤더 161바이트를 받아 원장에 등록했다.

## 시간축의 확인 범위

[고정한 변환 코드](https://github.com/catalystneuro/MICrONS-to-nwb/blob/80b4275c47daaf5a88bffedcad93c68383e374f3/src/microns_to_nwb/convert_session.py)는 v8 `ScanTimes` 파일의 프레임 시간을 읽고, 필요한 경우 행동 기록의 가장 이른 시점에 맞춰 공통 이동을 적용한다. 그 배열을 모든 field의 형광 시계열에 넘긴다. `ophys.py`는 mask 순서로 원래 trace를 쌓으며, 이 경로에 세포별 `ms_delay`를 적용하는 연산은 없다.

이 코드 검사만으로 상류 trace 처리나 실제 과거 빌드까지 모두 재현한 것은 아니다. 따라서 이번 산출물에는 **NWB 프레임 시간과 세포별 ms_delay를 별도 배열로 보존**했다. 지연을 더하거나 보간하지 않았다. 구조–반응 분석의 시간 정렬을 정할 때 상류 보정 여부와 지연 민감도를 확인해야 한다. 공통 타임스탬프가 같다는 이유만으로 세포들이 정확히 동시에 촬영됐다고 주장하지 않는다.

## 첫 고정 구간의 품질 검사

반응값을 읽기 전에 계약에 첫 1,250프레임과 기존 53개 대상 전부를 고정했다. 반응에 따른 선택·제외는 하지 않았다.

- 배열: 1,250 × 53. 모든 값이 유한하며 상수 신호는 0개다.
- NWB 프레임 시간: 10.14944010375001–208.416064377초.
- 원본 단위: `n.a.`. 형광 값을 발화율이나 ΔF/F로 바꾸어 부르지 않는다.
- 새 NWB 범위 다운로드: 7,340,032바이트. 기존 범위 캐시를 재사용했다.
- 전체 40,000프레임 중 첫 구간만 검사했다. 전체 기록의 품질·대표성·구조 연관성을 통과시킨 검사가 아니다.

이번 원래 질문에는 등록 판본 차이라는 답을 얻었다. “전체 행 순서가 밀렸다”는 설명은 313건의 일치와 과거 등록 ID의 일치로 지지되지 않는다. 단일 ROI의 생물학적 정답과 세포별 시간 보정은 남아 있다. 다음에는 판본 차이 한 건의 포함·제외를 구분하면서 분석에 필요한 기록 범위와 시간 정렬을 고정하고 구조–반응 관계를 평가한다.

## 재현 근거

- [등록 판본 검사 코드](../../verify/Q-NPF-04/allen_synphys/microns_registration_versions.py), [검사 결과](../../verify/Q-NPF-04/allen_synphys/microns_registration_versions_result.json)
- [실제 NWB CAVE ID 확인](../../verify/Q-NPF-04/allen_synphys/microns_historical_cave_id_gate.json)
- [첫 반응 추출 코드](../../verify/Q-NPF-04/allen_synphys/microns_first_response.py), [값을 읽기 전 계약](../../verify/Q-NPF-04/allen_synphys/microns_first_response_contract.json), [품질 결과](../../verify/Q-NPF-04/allen_synphys/microns_first_response_result.json)
- [이전 ScanUnit 교차 확인](Q_NPF_04_MICrONS_ScanUnit_추출과교차확인.md)

반응 배열은 `data/external/microns_functional_nwb/scan_4_7_first1250.npz`에 보존한다. SHA-256은 품질 결과와 데이터 원장에 있다. 등록 판본 검사, 캐시 재사용 실행, 문서 하네스를 검증했다.
