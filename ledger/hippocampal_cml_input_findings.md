# CML catFR1: 실제 전기 입력과 사건 시계의 불일치

2026-09-20. 해마 사건과 피질의 내용 재활성화를 같은 기록에서 검증할 대체 입력을
조사했다. 공개 metadata, EDF 헤더와 신호1초, 변환 코드만 확인했다. 기억 복원 효과나
사건 전후 전기 반응을 적합한 결과는 아니다.

## 고정 출처와 실제 보유 범위

출처는 [OpenNeuro ds004809 snapshot2.2.0](https://openneuro.org/datasets/ds004809/versions/2.2.0),
DOI `10.18112/openneuro.ds004809.v2.2.0`, commit
`2af9e88db8d4517883dd71733b5be654aa80f088`이다. 생성 시각은2024-04-23이고
license는 CC0다. 표본은 `sub-R1004D/ses-0`이며 다른 환자나 세션까지 일반화하지 않는다.

[보유 조사](../data/external/hippocampal_reinstatement/cml_catfr1_metadata_v1/inventory_result.json)는
120전극·120monopolar채널, 신호1600Hz·5400초, 사건739행을 확인했다.
채널 유형은 ECOG96·SEEG24다. 뇌영역 열은 서로 다른 atlas이므로 하나로 합산하지
않는다. `ind.region`의 cortex115와 `das/stein`의 CA1 2·DG3은 후보 위치 정보이며,
이것만으로 동일 분석 영역의 정확한 생물학적 분류를 확정하지 않는다.

| 자료 | 파일 수 | 보존 바이트 | 검증 범위 |
|---|---:|---:|---|
| `cml-catfr1-metadata-v1` | 22 | 369,859 | 고정판 metadata·공식 접근 경로·소스·응답·manifest |
| `cml-catfr1-edf-probe-v1` | 9 | 502,708 | EDF 헤더·record250·전압 변환·TAL 정정 |
| `cml-clock-consistency-v1` | 4 | 28,995 | 사건 전량의 수치 시계와 list 지원 |
| `cml-clock-source-audit-v1` | 12 | 233,986 | 과거/후속 공식 변환 코드·시계 판정·정정 포인터 |

수신 본문은 metadata327,804B, EDF415,346B, 변환 코드212,440B로 합계955,590B다.
전체 EDF는2,074,246,832B이며 다운로드하거나 전체 SHA를 검증하지 않았다.
Legacy Penn 접근 신청은 하지 않았고 TLS 검증 오류3건은 우회하지 않고 남겼다.

## 실제 EDF 표본에서 확인한 것

[EDF 검사](../data/external/hippocampal_reinstatement/cml_catfr1_edf_probe_v1/edf_probe_result.json)는
versionId가 고정된 S3 객체의 세 범위만 받았다. 모두206·정확한 Content-Range와
Content-Length를 확인했다. EDF+C의 헤더31,232B, 1초 record5,400개,
record당384,114B로 계산한 크기가 API의 전체 크기와 같다.

신호121개는 신경120개와 annotation1개다. 신경 채널 이름은 BIDS monopolar
120행과 순서까지 같다. 실제 헤더의 물리 단위는 모두 uV다. 채널별 digital/physical
범위로 변환한 record250의 값은 유한하며 관측 최솟값−568.803, 최댓값940.861uV다.
README의 일반 단위 설명 대신 실제 헤더 보정을 사용했다. Monopolar는 이미 reference가
적용된 자료이고 이후 분석의 재참조 선택도 따로 기록해야 한다.

초기 prototype의 `annotation_text_record`는 물리값을 문자로 바꾼 잘못된 출력이다.
원 바이트를 읽은 [독립 TAL 보충](../data/external/hippocampal_reinstatement/cml_catfr1_edf_probe_v1/offline_annotation_check.json)의
`+250\x14\x14`를 사용한다. 이것은 EDF의 record 시계를 확인할 뿐, 해당 시각에
WORD가 실제 제시됐다는 독립 증거는 아니다. 한 record의 유효값을 전체 세션의
artifact 없는 관측지원이나 고주파 신호 품질로 확대하지 않는다.

## 행동 시각과 전기 표본 번호는 같은 시계가 아니다

[전량 시계 검사](../data/local/hippocampal-reinstatement/cml-clock-consistency-v1/clock_consistency_result.json)는
739행의 onset·duration이 유한하고 onset이 감소하지 않음을 확인했다.
주석 onset0..3566.601초와 모든 종료 시각은 숫자상 EDF0..5400초 안에 있다.
그러나 이것으로 생리적 정렬이 확인되지는 않는다.

`sample − onset × 1600`은1,362,657.2..1,362,944.0표본으로 변하고 표준편차는
82.638표본이다. 첫 행은 onset0·sample1,362,944다. 단순한 시작점 차이만으로는
설명되지 않으며 onset의 millisecond 반올림 오차보다 크다. 임의의 offset 차감이나
drift 적합으로 정렬을 만들어내지 않았다.

[공식 코드 조사](../data/local/hippocampal-reinstatement/cml-clock-source-audit-v1/clock_source_audit_result.json)는
snapshot 이전 catFR1 경로의 마지막 commit `31edf0f2ce12d0c797d71df21d4877bd0e083d04`
(2024-04-11)을 확인했다. 이는 유력 당시 코드이고 dataset이 이 commit으로 생성됐다는
인증된 연결은 아니다. 해당 코드는 `sample=eegoffset`,
`onset=(mstime-first_mstime)/1000`으로 서로 다른 기준을 썼다. EEG는 event 경계 없이
`reader.load_eeg(scheme=contacts)`가 반환한 기록 객체를 EDF로 내보냈다.
Converter가 첫 행동에서 자르지는 않지만 CMLReader 입력 자체가 clip인지 여부는
이 코드만으로 알 수 없다.

후속 공식 commit `9d9f2bfe3f6ff51de3a2acc53da1c9fe778fed61`(2026-07-13)은
잘못된 onset 기준을 명시하고 `onset=sample/sfreq`로 바꿨다.
[정확한 수정 행](../data/local/hippocampal-reinstatement/cml-clock-source-audit-v1/offline_fix_line_supplement.json)을
함께 보존했다. 후속 코드를2024년 snapshot의 실제 생성 규칙으로 소급하지 않는다.
현재 표의 패턴은 과거 계산과 정합적이지만 원 alignment 변환·당시 실행판이나
독립 sync 증거는 확인하지 못했다. 후속 [sample origin 추적](hippocampal_cml_content_support_findings.md)은
역사적 후보 cmlreaders가 source sample0을 유지하는 경로임을 확인했다.
따라서 독립 생리 정렬의 확증은 남겨두고, 명시적인 native sample 계약 아래 제한
신호 구간을 읽는 단계로 진행한다. 이 조건부 읽기를 동기화 문제의 완전 해소로 세지 않는다.

## 내용 라벨과 다음 진행 조건

주 실험 WORD300개는25목록×12개이고 REC_START/REC_END도 각각25개다.
REC_WORD24개와 REC_WORD_VV111개를 구별한다. 연습 WORD12개는 list−999다.
주 회상 발화는 모두 같은 list의 회상 경계 안에 있다. Events JSON의 목록1..24 설명과
실제1..25는 다르다. List26에는 PROB·START·STOP만 있다. 원 결과의 COUNTDOWN
서술 오류와 첫 정정 파일의 필드 경로 오타는
[새 정정 파일](../data/local/hippocampal-reinstatement/cml-clock-source-audit-v1/interpretation_correction_v2.json)에
분리해 남겼고 해시로 고정된 파일은 덮어쓰지 않았다.

이 자료는 실제 신호에 접근할 수 있는 해마·피질 후보 입력이다. 후속 내용 분석에서
24개 회상 단어 중 same-list 정확 회상은15회/고유13항목이고 나머지는 침입 회상임을
확인했다. 이 구분과 sample 계약 아래 첫 부호화–회상 쌍의 실제 신호를 확인한다.
독립 sync와 사람·세션 간 일반화는 남아 있다. 해마 이력이 피질 내용 판독에 추가
정보를 주는지, 기억 검색·관계 변화·리만 계량의 물리적 변화 비용이나 현재 표현의
선택을 설명하는지는 아직 검증하지 않았다.
