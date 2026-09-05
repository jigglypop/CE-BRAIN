# Allen 상층 E-E 연결 검출 조건 재검토

앞선 231쌍은 양방향 `has_synapse`가 비결측인 모집단이다. 이번에는 표지 존재와 충분한 검사 수를 구분했다. 기존 원본과 파생표를 재사용했으며 이전 집계는 덮어쓰지 않았다.

[공식 연결 분석 코드](https://raw.githubusercontent.com/AllenInstitute/aisynphys/current-release/aisynphys/connectivity.py)의 `pair_was_probed`는 흥분성 연결에 `n_ex_test_spikes > 10`을 사용한다. 이는 자료 유지와 검사 부족 배제 사이의 실무적 기준이며 검출 완전성을 보장하지 않는다. 열람한 current-release 기준을 명시적으로 적용했으며 DB 생성 당시 코드와 같은 판본이라는 주장은 하지 않는다.

| 조건 | 쌍 수 | 양쪽 없음 | 한쪽 연결 | 양방향 연결 |
|---|---:|---:|---:|---:|
| 양방향 모두 검사 수 >10 | 190 | 168 | 19 | 3 |
| 적어도 한 방향이 기준 미달 | 41 | 40 | 1 | 0 |

462개 방향 중 59개는 검사 수가 10 이하였고, 결측은 없었다. 최소 0, 최대 1773이었다. 따라서 앞선 비결측 231쌍을 모두 충분히 검사된 모집단이라고 해석해서는 안 된다. 새 기준에서도 상호연결 3쌍은 남지만, 이것만으로 검출 편향이 제거되거나 전자현미경 결과가 재현되지는 않는다.

79개 절편에 비어 있지 않은 서로 다른 `lims_specimen_name` 79개가 있다. DB의 slice 표에는 명시적인 `donor_id` 열이 없다. 문자열 일부를 잘라 동물 ID로 추정하지 않았으므로 독립 동물 수는 아직 미확인이다. 동물 간 전이 검사는 이 식별 관계를 확인한 뒤 설계해야 한다.

이번 질문인 검사 조건 확인에는 답했다. 비결측 표지가 충분한 검사와 같다는 해석은 성립하지 않는다. 연결 기전이나 CE 인과사슬을 반증한 것은 아니며, 뇌 구조 규명 목표는 미완료다. 다음에는 donor 관계의 공식 매핑을 찾고 검출 기준을 유지한 불확도를 평가한다. 계산 검증은 L0, 범위를 고정한 관측 표지 기술은 BIO_EVIDENCE_L1 상한이다.

- [선택·검출 계약](../../verify/Q-NPF-04/allen_synphys/superficial_ee_detection_contract.json)
- [결과와 검증](../../verify/Q-NPF-04/allen_synphys/superficial_ee_detection_result.json)
- [실행 코드](../../verify/Q-NPF-04/allen_synphys/superficial_ee_detection.py)

원본과 CSV 해시, 모든 방향별 표지 일치, 190+41=231 분할을 검증했다. 실행: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/superficial_ee_detection.py`.
