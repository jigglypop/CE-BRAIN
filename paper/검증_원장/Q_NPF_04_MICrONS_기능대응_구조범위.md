# MICrONS 기능 대응 표시와 구조 분석 범위

## 확인한 범위

기존 V1 column 구조 분석의 양쪽 교정 세포 1,348개 중 **486개**에 수동 기능 대응 표시가 있다. 모두 흥분성 표지이며 억제성 세포에는 이 표시가 없다. 이들 양 끝 사이의 구조적 방향 연결은 시냅스 표지 1개 이상 기준 **7,976개**, 상호 연결쌍은 **188개**다.

이는 기능 자료와 연결할 수 있는 구조 표본의 위치를 확인한 **L0 입력 범위 점검**이다. 기능 반응·동시 관측·인과적 연결을 측정한 결과는 아니다. 기존 표본을 기능 대응 유무에 따라 교체하지 않았다.

## 대응 표시의 출처

보유한 [전처리 notebook](../../data/external/microns_v1718_cosyne/preprocessing_celltypes_v1718.ipynb)은 materialization v1718의 `coregistration_manual_v4`에서 nucleus ID를 가져와 세포 표의 `id` 포함 여부로 `coreg`를 만든다. 따라서 boolean 하나만으로 기능 영상의 session·scan·unit 식별자를 복원할 수는 없다.

[공식 수동 대응 설명](https://tutorial.microns-explorer.org/release_manifests/version-943.html)에 따르면 기능 단위의 키는 `session, scan_idx, unit_id`이며, 한 EM 세포에 여러 기능 단위가 대응할 수 있다. 이를 중복 세포나 독립 복제로 세면 안 된다. 또한 기능 특성 표의 선호 방향 등은 모델 응답에서 얻은 값이 포함되므로 원 관측 반응과 구분해야 한다.

이 대응은 MICrONS 내부의 기능 영상과 EM 사이의 대응이다. Allen SynPhys와 같은 세포쌍이라는 근거는 아니다. 두 자료를 직접 정답·예측으로 묶지 않는다.

## 고정 집계

기존 세포 선택 `is_column AND status_axon AND status_dendrite`와 기존 시냅스 표지 수 문턱 1·3을 유지했다. root ID를 정수로 보존했으며 이전 구조 집계의 전체 방향 연결 수를 재현했다. 전체 세포 표 122,040행 중 기능 대응 표시는 15,402행이다.

| 시냅스 표지 최소 수 | 전체 방향 연결 | 양 끝 대응 표시 | 한 끝만 표시 | 양 끝 표시 없음 | 양 끝 표시 부분의 상호 연결쌍 |
|---|---:|---:|---:|---:|---:|
| 1 | 78,301 | 7,976 | 36,378 | 33,947 | 188 |
| 3 | 13,528 | 205 | 6,545 | 6,778 | 0 |

문턱 1에서는 486개 모두 양 끝 표시 부분의 연결에 참여하고, 문턱 3에서는 220개가 참여한다. 문턱별 차이는 같은 자료의 민감도이며 독립 복제가 아니다. 시냅스 수가 적은 연결을 약한 기능 연결로 단정하거나, export 미표지를 생물학적 연결 부재로 바꾸지 않는다.

## 다음 입력과 한계

실제 구조·기능 비교에는 486개 nucleus ID에 대응하는 기능 단위 키, 반응 또는 출처가 명확한 모델 특성, 같은 스캔에서 관측된 세포쌍 범위가 필요하다. [공식 정적 저장소 안내](https://tutorial.microns-explorer.org/static-repositories.html)에 과거 판본 대응표의 공개 정적 다운로드가 안내되어 있다. 다른 판본을 사용할 경우 [공식 판본 규칙](https://tutorial.microns-explorer.org/materialization-version.html)에 따라 식별자를 연결해야 한다. root ID 이름 일치만으로 판본 간 동일성을 보장하지 않는다.

이번에는 기존 파일을 재사용해 대상 nucleus/root 목록을 만들었으며 새 다운로드는 없다. 다음은 이 목록에 맞는 대응표를 확보해 중복·판본·스캔 범위를 확인하는 것이다. 준비 단계이며 전체 뇌 구조나 통합 인과사슬은 미확립이다.

## 검증

[계약](../../verify/Q-NPF-04/allen_synphys/microns_functional_coverage_contract.json), [코드](../../verify/Q-NPF-04/allen_synphys/microns_functional_coverage.py), [결과와 대상 ID](../../verify/Q-NPF-04/allen_synphys/microns_functional_coverage_result.json)에 고정 입력·선택·집계를 남겼다. 원자료 해시, 이전 선택 root 목록과 연결 수, 오프라인 재계산을 확인했다. 결과는 [데이터 원장](../../ledger/data_registry.md)에 등록했다.

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_functional_coverage.py --verify`.
