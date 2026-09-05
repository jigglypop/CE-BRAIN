# ICMS93 원처리 코드와 NWB 변환의 확인 경계

원본 분석 코드를 확인한 결과, 부피 영상과 평면 촬영 시계의 구분이 필수다. 현재 NWB의 짧은 유효 구간을 그대로 연속 생리 반응으로 해석하거나, 추정한 배율로 늘려 보정할 근거는 아직 부족하다. 전기생리도 펄스 직후 신호 제거 구간을 생물학적 억제로 오인하지 않아야 한다.

## 확인된 출처

저자 공개 저장소의 전체 파일 트리를 받아 로컬 코드와 Git blob 해시를 비교했다. 트리 기준은 `d1922d16913b50bf6338ff4e0c2953cb8ef43d15`이며 목록은 잘리지 않았다. 영상 처리·시행 구성·전기생리 전처리 파일 세 개가 로컬 사본과 정확히 일치했다. 원 코드 파일은 재다운로드하지 않았다. [저자 코드 판본](https://github.com/XieLuanLab/icms-activation-plasticity/tree/d1922d16913b50bf6338ff4e0c2953cb8ef43d15)

공개 파일명에서 `nwb` 또는 `convert`를 포함한 경로는 찾지 못했다. 이는 다른 저장소나 비공개 위치에도 변환 코드가 없다는 증거가 아니다. 표본 NWB의 `general`에도 실행 변환 스크립트 필드는 없었다. 공개 분석 코드의 일치는 이 NWB를 실제로 만든 코드·실행 판본의 확정을 대신하지 않는다.

## 영상: 평면 시각과 부피 축

`NeuroAnalysis_BehavioralParametricSweepBlockExtractTest.m`은 `imgStarts`와 자극 시각으로 평면을 구분하고, 평면 수를 이용해 부피별로 묶는다. `preFrames4D`의 축은 영상 x·y·z와 부피 반복으로 구성된다. 불완전 구간을 자른 뒤 부피 반복을 평균하는 경로가 있다. 따라서 부피 반복 한 칸과 평면 한 장의 촬영 간격을 같다고 가정할 수 없다.

NWB 설명은 부피별 ROI ΔF/F를 전기생리 기준 시계에 재배치하면서 약 30.125 Hz를 평면별 촬영률로 명시한다. [앞선 전체 배열 검사](Q_NPF_04_ICMS93_영상시간축_유효범위.md)는 101개 유효 구간과 728개 유효 행만 확인했다. 두 설명 사이의 시간 단위 대응은 아직 추적되지 않았다. 변환 시 시간 압축이 있었을 가능성은 남지만, 현재 증거로 오류를 확정하지 않는다.

원 코드의 영상 분석 창도 전기 자극열 길이와 다르다. 자극 종료 뒤 추가 시간을 포함해 형광을 모으고, 부피별 유효 평면을 다룬다. 이 원처리 의미를 확인하지 않고 NWB에서 자극 직후 지연이나 회복 시정수를 추정하지 않는다.

## 행동과 세포 ID

공개 `dataloader.py`의 시행 번호는 1부터 시작하며 `trial_start`·`trial_end`는 자극 시작·종료 표지에서 가져온다. NWB의 `trial_index` 설명은 0-based라고 적혀 있으나 실제 시작값은 1이었다. 현재 검사는 숫자 offset을 적용하지 않고 명시적 키로 결합했으므로 해당 설명 차이에 의존하지 않는다. 이 공개 경로가 NWB 변환에서 그대로 쓰였는지는 별도 확인이 필요하다.

영상의 `roi_id_source`는 원 `ROI.mat`의 0-based ROI 번호라는 설명이다. 세션을 넘어 유지되는 세포 ID나 전기생리 unit과 영상 ROI의 동일세포 대응 키라고 기술하지 않는다. `units/cell_type` 역시 파형의 trough-to-peak 분류에 따른 추정 세포형이다. 이를 독립 조직학 표지나 확정된 억제성 세포 ID로 승격하지 않는다.

## 전기생리: 자극 아티팩트 처리

공개 `icms_pipeline.py`는 펄스 주변 신호 제거, 아티팩트 주형 차감, 보간, 최종 제거를 수행한다. 시간 설정은 펄스 전 0.5 ms, 초기 후 1.4 ms, 최종 후 1.5 ms다. 100 Hz 펄스열에서는 각 펄스 사이 간격과 비교해 무시할 수 없는 관측 손실이다. 이 코드가 해당 NWB의 실제 실행 경로였는지는 아직 확인되지 않았으므로 정확한 유효 시간 마스크를 확정하지 않는다.

다음은 저장된 spike time을 펄스 주기에 대조해 결손 패턴이 있는지, 그리고 처리 코드의 시간 설정과 맞는지 확인하는 입력 진단이다. 실제 펄스 시각이 제공되지 않으면 정규 펄스열 근사와 실제 이벤트를 구분해야 한다. 신경 반응 분석은 해당 결손과 catch 정의를 확인한 뒤 관측 가능한 구간에 한정해 설계한다.

## 판정

원처리의 시간 단위·세포형·ID 의미를 좁혔지만 NWB 변환 실행 계보는 미확인이다. 현재 `BIO_EVIDENCE_L0`의 출처·측정 검사이며, 개입 효과나 전체 뇌 인과 기전을 확립한 것은 아니다. 변환 코드 미확보는 영상 지연 해석을 제한하지만 전기생리 관측 가능성 검사를 막지는 않는다.

## 근거

- [원 코드 해시 대조 기록](../../verify/Q-NPF-04/allen_synphys/icms93_source_chain_audit.json)
- [저자 저장소 파일 트리](../../data/external/xie_icms_plasticity_2025/author_repo_tree_20260905.json)
- [부피 영상 처리 코드](../../data/external/xie_icms_plasticity_2025/code/processing/imaging/volumetric/NeuroAnalysis_BehavioralParametricSweepBlockExtractTest.m)
- [시행 구성 코드](../../data/external/xie_icms_plasticity_2025/code/processing/dataloader.py)
- [전기생리 전처리 코드](../../data/external/xie_icms_plasticity_2025/code/processing/preprocessing/icms_pipeline.py)
