# MICrONS 기능 단위와 동일 스캔 대응

## 확인 결과

기존 구조 표본에서 기능 대응 표시가 있던 **486개 세포 모두** 공개 수동 대응표의 기능 영상 단위에 연결됐다. 대응은 598행이며 100개 세포가 여러 기능 단위를 갖는다. 세포 수와 기능 단위 수를 독립 표본 수로 합치지 않았다.

시냅스 표지 1개 이상 기준 구조 연결 7,976개 중 양 끝 세포가 같은 `session, scan_idx`를 공유하는 연결은 **955개**, 같은 field까지 공유하는 연결은 **413개**다. 이는 동시 분석에 필요한 기록 범위 후보이며, 실제 유효 시계열 확보나 기능 연결 검증은 아니다. **L0 입력 결박**이다.

## 수집과 판본

[공식 정적 보관 안내](https://tutorial.microns-explorer.org/materialization-version.html)의 경로 규칙을 사용했다. v1718의 정적 header 요청은 HTTP 404였고 v1412의 header는 200이었다. v1718 자료 전체가 없다는 뜻은 아니다. 이번에는 공개 보관된 v1412 `coregistration_manual_v4`의 header 240바이트와 gzip 942,486바이트를 처음 받았다. [수집 영수증](../../verify/Q-NPF-04/allen_synphys/microns_coregistration_acquisition.json)에 URL·ETag·해시·판본을 기록했다.

표 전체는 19,181행, 서로 다른 nucleus는 15,439개다. 한 `session, scan_idx, unit_id`가 여러 nucleus에 배정된 충돌은 0개였다. 이 수는 v1412 정적 표 기준이며 다른 판본의 안내 숫자와 혼합하지 않는다.

정적 merged CSV의 `id`는 해당 대응 행 ID이고, nucleus 연결에는 `target_id`를 사용했다. 대상 세포의 nucleus ID와 xyz 좌표가 모두 같고 기능 단위의 nucleus 배정이 유일할 때만 연결하도록 먼저 고정했다. 486개 대상에서 누락과 거부 행은 없었다. 반응 크기나 연결 유무에 따른 대상 교체는 하지 않았다.

598개 대응 중 v1412와 보유 v1718의 root ID가 다른 행은 358개였다. [공식 판본 지침](https://tutorial.microns-explorer.org/materialization-version.html)은 nucleus ID 같은 정적 annotation을 판본 간 식별자로 권장한다. 이번 일치는 nucleus·좌표에 근거하며, v1718의 수동 대응 내용 전체가 v1412와 같다는 증명은 아니다.

## 구조와 기록 범위

| 최소 시냅스 표지 수 | 양 끝 기능 대응 구조 연결 | 같은 스캔 공유 | 같은 field 공유 | 같은 스캔의 상호 연결쌍 |
|---|---:|---:|---:|---:|
| 1 | 7,976 | 955 | 413 | 32 |
| 3 | 205 | 23 | 9 | 0 |

모든 수는 중복 없는 구조 edge 또는 무방향 상호 연결쌍 기준이다. 여러 스캔에서 관측된 edge를 반복 가산하지 않았다. 대상 기능 단위는 총 16개 session·scan 조합에 걸친다. 일부 스캔은 대상 세포가 1~2개뿐이며 큰 스캔은 58개다. 스캔을 독립 동물 복제로 해석하지 않는다.

같은 스캔이어도 실제 겹치는 시간, 누락 프레임, 시계열 품질, 자극 동기화는 아직 확인하지 않았다. 같은 field는 더 엄격한 기록 구분이지만 역시 유효 동시 반응을 보증하지 않는다. 이 표는 Allen SynPhys의 세포쌍과 직접 대응하는 표가 아니다.

## 다음 실행 조건과 검증

다음은 고정된 기능 단위 키에 맞는 공개 반응 파일을 확보해 시간축·자극·품질과 단위를 확인하는 것이다. 구조 edge와 상관관계를 비교하더라도 공통 자극·공통 입력을 통제해야 하며 상관을 단일 시냅스 인과 효과로 바꾸지 않는다. 현재는 전체 뇌 구조와 통합 인과사슬 모두 미확립이다.

[계약](../../verify/Q-NPF-04/allen_synphys/microns_coregistration_join_contract.json), [코드](../../verify/Q-NPF-04/allen_synphys/microns_coregistration_join.py), [전체 대응·스캔별 결과](../../verify/Q-NPF-04/allen_synphys/microns_coregistration_join_result.json)를 보존했다. 원파일 해시와 오프라인 재계산을 확인했으며 수집 파일과 파생 결과는 [원장](../../ledger/data_registry.md)에 등록했다.

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_coregistration_join.py --verify`.
