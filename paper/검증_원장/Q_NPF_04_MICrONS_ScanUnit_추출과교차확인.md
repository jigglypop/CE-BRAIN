# MICrONS ScanUnit 추출과 교차 확인

## 이번 질문과 결론

구조상 세포와 실제 형광 반응을 같은 단위에서 비교하려면 스캔의 `unit_id`를 NWB의 `field, mask_id`에 연결해야 한다. 이번에는 공식 v8 배포 파일에서 그 대응표를 확보했다. 오프라인 해독 결과를 두 DB 인덱스로 교차 확인했고, 첫 스캔의 영역별 mask 범위도 NWB와 일치했다. 다만 과거 NWB 변환 시점의 세포 등록과 현재 대응의 동일성은 아직 별도 확인이 필요하다.

이전에는 13개 좌표 후보만 있었다. 그중 **12개는 v8 대응표와 일치하고 1개는 다르다.** 따라서 이전 후보 전체를 확정 대응으로 취급할 수 없다는 실제 반례가 생겼다. 이는 뇌 기전의 반증이 아니라 자료 연결의 불일치다.

## 확보한 원본

[제작자 배포 안내](https://github.com/cajal/microns-nda-access)의 v8 컨테이너 아카이브는 103,798,314,496바이트다. 컨테이너를 실행하지 않고 HTTP 부분 조회로 tar 헤더를 읽었다. 데이터 층은 아카이브의 398,580,224바이트 지점에서 시작하며, 그 안에 358개 항목이 있다.

| 파일 | 아카이브 내 시작 위치 | 크기 |
|---|---:|---:|
| `scan_unit.frm` | 93,896,537,088 | 9,251바이트 |
| `scan_unit.ibd` | 93,896,547,328 | 19,922,944바이트 |

두 파일만 추출했다. 기존 헤더 캐시에서 74,787바이트를 재사용했고, 추출 중 새로 받은 양은 19,857,408바이트다. 이는 아카이브 목록 탐색 때 받은 양과 별개다. 요청 범위·전체 크기·ETag를 확인하고 추출 파일의 SHA-256을 기록했다. 원본과 목록, 해독 결과는 데이터 원장에 등록했다.

## 해독과 검증

[고정한 제작자 스키마](https://github.com/cajal/microns_phase3_nda/blob/0b0acf0f3c9406479ba7a46d338353b8623d8ef1/microns_phase3/nda.py)는 session·scan_idx를 smallint, unit_id를 int, field·mask_id와 위치·지연을 smallint로 선언한다. 모든 해당 열은 고정 정수다. [MySQL 행 형식 설명](https://dev.mysql.com/doc/refman/5.7/en/innodb-row-format.html)에 따라 clustered index의 기본 키 뒤 시스템 필드를 건너뛰고 나머지 열을 읽었다.

최초 구현은 레코드 헤더의 상태 비트 위치를 한 바이트 잘못 읽어 assertion에서 중단됐다. 결과를 저장하기 전에 오프셋을 수정했다. 최종 실행은 다음을 확인했다.

- 기본 인덱스의 leaf 473개에서 **168,971행**을 읽었다.
- 보조 인덱스의 leaf 183개에서도 같은 수의 행을 읽었으며 `(session, scan_idx, field, mask_id, unit_id)`의 전체 집합이 기본 인덱스와 완전히 같았다.
- 페이지별 연결 목록의 순환 없음, 헤더의 레코드 수, 키 정렬, 삭제 표시 없음, 기본 키 중복 없음을 확인했다.
- session 4 / scan 7은 **8,395행**이다. 영역 1–8의 수는 각각 **643, 452, 1,455, 1,389, 1,420, 1,411, 895, 730**으로 NWB 열 수와 같다. 각 영역의 mask 번호는 1부터 해당 개수까지 모두 존재한다.
- 기존 53개 대상의 unit이 모두 있고, 영역 번호도 기존 coregistration 표와 같다.

이 교차검사는 같은 DB 파일 내 두 저장 구조의 일관성 검사다. 독립 생물학적 복제나 MySQL 엔진으로 직접 질의한 결과는 아니다. 최종 해독 코드와 제작자 스키마 해시를 별도 gate에 기록했다.

## 발견한 불일치와 시간 조건

`unit_id=3151`, field 4의 v8 대응은 **mask 601**이다. 이전 NWB 좌표 검색은 **mask 598**을 후보로 제시했다. 다른 12개 후보는 일치했다. 이 한 건의 차이가 과거 등록 판본의 변경인지, 변환 시 행 순서 문제인지, 다른 대응 오류인지는 아직 판별하지 못했다. 원본 NWB 변환 코드는 과거 `functional_coreg`를 조회하므로 최신 표와 같다고 가정하지 않는다.

ScanUnit에는 `ms_delay`도 있다. 제작자 정의는 첫 field의 첫 pixel을 기준으로 각 단위를 읽는 지연이다. 첫 스캔 전체에서 0–154ms, 이번 53개 대상에서는 **33–151ms**다. NWB의 공통 프레임 시간 배열이 같다는 사실만으로 각 세포의 실제 촬영 시점까지 같다고 해석할 수 없다. 지연 보정이 이미 적용됐는지를 확인한 뒤 시간축에 반영해야 하며 중복 보정하면 안 된다.

## 판정과 다음 진행 조건

공식 대응표 확보 질문에는 답했다. 기존 좌표 후보 전체의 신뢰성은 한 건의 불일치로 부정됐다. v8 unit–mask 경로는 전수 교차검사를 통과해 남아 있다. 다음에는 불일치 한 건의 판본·변환 경로와 세포별 지연 처리를 확인하고, 통과한 대응에 한해 반응을 추출한다. 불일치를 감추기 위해 mask 598을 601로 조용히 치환하지 않는다.

이번 결과는 `BIO_EVIDENCE_L0` 자료 동일성 검사다. 뇌 전체 구조·통합 인과 기전의 확립도, 구조와 반응 사이 생물학적 관계의 검정도 아직 아니다.

## 근거 파일

- [tar 목록 조회 코드](../../verify/Q-NPF-04/allen_synphys/microns_tar_index.py), [선택 추출 코드](../../verify/Q-NPF-04/allen_synphys/microns_extract_scan_unit.py)
- [해독 코드](../../verify/Q-NPF-04/allen_synphys/microns_decode_scan_unit.py), [해독 결과](../../verify/Q-NPF-04/allen_synphys/microns_scan_unit_decoding_result.json)
- [첫 스캔 대응표](../../verify/Q-NPF-04/allen_synphys/microns_scan_unit_scan_4_7.csv), [NWB mask 범위 검사](../../verify/Q-NPF-04/allen_synphys/microns_scan_unit_nwb_gate.json)
- [이전 공개 원본 탐색](Q_NPF_04_MICrONS_ScanUnit_공개원본탐색.md), [이전 좌표 후보 판정](Q_NPF_04_MICrONS_ROI좌표_조건부대응.md)

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_decode_scan_unit.py`. 원본 캐시 재검증과 문서 하네스도 통과했다.
