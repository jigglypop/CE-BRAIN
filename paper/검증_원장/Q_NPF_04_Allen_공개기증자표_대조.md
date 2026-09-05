# Allen 공개 기증자 표 대조

공개 Donor API의 정확한 이름 대조로는 현재 생리 입력 표본의 환자 구분을 확정하지 못했다. 기존 511쌍의 표본 이름에서 추출한 45개 세 부분 접두사 중 6개만 API에 존재했다. 생리 입력 조건을 만족하는 362쌍에서는 일치가 0쌍이었다. 이는 공개 API의 이번 조회 범위에서 연결을 확보하지 못했다는 뜻이며, 해당 기증자가 없거나 자료가 잘못됐다는 뜻이 아니다.

## 방법과 결과

[앞선 검사](Q_NPF_04_Allen_기증자그룹_충돌점검.md)는 사이트·번호만 묶으면 앞자리 코드가 다른 이름이 합쳐짐을 확인했다. 이번에는 세 부분 전체를 보존하고 공식 Donor 표의 `name`에 정확히 일치하는 항목을 찾았다. `id`와 `name`만 요청했으며 인구학·질병 정보는 조회 조건이나 연결 근거로 사용하지 않았다.

| 표본 | 세 부분 접두사 수 | 이름이 일치한 검사쌍 | 대응한 공개 Donor ID 수 |
|---|---:|---:|---:|
| 기존 511쌍 | 45 | 22 | 6 |
| 생리 입력 362쌍 | 30 | 0 | 0 |

응답의 성공 상태, 반환 수와 전체 행 수 일치, 같은 이름의 중복 ID 부재를 확인했다. 요청 URL은 계약에, 응답은 데이터 원장에 등록한 JSON에 보존했다. 전체 Donor 표의 탐색 조회는 저장하지 않았고, 실제 결과의 근거는 별도로 저장한 45개 이름 대상 응답이다.

공식 API 문서는 Donor 이름과 Specimen의 donor 관계를 구분한다. 이번 대조는 이름 일치이며 절편의 공식 donor 외래키를 직접 얻은 것은 아니다. 또한 앞자리 코드가 연도를 뜻한다는 해석은 이번 확인 자료에서 확정하지 않았다. 30개 접두사를 30명으로 바꾸거나, 27개 사이트·번호 그룹을 환자 수로 사용하는 해석은 계속 보류한다.

## 다음 판단

이름 기반 API 대조 경로는 362쌍의 환자 검증 근거를 제공하지 못했다. 같은 조회를 반복하거나 이름 형식을 임의로 변형해 일치율을 높이지 않는다. 후속 경로는 해당 표본의 공식 Specimen 관계 또는 해당 릴리스의 직접 기증자 매핑이다. 이를 확보하기 전 새 환자 제외 분석은 실행하지 않는다. 연구 전체가 끝난 것은 아니며, 기존 제한된 연결 예측 결과의 범위도 바뀌지 않았다.

## 근거

- [계약과 정확한 요청 URL](../../verify/Q-NPF-04/allen_synphys/allen_human_public_donor_match_contract.json)
- [조회·대조 코드](../../verify/Q-NPF-04/allen_synphys/allen_human_public_donor_match.py)
- [대조 결과](../../verify/Q-NPF-04/allen_synphys/allen_human_public_donor_match_result.json)
- [저장한 공식 API 응답](../../data/external/allen_synphys_r21/public_donor_name_match.json)
- [공식 Donor 문서](https://api.brain-map.org/doc/Donor.html)
- [공식 Specimen 문서](https://api.brain-map.org/doc/Specimen.html)

응답 SHA-256: `8c7c518efe38153d686c07715c1faabb6a9ce94e6f3c22ea079327c1fdca9c9b`.
