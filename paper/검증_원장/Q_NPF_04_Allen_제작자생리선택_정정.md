# 제작자 생리 선택과 holding 처리 확인

제작자의 내재 생리 분석을 재현할 대상은 앞서 진단한 `LP_FastRheo` 시행 82–89가 아니다. 고정 공식 코드의 실제 선택 함수를 메타데이터에 적용하니, 세 전극 각각에서 `TargetV` 시행 7–12와 `If_Curve` 시행 90–95를 선택했다. 앞선 발화 후보 분석은 별도 프로토콜 진단으로 보존하며 DB 생리 산출의 재현 근거로 사용하지 않는다.

## 프로토콜 선택

`get_intrinsic_recording_dict`는 전류고정 기록 중 `TargetV`, `If_Curve`, `IV_Curve ` 또는 `Chirp`가 이름에 있는 기록을 선택한다. `LP_FastRheo`라는 이름에 LP가 들어 있어도 이 조건을 통과하지 않는다. 해당 함수는 이름을 바탕으로 선별할 뿐, 실제 펄스 존재·명령 세기·품질까지 확인하지는 않는다.

이번 검사는 실제 고정 함수를 호출하되, 원본에서 이미 읽은 전극·자극 설명·clamp 단위를 가진 대리 객체를 입력했다. 파형·QC를 흉내 내지는 않았다. 선택 결과는 전극당 12기록, 전체 36기록이다. 이후 제작자 경로는 DB recording에 연결해 QC를 확인하고 자극 시작·종료를 판독한다. 이 두 후속 조건은 아직 통과하지 않았다.

## holding과 저장 명령의 관계

고정 `MiesTSeries.data` 코드에서 저장 명령은 holding을 포함하지 않으며, command를 읽을 때 holding을 더한다. `MPSweep`은 그 command에서 holding을 다시 빼고 pA로 바꿔 IPFX에 전달한다. 따라서 그 경로에서 IPFX가 받는 자극은 holding에 상대적인 전류 단계다. 앞선 추출의 상대 명령에 holding을 다시 더해 IPFX 입력으로 쓰는 것은 같은 경로의 재현이 아니다.

이는 전류 입력의 의미를 확인한 것이며 실제 전압 응답에서 holding의 생리적 영향이 사라진다는 뜻은 아니다. Bridge 메타데이터는 코드에서 저장값에 10⁶을 곱해 저항 단위로 설정한다. 이 대입만으로 전압을 임의 재보정할 근거는 없다.

## 기준선과 남은 조건

같은 MIES 코드의 `baseline_regions`는 notebook의 onset auto/user와 termination 지연을 사용한다. 따라서 이 값들이 모두 0인 FastRheo에서 빈 기준선이 나온 것은 확인한 코드와 일치한다. 그 결과를 고쳐 통과시키려고 시간창을 바꾸지 않는다.

다음 대상은 제작자가 선택하는 36기록이다. 기존 캐시를 재사용해 원본–DB recording 대응, QC와 실제 명령을 확인한다. 서로 떨어진 시행 7–12와 90–95가 같은 세포·같은 상태를 나타내는지는 별도 검증한다. 새 프로토콜에서 얻은 결과를 원래 반복 자극 시점의 고정 파라미터로 자동 적용하지 않는다.

## 근거

- [선택 검사 계약](../../verify/Q-NPF-04/allen_synphys/producer_intrinsic_selection_audit_contract.json)
- [실제 함수 호출 검사](../../verify/Q-NPF-04/allen_synphys/producer_intrinsic_selection_audit.py)
- [선택된 36기록](../../verify/Q-NPF-04/allen_synphys/producer_intrinsic_selection_audit_result.json)
- [고정 프로토콜·QC 연결 코드](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__nwb_recordings.py)
- [고정 MIES 명령·기준선 코드](../../verify/Q-NPF-04/allen_synphys/source_snapshots/neuroanalysis__miesnwb.py)
- [고정 IPFX 어댑터](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__intrinsic_ephys.py)

없던 두 소스 파일만 수집하고 판본·해시를 데이터 원장에 등록했다. 코드 판본의 경로 확인을 과거 DB 전체 생성 환경의 확정으로 확대하지 않는다.
