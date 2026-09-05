# Allen과 Planert의 측정 정의 대응

Allen의 수치 입력 362쌍은 비교 후보로 유지한다. 다만 피질 깊이의 산출 방식과 생리 측정 절차가 달라, Planert 모형의 계수를 그대로 적용한 결과를 동일 조건의 독립 검증으로 보고할 수 없다. 이번 점검은 측정 정의의 출처 감사이며 새 생물학적 결과가 아니다.

## 확인한 출처

기존 생리 스키마·파이프라인을 재사용하고, 없던 공식 코드 네 파일을 커밋 `b187927abf1e8df46d11b47eeb88c8e2c76aee3c`에서 받아 데이터 원장에 등록했다. 이 커밋의 코드 경로를 확인한 것이며, r2.1 DB의 모든 행이 정확히 이 커밋과 동일한 의존성으로 산출됐다는 실행 이력까지 확보한 것은 아니다.

| 입력 | Allen 정의와 단위 | 비교에서 필요한 주의 |
|---|---|---|
| 피질 깊이 | `distance_to_pia`, DB 단위 m. 산출 코드의 `absolute_depth`에 10⁻⁶을 곱해 저장 | Planert 회전 좌표의 피질 거리와 산출법이 다름 |
| 정상상태 입력저항 | `input_resistance_ss`, MΩ 결과에 10⁶을 곱해 Ω로 저장 | 정점 기반 `input_resistance`로 대체하지 않음 |
| 역치전류 | `rheobase_i`, pA 결과에 10⁻¹²을 곱해 A로 저장 | holding current를 뺀 자극으로 IPFX에 전달; 발화 판정·자극 단계의 대응은 미확인 |

단위만 맞추려면 Allen의 피질 거리는 10⁶을 곱해 µm로, 저항은 10⁻⁶을 곱해 MΩ로, 역치전류는 10¹²을 곱해 pA로 바꾼다. 같은 단위인 두 세포 값의 비율에서는 이 공통 배율이 소거되지만, 프로토콜 차이나 측정 편향은 소거된다고 가정할 수 없다.

## 피질 깊이는 단순 직선 거리가 아니다

공식 cortical location 파이프라인은 층 그림과 세포 위치를 읽고 `get_depths_slice(..., ignore_pia_wm=True)`를 호출한다. 해당 경로는 직접 표기된 pia·white matter 경계를 무시하도록 설정한다. 이후 층 경계로부터 Laplace 장을 만들고 경로를 따라 거리를 계산한다. 경계가 누락되면 종별 참조 층 두께로 보충할 거리를 계산하는 코드가 있다.

따라서 `distance_to_pia`가 유한하다는 사실만으로 직접 측정된 피질 표면 직선 거리라고 해석하면 안 된다. 362쌍 각각에서 참조값 보충이 얼마나 쓰였는지, 당시 영상·층 경계·의존성 버전이 무엇인지는 아직 확인되지 않았다. 같은 기록 안에서 공통 보충값이 차이에 소거될 가능성도 있지만, 기록별 경계와 산출 이력을 확인하지 않고 소거를 보장하지 않는다.

## 생리 측정은 단위 대응과 절차 대응을 구분한다

Allen 어댑터는 전압을 mV로 바꾸고 명령 전류에서 holding current를 뺀 뒤 pA로 변환한다. 기록마다 자극 시작을 맞추고, 사용 가능한 자극 중 가장 짧은 지속시간까지 분석한다. `LongSquareAnalysis`에 `subthresh_min_amp=-200`을 전달하며 임계 이하·이상 기록 모두를 필수로 요구하지 않는다.

이 호출은 Planert의 고정 전류 단계에 따른 정상상태 반응 평균과 같은 연산임을 보장하지 않는다. IPFX의 실제 사용 판본과 세부 저항 추정·최소 발화 판정은 추가로 추적해야 한다. 값이 있다는 이유만으로 두 자료의 QC가 같다고 판단하지 않는다.

## 진행 판정

- **확인됨:** 단위 변환, 피질 깊이 산출에 층 경계·참조값이 개입할 수 있는 경로, 생리 특징의 IPFX 위임.
- **미확립:** r2.1 행별 산출 판본, 피질 깊이의 직접 측정 동등성, 생리 프로토콜·QC 동등성, 공개 비식별 환자 그룹 연결.
- **다음 조건:** 같은 준비물의 독립 재현 주장을 보류한다. 공식 기증자 그룹 경로와 DB 생성 이력을 먼저 조사한다. 환자 그룹을 확보하지 못하면 절편 제외 평가의 상한을 명시하고, 이를 환자 제외 결과로 대체하지 않는다.

## 재현 근거

- [입력 재고와 362쌍의 조건](Q_NPF_04_Allen_결합예측입력_재고.md)
- [위치 스키마](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__database__schema__cortical_location.py)
- [위치 파이프라인](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__pipeline__multipatch__cortical_location.py)
- [층 깊이 산출](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__layer_depths.py)
- [생리 분석 어댑터](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__intrinsic_ephys.py)
- [기존 생리 저장 단위](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__pipeline__multipatch__intrinsic.py)
- [공식 고정 커밋의 층 깊이 코드](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/layer_depths.py)

네 신규 파일의 SHA-256은 데이터 원장에 기록했다. 원자료·기존 계약·결과는 수정하지 않았다.
