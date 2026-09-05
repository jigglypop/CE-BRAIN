# MICrONS ROI 좌표의 조건부 대응

## 결과

첫 스캔 4/7의 대상 53개 세포 중 **13개**가 NWB에 저장된 EM 좌표·field와 정확하게 일치하는 유일 ROI 후보를 갖는다. 40개는 일치 후보가 없으며 복수 후보는 없었다. 원 반응값은 아직 읽지 않았다. 이는 **L0 조건부 대응**이며 53개 전체의 식별 문제가 해결된 것은 아니다.

## 변환 코드에서 확인한 규칙

[공개 변환 소스](https://github.com/catalystneuro/MICrONS-to-nwb/blob/80b4275c47daaf5a88bffedcad93c68383e374f3/src/microns_to_nwb/tools/ophys/ophys.py)를 commit `80b4275c47daaf5a88bffedcad93c68383e374f3`에 고정해 보관했다. 코드의 `add_plane_segmentation`은 `mask_id` 순서로 분할을 읽어 NWB의 ROI `id`에 저장한다. `add_roi_response_series`도 같은 `mask_id` 순서로 형광을 읽는다. 따라서 지난 직접 `unit_id` 연결 거부는 타당하며 ROI ID는 이 코드 기준으로 mask ID다.

코드는 선택 영상면에 CAVE ID·EM 좌표도 저장한다. 실제 NWB에서도 field 2·4·6·8에 이 열들이 존재했다. 구조 정수 root ID는 변환 코드에서 float64로 바뀌므로 그 숫자의 동일성에 의존하지 않았다. 정수 EM 좌표 세 성분과 field가 모두 같을 때만 후보로 기록했다. 근접 좌표나 누적 ROI 개수로 보정하지 않았다.

## 중요한 행 순서 한계

좌표 열을 쓰는 `add_functional_coregistration_to_plane_segmentation`은 `ScanUnit`에서 `unit_id`를 가져오지만 명시적인 `order_by`가 없다. 이 순서와 정렬된 mask 순서가 같다는 조건은 공개 코드만으로 보증되지 않는다. 따라서 NWB 저장 좌표와 일치하는 13개를 곧바로 확정 기능 반응으로 해석하지 않는다. 실제 `ScanUnit`의 `unit_id, field, mask_id` 대응표 또는 동등한 원 입력 증거로 행 정렬을 교차검사해야 한다.

고정한 공개 코드가 실제 배포 파일을 만든 정확한 실행 판본이라는 증명도 아직 없다. 파일 내용과 일치하는 저장 규칙의 근거로만 사용했다. 나머지 40개가 일치하지 않는 이유는 과거 CAVE 대응 범위, 판본·좌표 변경 또는 다른 입력 문제일 수 있으며 이번 검사로 원인을 확정하지 않는다. 세포·연결 부재로 세지 않는다.

## 실행과 다음 조건

기존 부분 캐시에서 좌표 배열을 읽어 **새 NWB 다운로드는 0바이트**였다. 코드 소스 3개는 처음 확보했고 [수집 영수증](../../data/external/microns_nwb_conversion_source/receipt.json)에 출처와 해시를 남겼다. [계약](../../verify/Q-NPF-04/allen_synphys/microns_roi_coordinates_contract.json), [코드](../../verify/Q-NPF-04/allen_synphys/microns_roi_coordinates.py), [모든 후보와 누락](../../verify/Q-NPF-04/allen_synphys/microns_roi_coordinates_result.json)을 보존했다.

보관 배열에서 53개 좌표 비교와 ROI 참조를 다시 계산해 13/40/0 분할을 확인했다. 다음은 실제 단위–mask 대응표로 이 후보를 검증하는 것이다. 반응이 잘 보이는 후보만 골라 나머지를 버리지 않는다. 뇌 전체 구조·인과기전은 계속 미확립이다.
