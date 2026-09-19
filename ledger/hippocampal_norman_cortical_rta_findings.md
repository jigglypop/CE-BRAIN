# Norman2019 별도 피질 RTA: 수집 완료와 사건 연결의 경계

2026-09-20. 기존 MVPA에서 미확인으로 남은 별도 all-visual 피질 RTA 파일을 확보하고
숫자 배열·표·설정 전체 구조를 검사했다. 이 파일의 존재만으로 개별 ripple에 대응하는
피질 사건값이 복원된다고 가정하지 않았다. 새 모형 적합은 하지 않았다.

## 검증한 수신과 보존

출처는 기존 Zenodo3259369/FreeRecallSWRv1.0.0 ZIP 안의
`Ripple_triggered_cortical_reactivation_across_visual_ROIs/data/RTA_all_visual_channels.mat`다.
이전에 등록된 ZIP 목록을 재사용했고 전체 ZIP을 다시 받지 않았다.

| 판본 | 파일 수 | 보존 바이트 |
|---|---:|---:|
| `norman2019-cortical-rta-v1` | 7 | 431,860,437 |
| `norman-cortical-rta-schema-v1` | 14 | 203,674 |
| `norman2019-cortical-rta-parts-v1` | 28 | 431,865,433 |

압축 항목431,857,478B, 해제 MAT431,836,315B, CRC32 `aebb47ae`를 확인했다.
MAT SHA는 `095f8a3166e4f17385a9b8e74a4c612d52efef82a1d41ce4e335ef22cfe6bf01`다.
압축 조각26개와 local header는 원 수신 위치에 보존하고 해제 MAT·수집 소스·영수증·
실패 기록은 저장소 데이터 경로에 복사한 뒤 SHA를 다시 확인했다.

첫 collector는 목록 키 오류로 네트워크 전0B에서 실패했다. 수정 collector의
session9502는 chunk022를16,762,116/16,777,216B만 받은 실제 short-body로 종료했다.
이 실패를 보존하고 session58748에서 부족한15,100B만 재개해 정상 종료했다.
완료 청크의 재수신은 없었다. 실제 네트워크 본문431,857,990B는448MiB 상한 이내다.
완료 범위 응답27개는 모두206이고 Content-Range·길이를 검사했다. ETag는 모든 응답에
없었으며 전체 ZIP MD5는 검증하지 않았다. 수집 도중의 위치 기록은 완료 기록으로
덮어쓰지 않고 후속 판본을 추가했다.

## 실제 숫자 배열과 표

[통합 구조 결과](../data/local/hippocampal-reinstatement/norman-cortical-rta-schema-v1/final_summary.json)와
[typed metadata](../data/local/hippocampal-reinstatement/norman-cortical-rta-schema-v1/rta_typed_metadata.json)를
보존했다. 통합 결과 SHA는
`c5f53ca4fb62122a5afde0ed5225bb1de3fecd5646bf284da7c0c92a9ac5d0ed`다.

| 변수 | 실제 구조 | 사건 연결의 지원 |
|---|---|---|
| DATAbyChannel | 21조건: 비-viewing17개 `[49,253,212]`, viewing4개 `[212,467]` | 조건 집계, 원 사건 축 없음 |
| ERPbyChannel | 비-viewing17개 `[212,857]`, viewing4개 빈 배열 | 원 사건 축 없음 |
| viewing_spectrogram | preferred/nonpreferred 각 `[49,467,212]` | 원 사건 축 없음 |
| RTA0/1/2 | channel/item 두 문자열 열 | 원 event ID·run·ripple index·시각 열 없음 |
| electrode_param.A/B | 각212개 cell, 서로 다른 길이의 숫자 벡터 | 표본별 출처와 RTA/시각 대응 key 없음 |
| ItemResponse/ItemResponseNU | 각 `[212,28]` scalar numeric | 개별 사건 식별자 없음 |

RTA 표의 여섯 문자열 배열은 기존 MVPA 표와 전량 같다. NPZ SHA도
`d6ab4aead576772c7680600326e4fa71f99f87f0180fbf0324bb80ab873c54ac`로 같다.
A의 cell 길이는1..101, 총7,852값 중7,842유한이고 B는1..100, 총6,645값 중6,635유한이다.
이 벡터를 임의로 RTA 행 순서나 원 ripple 시각에 붙이지 않는다. A/B에 숫자가 있다는
사실과 개별 사건의 수치·출처가 함께 식별된다는 것은 다르다.

저장 설정은 `norm_flag=0`, `ref_flag=2`, `specflag=1`,
`time_locking_event="onset"`이다. `t_out`은253점−756..756, 간격6이고
`t_out_stim`은467점−0.648..2.148, 간격0.006이다. 단위 필드가 없으므로 두 배열을
같은 초 시계로 직접 합치지 않는다. 설정값만으로 전체 생성·평균·정규화 규칙을
확인했다고 주장하지 않는다.

## 해마 검색 연구의 다음 조건

[공통 사건표](hippocampal_norman_event_observations_findings.md)는 원 ripple3,577개와
행동470행의 시각을 보존한다. 그러나 이번 파일에도 이 시각과 숫자 피질 반응을
원 사건 단위로 잇는 typed key가 없어 사건별 피질 feature와 원 시계의 동시지원은
확인되지 않았다. 이 파일을 받으면 관측 경계가 해소될 것이라는 가능성은 실제 구조
검사로 좁혀졌다. 저자 원생성 코드나 별도 사건 자료가 존재하지 않는다는 판정은 아니다.

다음 입력은 원 생성 경로에서 수치 표본과 사건의 대응을 복구할 자료이거나,
[CML 후보](hippocampal_cml_input_findings.md)처럼 사건 정렬 출처를 확인할 수 있는
연속 신호다. 리플·행동 시각만으로 빠진 피질 반응을 추정해 채우지 않는다.
기존 prototype 전이의 음수 결과와 후향 ripple 검출 조건도 그대로 유지한다.
해마의 주소 지정·검색, 학습에 따른 관계 변화, 물리 변화 비용의 계량과 현재 표현의
선택을 잇는 전체 생물학적 기전은 아직 미확립이다.
