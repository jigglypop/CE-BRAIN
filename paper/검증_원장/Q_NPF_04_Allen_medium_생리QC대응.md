# medium DB의 생리 기록과 원본 대응

제작자 선택 조건에 맞는 36기록을 medium DB에서 찾았고, 기록마다 저장된 QC가 통과임을 확인했다. 원본 메타데이터의 시행·전극·자극 이름도 모두 일치했다. 이전 FastRheo의 빈 기준선 문제와 구분되는 결과다. 저장된 QC 판정의 확인이며 전체 원시 QC 재현이나 세포 상태 불변의 증명은 아니다.

## small DB에서 조회하지 못한 이유

보유한 r2.1 small DB는 실험 3337과 전극·세포 정보를 갖지만 `sync_rec`, `recording`, `patch_clamp_recording`, `test_pulse`, `pulse_response` 테이블의 행 수가 모두 0이다. 이 판본에서 기록이 조회되지 않는 것을 원 실험에 기록이 없다는 뜻으로 해석하면 안 된다.

공식 배포 목록의 r2.1 medium은 같은 스키마 버전 22이며 파일 크기는 11,125,997,568바이트다. 원격 파일의 ETag와 byte range를 확인하는 읽기 전용 SQLite 조회 경로를 만들어 필요한 페이지만 읽었다. 신규 전송은 1,835,008바이트였고 전체 파일을 받지 않았다. 부분 블록의 해시와 원격 판본은 별도 캐시에 보존했다.

## 확인된 대응

| 항목 | 결과 |
|---|---|
| 실험 외부 ID | `1574292898.139`, 내부 ID 3337 |
| 표적 전극 | device 2·4·5 |
| TargetV | 시행 7–12, 전극당 6기록 |
| If_Curve | 시행 90–95, 전극당 6기록 |
| 원본과 일치하는 시행·전극 키 | 36/36, 중복 없음 |
| 자극 이름 일치 | 36/36 |
| QC 행의 recording 외래키·IC 모드 | 36/36 |
| 저장된 `qc_pass=1` | 36/36 |

DB에는 자극 구성, holding, 기준선 전압·잡음, 가까운 test-pulse ID도 있다. 이를 바탕으로 원본 파형과 더 자세히 비교할 수 있다. 여기서 test-pulse ID가 있다는 사실을 접근저항 품질 통과로 대신하지 않는다.

읽기 전용 VFS가 SQLite 값을 올바르게 전달하는지 확인하기 위해 로컬 small DB의 실험·전극·세포쌍 조회를 같은 VFS와 기본 sqlite3로 각각 실행해 일치를 확인했다. 원격 조회는 HTTP 206·Content-Range·ETag와 캐시 블록 해시를 검사한다. 이 검사는 medium 전체 파일의 무결성 검사나 모든 DB 행의 원본 대조는 아니다.

## 다음 조건

다음에는 선택된 프로토콜의 원시 명령과 DB에 저장된 자극 구성을 맞추고, test-pulse 정보와 시간적 세포 대응을 검사한다. FastRheo 파형의 결과를 이 36기록의 결과로 대체하지 않는다. 이전의 같은 자료 공개 API 반복 조회 대신, 이번에 확보한 medium 캐시를 재사용한다.

## 재현 근거

- [읽기 전용 조회 계약](../../verify/Q-NPF-04/allen_synphys/medium_recording_lookup_contract.json)
- [부분 SQLite 조회 코드](../../verify/Q-NPF-04/allen_synphys/medium_recording_lookup.py)
- [36기록과 원본 QC](../../verify/Q-NPF-04/allen_synphys/medium_recording_lookup_result.json)
- [메타데이터 대응·VFS 대조 검사](../../verify/Q-NPF-04/allen_synphys/medium_recording_binding_validation.json)
- [공식 배포 목록 사본](../../data/external/allen_synphys_r21/download_urls.json)

APSW 3.53.4.0은 이 작업의 별도 도구 폴더에 설치했다. 과거 분석 환경이나 기존 과학 결과를 변경한 것이 아니다.
