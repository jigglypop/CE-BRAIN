# Allen 표본 외래키의 공개 조회

생리 입력을 갖춘 362쌍에 참여한 218개 세포 모두에 내부 `lims_specimen_id`가 있었다. 이 ID들을 공식 공개 Specimen API에 직접 조회했지만 반환된 표본은 0개였다. 공개 API를 통한 환자 외래키 연결은 확보하지 못했으며, 이 경로에서 환자 제외 분석을 시작하지 않는다.

## 방법과 검증

[입력 재고](Q_NPF_04_Allen_결합예측입력_재고.md)의 362쌍을 그대로 사용했다. 연결 유무에 따라 표본을 추가·제외하지 않고 각 세포의 저장된 표본 ID만 읽었다. 공개 API에서 `id`와 `donor_id` 두 열만 요청했다. 이름을 변형하거나 다른 자료의 신원 정보를 추정해 연결하지 않았다.

| 항목 | 결과 |
|---|---:|
| 검사쌍 | 362 |
| 참여 세포 및 보유한 표본 ID | 218 |
| 공개 API 반환 표본 | 0 |
| donor ID를 확보한 쌍 | 0 |

API는 성공 응답을 반환했고 전체 결과 행 수와 실제 반환 행 수가 모두 0이었다. 이는 HTTP 오류나 시간 초과가 아니다. 내부 LIMS에 표본이 없거나 자료가 무효라는 판정도 아니다. 내부 표본 ID와 공개 API의 포함 범위가 대응한다는 전제가 현재 확보되지 않았다. 응답을 저장하고 데이터 원장에 등록했다.

## 이 경로의 결론

[이름 대조](Q_NPF_04_Allen_공개기증자표_대조.md)와 이번 직접 ID 조회 모두 현재 362쌍의 기증자 연결을 제공하지 못했다. 같은 공개 조회의 반복과 이름 조합 추정은 중단한다. 이 분석에서 필요한 것은 해당 릴리스의 비식별 기증자 대응표 또는 이를 명시한 공식 메타데이터다. 연구 목표 전체가 달성됐거나 모든 공개 자료를 소진했다는 뜻은 아니다.

다음 분석 경로를 정할 때는 두 경우를 구분한다. Allen 자료로 계수를 재학습하고 환자 간 일반화를 주장하려면 검증된 기증자 그룹이 필요하다. 다른 자료에서 고정한 예측을 Allen에 적용해 기술적 오차를 계산하는 외부 적용은 가능하지만, 측정 정의의 차이·부분 회로 관측·환자 간 상관을 명시하고 이를 환자 단위 독립 복제로 해석하지 않아야 한다. 어느 경우에도 준비 진전을 뇌 구조의 확립으로 세지 않는다.

## 재현 근거

- [조회 계약](../../verify/Q-NPF-04/allen_synphys/allen_human_specimen_donor_lookup_contract.json)
- [조회 코드](../../verify/Q-NPF-04/allen_synphys/allen_human_specimen_donor_lookup.py)
- [검사 결과](../../verify/Q-NPF-04/allen_synphys/allen_human_specimen_donor_lookup_result.json)
- [저장한 API 응답](../../data/external/allen_synphys_r21/public_specimen_donor_lookup.json)
- [공식 Specimen 관계 설명](https://api.brain-map.org/doc/Specimen.html)

응답 SHA-256: `3370431813a2de3afb606ef7f234ea7b0345af95df7b9816963e18389258a2b2`.
