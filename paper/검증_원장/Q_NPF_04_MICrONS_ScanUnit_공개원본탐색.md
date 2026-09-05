# MICrONS ScanUnit 공개 원본 탐색

이번 질문은 구조상 세포를 실제 형광 반응의 열에 연결하는 `session, scan_idx, unit_id → field, mask_id` 대응표를 확보할 수 있는가이다. 뇌 구조와 기능을 같은 세포에서 비교하기 위한 선행 확인이며, 생물학적 가설 검증 결과는 아니다.

## 확인 결과

공개 digital twin v2의 `anatomy/units.csv` 첫 구간에는 `session, scan_idx, unit_id, unit_x, unit_y, unit_z, brain_area, field`가 있다. 필요한 `mask_id`는 없다. 좌표·영역 목록을 NWB 반응 열의 대응표로 대신 사용할 수 없다.

[제작자 스키마 안내](https://github.com/cajal/microns_phase3_nda)는 `ScanUnit`을 스캔 내 단위 번호, `Segmentation`을 field 내 mask 번호로 구분한다. v8 공개 SQL 원본은 116,199,864,342바이트다. 전체 대신 29개 구간, 합계 60,817,408바이트(58 MiB)를 읽고 저장했다. 각 HTTP 응답의 부분 범위·전체 크기를 확인하고 ETag 일치와 로컬 SHA-256을 검사했다.

읽은 구간에서 `activity`, `fluorescence`, `mean_intensity`, `monet2`, `unit_hash`, `#scan_include` 표 이름을 확인했다. `scan_unit` 표의 위치는 아직 찾지 못했다. SQL에 긴 바이너리 값이 들어 있어 임의의 작은 구간에서 표 이름이 보이지 않을 수 있다. **부분 조회에서 찾지 못한 것은 전체 DB에 표가 없다는 증거가 아니다.**

## 판정과 다음 행동

원래 식별자 질문에는 아직 답하지 못했다. 작은 anatomy 목록만으로 mask 대응을 해결하는 경로는 필요한 열이 없어 사용할 수 없다. 공식 SQL이나 DB의 ScanUnit 표를 통한 경로는 남아 있다. 다음에는 배포 아카이브의 표별 저장 구조 또는 제작자 코드의 직접 내보내기 경로를 조사한다. 동일한 SQL 구간은 다시 받지 않는다.

기존 53개 대상 중 13개 좌표 후보는 계속 조건부다. 실제 대응표와 일치하기 전에는 확정된 반응 열로 추출·해석하지 않는다. 이번 증거 등급은 `BIO_EVIDENCE_L0`이며, 뇌 전체 구조나 인과 기전을 확립한 결과가 아니다.

## 재현 자료

- [조회 코드](../../verify/Q-NPF-04/allen_synphys/microns_sql_probe.py): 총 64 MiB 이내의 범위 캐시, 기존 구간 해시 확인 후 재사용.
- [조회 결과와 범위별 해시](../../verify/Q-NPF-04/allen_synphys/microns_sql_probe_result.json): 원본 URL, 오프셋, ETag, SHA-256, 확인한 표 이름.
- [이전 좌표 후보 판정](Q_NPF_04_MICrONS_ROI좌표_조건부대응.md): 재검토의 출발점.

로컬 캐시는 `data/external/microns_sql_v8_ranges/`에 있다. 해시는 받은 구간의 보존을 확인하며 전체 SQL 원본의 무결성을 검증한 것은 아니다.
