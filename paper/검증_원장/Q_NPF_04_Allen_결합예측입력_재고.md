# Allen 결합 예측 입력 재고

Allen 인간 상층 TCx의 기존 511쌍에서 피질 위치·생리 입력을 함께 사용할 수 있는 후보는 362쌍이다. 독립 검증에 필요한 수치 입력은 일부 확보됐지만 환자 식별과 측정 절차의 대응은 아직 확인되지 않았다. 이 결과는 자료 적격성 점검이며 생물학적 가설 지지나 독립 복제가 아니다.

## 질문과 자료

[양방향 결합 예측](Q_NPF_04_양방향결합_환자제외예측.md)의 후속으로, 다른 기관의 자료에서 같은 입력을 구성할 수 있는지 검사했다. 데이터 원장에 등록된 `synphys_r2.1_small.sqlite`를 읽기 전용으로 재사용했다. 새 다운로드나 연결 결과에 따른 모형 선택은 없었다.

기존 Allen 인간 TCx, 두 세포 모두 비시냅스 정보로 분류한 흥분성 세포, 목표 층 2·2/3·3, 양방향 연결 판정 존재, 각 방향 검사 스파이크 >10 조건을 유지했다. 511쌍·97기록·70절편을 재현했다. 절편 수는 환자 수가 아니다.

## 입력 보유 결과

세포 항목은 두 세포 모두 유한한 값이 있어야 계산했다. 양수 조건은 생리 비율의 로그를 구성할 수 있는지 확인하는 최소 조건이며 저자의 전체 품질 검사를 대신하지 않는다.

| 항목 | 사용 가능한 쌍 |
|---|---:|
| 피질 표면 거리 `cortical_cell_location.distance_to_pia` | 488 |
| 정상상태 입력저항 `intrinsic.input_resistance_ss` | 478 |
| 위 입력저항이 양수 | 460 |
| 역치전류 `intrinsic.rheobase` | 396 |
| 위 역치전류가 양수 | 396 |
| 양방향 세포 간 거리 | 511 |
| 피질 거리·입력저항·역치전류·쌍 거리가 모두 유한 | 373 |
| 위 조건과 양수 입력저항·역치전류 | 362 |

기존에 검사했던 `cell.depth`는 절단면에서의 깊이다. 이번에는 별도 테이블의 `distance_to_pia`가 존재하고 값도 다수 보유됨을 확인했다. 따라서 절단면 깊이만 있다는 가정으로 피질 위치 비교 전체를 닫으면 안 된다. 다만 이 재고만으로 좌표 산출 방식·단위·Planert 회전 좌표와의 동등성이 입증되지는 않는다.

저장된 intrinsic 스키마는 `input_resistance`를 반응 정점의 저항, `input_resistance_ss`를 정상상태 저항으로 구분한다. Planert의 정상상태 저항에 대응할 후보는 후자지만 전류 단계·추정 방법·단위와 QC의 대응은 추가 확인해야 한다.

## 진행 조건

DB 전체 테이블의 열 이름에서 `donor` 또는 `patient`를 포함한 항목은 발견되지 않았다. 인간 절편의 `meta`에도 키가 없었다. 저장된 slice 스키마는 `lims_specimen_name`을 절편 표본의 이름으로 설명한다. 이를 검증 없이 환자 ID로 사용하거나 공개 메타데이터를 조합해 신원을 추정하지 않는다. 이 점검은 외부 공식 자료에도 연결 키가 없다는 증거는 아니다.

- **완료:** 입력 보유 여부와 기존 검사쌍·기록 집합 재현, 세포 테이블 조인의 유일성 확인.
- **준비됨:** 최대 362쌍에서 공통 수치 입력을 구성할 후보 경로.
- **미확립:** 환자 단위 분리, 두 자료의 측정·QC 대응, 결합 예측의 독립 재현.
- **다음 행동:** 공식 스키마·산출 코드에서 피질 위치와 생리 측정 정의를 확인하고, 공개된 비식별 기증자 그룹 연결이 있는지 조사한다. 그 전에는 절편 제외 평가를 환자 제외 평가로 보고하지 않는다.

## 재현 근거

- [재고 계약](../../verify/Q-NPF-04/allen_synphys/allen_human_joint_input_inventory_contract.json)
- [검사 코드](../../verify/Q-NPF-04/allen_synphys/allen_human_joint_input_inventory.py)
- [결과와 검사쌍별 보유 플래그](../../verify/Q-NPF-04/allen_synphys/allen_human_joint_input_inventory_result.json)
- [저장된 생리 스키마](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__database__schema__intrinsic.py)
- [저장된 절편 스키마](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__database__schema__slice.py)

계약 SHA-256: `e7a55da35b51b1c7de95f67edd1e5b44b5cf75c278985a91b2bf164cc12c2bfd`。
