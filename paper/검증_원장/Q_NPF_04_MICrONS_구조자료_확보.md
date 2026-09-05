# Q-NPF-04 — MICrONS 구조 자료 확보와 연결 재고

작성일: 2026-09-05. 지위: **다른 측정 방식의 공개 구조 자료 확보·관측 집계**. 전기생리 결과의 독립 재현 완료나 전체 뇌 구조 완성이 아니다.

## 자료 선택과 차이

[Allen 연결 조건 동시 보존](Q_NPF_04_Allen_연결조건_동시보존.md) 뒤, 같은 자료의 조건만 반복 조정하지 않기 위해 다른 측정 자료를 조사했다. MICrONS는 전자현미경 기반 구조 자료를 제공한다. 공식 교육 자료에서 V1 column의 교정된 세포 사이 시냅스 추출 파일을 찾았다. [공식 접근 안내](https://alleninstitute.github.io/Teaching_Connectomics/notebooks/microns_data_access_education.html)

공개 저장소 `AllenInstitute/connectomics_at_cosyne`의 commit `513a6fe738f91ce179650f1cadf26d4a4728b21a`에 고정된 materialization v1718 파일을 확보했다. 세포 정보 CSV와 V1 column 시냅스 Feather, 세포 정보 전처리 notebook, 라이선스 원문을 함께 보존했다. 별도 계정 생성이나 CAVE 접근은 하지 않았다.

이 자료의 구조적 시냅스 표지는 앞선 전기생리 `has_synapse`와 측정량이 다르다. 수집·재구성 경로가 다른 데이터 후보를 확보했지만, synphys와 표본이 겹치지 않는다는 사실을 개체 ID 수준에서 아직 대조하지 못했다. 따라서 독립 표본 검증을 완료했다고 부르지 않는다. 한 EM 부피 안의 많은 세포는 독립 동물 표본이 아니다.

## 고정한 선택과 무결성

연결 수를 집계하기 전에 `is_column`, `status_axon`, `status_dendrite`가 모두 참인 세포를 선택하도록 고정했다. root ID는 큰 정수로 유지했다. 교정 여부가 없는 세포를 자동으로 포함하거나 행이 없는 연결을 생물학적 음성으로 바꾸지 않았다.

세포 표는 122,040행이고 중복·0 root ID가 없었다. column 표지 세포 1,357개 중 양쪽 구조 교정 조건을 만족한 세포는 1,348개였다. broad type 표지는 흥분성 1,184개·억제성 164개다.

시냅스 표는 146,711행이고 시냅스 ID 중복과 세포 표에 없는 partner root ID가 없었다. 선택된 서로 다른 두 세포 사이 표지는 145,598개이며, 선택 조건 밖 partner를 포함한 1,113개는 별도로 셌다. 크기 0 이하·결측 표지와 선택 부분의 자기 연결 행은 없었다.

## 구조적 연결 집계

| 연결에 필요한 시냅스 표지 수 | 유향 연결 | 상호 연결 쌍 | 한쪽 방향만 표지된 쌍 | 유지된 연결이 없는 선택 세포 |
|---|---:|---:|---:|---:|
| 1개 이상 | 78,301 | 9,869 | 58,563 | 0 |
| 3개 이상 | 13,528 | 1,491 | 10,546 | 29 |

두 문턱은 계산 전에 고정했다. 여러 시냅스 표지가 같은 방향 세포쌍에 있으면 하나의 유향 연결로 묶었고, 상호 연결은 양쪽 방향이 해당 문턱을 만족할 때 한 쌍으로 셌다.

문턱을 바꾸면 관측된 연결 수도 크게 바뀐다. 이것은 이 추출물의 구조 표지 집계이며, 전기생리의 연결 확률이나 시냅스 강도와 같지 않다. 낮은 표지 수의 연결을 모두 오류로 판단하거나 높은 문턱을 생물학적 진실로 채택하지 않았다. 한쪽 방향만 표지됐다는 말도 반대 방향의 실제 부재를 보장하지 않는다.

## 남은 판별 조건

이번에는 다른 측정 방식의 세포·구조 연결 표를 실제로 확보하고 추적 가능한 집계를 만들었다. 이전 전기생리의 조건부 상호 연결 결과가 재현됐는지는 아직 판정하지 않았다. 원 시냅스 export 쿼리의 완전성, 관측 부피 경계·절단·교정 선택과 개체 출처를 먼저 확인해야 한다.

전처리 notebook에는 세포 정보·교정 상태를 합치는 과정이 있지만 시냅스 export 전체 생성 과정이 재현된 것은 아니다. 판본에 고정된 파일의 무결성과 원 데이터 조회의 완전성은 구분한다. 추가 조건 확인 뒤에만 미표지 쌍의 비교 분모와 연결 재배치 모형을 정한다. 앞선 8세포 이하 실험의 정확 열거 방식을 1,348개 세포에 그대로 적용하거나 임의의 작은 묶음을 독립 실험으로 세지 않는다.

전체 뇌 구조, 동적 기능, 인과적 기전과 CE 고유성은 여전히 미확립이다.

## 자료와 검증

주요 두 파일은 각각 19,202,665바이트와 5,336,978바이트다. 원장 검색에서 기존 보유를 찾지 못해 새로 받았고, 네 파일의 출처·판본·위치·용량·SHA-256을 등록했다. Feather 해독용 pyarrow 25.0.1은 별도 로컬 폴더에 설치했으며 설치 영수증을 남겼다. 기존 전역 환경의 패키지는 변경하지 않았다.

- [수집 코드](../../verify/Q-NPF-04/allen_synphys/acquire_microns_reference.py), [수집 영수증](../../verify/Q-NPF-04/allen_synphys/microns_acquisition_receipt.json)
- [집계 계약](../../verify/Q-NPF-04/allen_synphys/microns_structural_inventory_contract.json), [집계 결과와 선택 root ID](../../verify/Q-NPF-04/allen_synphys/microns_structural_inventory_result.json), [집계 코드](../../verify/Q-NPF-04/allen_synphys/microns_structural_inventory.py)
- [Feather 해독기 설치 영수증](../../verify/Q-NPF-04/allen_synphys/arrow_reader_install.json), [데이터 원장](../../ledger/data_registry.md)

검증 `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_structural_inventory.py --verify`에서 파일 해시와 결과의 정확한 재현을 확인했다.
