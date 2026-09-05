# MICrONS ROI 식별자와 첫 스캔 시간축

## 판정

첫 대응 스캔 4/7의 8개 ROI 테이블 참조와 시각 배열을 읽었다. 시간축은 모두 유한하고 엄격하게 증가한다. 그러나 **NWB ROI ID와 기능 대응표 unit ID의 직접 연결은 부적합**하다. 두 식별자는 같은 범위를 뜻하지 않는다. 이 단계에서 53개 대상 세포의 형광 반응을 추출하거나 구조·기능 결과를 계산하지 않았다.

## 식별자 확인

각 `RoiResponseSeries.rois`의 실제 HDF5 table reference를 따라 ROI 테이블을 찾았다. ROI ID는 각 영상면에서 `1..N`으로 반복된다. 반면 [제작자 데이터 설명](https://github.com/cajal/microns_phase3_nda)은 분할 mask ID가 field별 식별자이고 `ScanUnit.unit_id`가 스캔 전체 식별자라고 명시한다. NWB ID를 mask ID로 확정하려면 변환 코드의 출처도 추가 확인해야 한다.

53개 대상 가운데 unit ID 808·829·1070이 여러 NWB 영상면의 ROI ID와 숫자로 겹쳤지만, 이 대상들은 field 2다. 숫자가 겹친 ROI는 field 3~7에 있었으며 **field까지 일치하는 직접 연결은 0개**였다. 결과 파일의 `hits`는 숫자 일치 후보일 뿐 확정 세포 대응이 아니다. [판정 영수증](../../verify/Q-NPF-04/allen_synphys/microns_roi_identity_gate.json)에 직접 연결 거부를 명시했다.

field는 단순히 series 번호에서 추정하지 않고 연결된 imaging-plane 설명의 `field` 값으로 확인했다. 기존 수동 EM–기능 대응 486개가 취소된 것은 아니다. 현재 빠진 것은 그 기능 unit에서 NWB ROI 열까지의 연결이다.

## 시간축과 단위

각 영상면의 시간축은 40,000개 float64 값이며 저장 단위는 seconds다. 모두 시작 10.14944010375001초, 끝 6360.78672672675초다. 간격 중앙값은 0.15879041100015456초이며 최솟값은 약 0.156571초, 최댓값은 약 0.161913초다. 약 6.30 Hz 간격이지만 균일 시간 간격으로 가정하지 않는다.

[DANDI 공식 예제](https://docs.dandiarchive.org/example-notebooks/000402/MICrONS/demo/000402_microns_demo/)는 NWB 변환 때 원 스캔 시간 기준을 가장 이른 행동 시각으로 이동했다고 설명한다. 예제는 다른 스캔이므로 그 오프셋을 복사하지 않았다. 이번 스캔의 실제 시각을 보존했으며 자극·행동과의 공동 시간축 검사는 남아 있다.

형광 데이터 단위 속성은 `n.a.`, conversion 1.0, offset 0.0이다. 이를 전류·막전위·발화율 또는 ΔF/F로 임의 변환하지 않는다. 반응 데이터는 여러 ROI와 시점이 묶인 chunk로 저장되므로 단일 열 추출도 주변 데이터 전송을 수반할 수 있다. 식별자 연결이 끝난 뒤 필요한 chunk 범위를 정한다.

## 검증과 다음 입력

추가 수집은 3,276,800바이트였으며 기존 부분 캐시를 재사용했다. [ROI·시간 배열](../../verify/Q-NPF-04/allen_synphys/microns_roi_identity_result.json)의 위치·해시, [계약](../../verify/Q-NPF-04/allen_synphys/microns_roi_identity_contract.json), [수집 코드](../../verify/Q-NPF-04/allen_synphys/microns_roi_identity.py)를 남겼다. [오프라인 검증 코드](../../verify/Q-NPF-04/allen_synphys/verify_microns_roi_identity.py)로 ID 순서·시간축·field 일치 후보를 재계산했다. 결과와 배열은 [데이터 원장](../../ledger/data_registry.md)에 등록했다.

다음은 `ScanUnit`의 `unit_id → field, mask_id` 실제 대응과 NWB 변환 과정의 ID 보존 규칙을 확보하는 것이다. 누적 ROI 개수로 오프셋을 추정해 연결하지 않는다. 현재는 L0 입력 검사이며 뇌 전체 구조·인과기전은 미확립이다.

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/verify_microns_roi_identity.py`.
