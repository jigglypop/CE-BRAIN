# MICrONS 첫 대응 스캔의 NWB 반응 경로

## 결과와 범위

기존 기능 대응표의 session·scan 오름차순 첫 항목 **4/7**에 해당하는 공개 NWB에서 추출 형광 반응 경로를 확인했다. `/processing/ophys/Fluorescence` 아래 `RoiResponseSeries1`부터 `8`까지 있으며 각 배열은 40,000시점이다. 8개 배열의 열 수는 각각 643, 452, 1,455, 1,389, 1,420, 1,411, 895, 730으로 총 8,395개다. 열 수를 서로 다른 생물 세포 수로 단정하지 않는다.

각 배열은 float32이며 대응 `rois`와 40,000개 float64 `timestamps`가 있다. `ImageSegmentation`에는 plane별 `id`, `mask_type`, `image_mask`가 있다. 지금 확인한 것은 경로·shape·자료형이며, **시간값의 단조성·간격·단위, 반응 품질, ROI와 기능 unit ID의 동일성은 아직 미검사**다. 구조·기능 결과가 아닌 L0 입력 확인이다.

## 자료와 수집

[공식 배포 안내](https://tutorial.microns-explorer.org/static-repositories.html)가 연결한 DANDI 000402의 고정 공개 판본 `0.230307.2132`를 사용했다. [공개 자산 목록 API](https://api.dandiarchive.org/api/dandisets/000402/versions/0.230307.2132/assets/?page_size=100)에는 19개 NWB가 있다. 선택한 파일은 `sub-17797_ses-4-scan-7_behavior+image+ophys.nwb`, 자산 ID `9f5b1624-ea1c-4eb4-9f45-e4a39398ff2b`, 크기 70,959,637,818바이트다.

전체 파일을 받지 않았다. 첫 메타데이터 전체 순회는 고정 누적 캐시 상한 32MiB에서 중단됐다. 기존 판독기의 오류 문구는 64MiB지만 실제 설정값은 32MiB였음을 [중단 기록](../../verify/Q-NPF-04/allen_synphys/microns_nwb_metadata_failure.json)에 명시했다. 이를 데이터 부재로 판정하지 않았다.

별도 계약으로 `processing` 상위 4단계만 목록화하고 추가 수집을 8MiB 이내로 제한했다. 추가 3MiB로 완료하여 총 캐시는 **35MiB**다. 부분 읽기는 원격 ETag·Content-Range와 블록 해시를 검사하며 보유 블록을 재사용한다. 전체 NWB의 다운로드 또는 전체 파일 해시 검증으로 표현하지 않는다.

공개 자산의 `variableMeasured` 요약에는 `RoiResponseSeries`가 명시되어 있지 않았지만 실제 파일 안에서는 확인됐다. 메타데이터 요약만으로 반응 부재를 결정하지 않은 이유다. 별도 공개 `functional_series/session4_scan7_field4/attributes.json`도 확인했으나 그 항목은 248×440×1×40,000 시간 영상 배열로, 세포별 추출 반응표가 아니다.

## 다음 검사

이 스캔에는 기존 구조 대상 53개 세포가 대응된다. 다음은 NWB의 ROI 테이블 참조와 id를 실제로 읽어 `session, scan_idx, unit_id, field`에 연결하고, 시간값·단위·결측과 반응 데이터의 부분 추출 비용을 확인하는 것이다. `RoiResponseSeries` 번호를 field 번호로 추정해 바로 매칭하지 않는다. 자극과 행동 시간축의 결박도 별도로 필요하다.

전체 뇌 구조와 통합 인과기전은 계속 미확립이다. 형광 반응의 동시성이나 상관을 단일 시냅스의 인과 효과로 해석하지 않는다.

## 증거

- [자산 목록](../../verify/Q-NPF-04/allen_synphys/microns_dandi_assets.json), [선택 자산 메타데이터](../../verify/Q-NPF-04/allen_synphys/microns_first_scan_asset.json)
- [첫 순회 코드](../../verify/Q-NPF-04/allen_synphys/microns_nwb_metadata.py), [계약](../../verify/Q-NPF-04/allen_synphys/microns_nwb_metadata_contract.json)
- [좁힌 조회 코드](../../verify/Q-NPF-04/allen_synphys/microns_nwb_processing.py), [계약](../../verify/Q-NPF-04/allen_synphys/microns_nwb_processing_contract.json), [결과](../../verify/Q-NPF-04/allen_synphys/microns_nwb_processing_result.json)
- [캐시 스냅샷](../../verify/Q-NPF-04/allen_synphys/microns_nwb_processing_cache_snapshot.json), [데이터 원장](../../ledger/data_registry.md)

오프라인으로 캐시 스냅샷의 모든 블록 크기·해시, 코드 계약 해시와 8개 반응 배열·시간축 shape의 대응을 확인했다. 실제 반응 수치 검증은 다음 단계다.
