# CE-NPF 대체 생물자료 D3 Maristany 2026 자료획득·형상 결과

> 후속 계약감사 정정: 초기 형상검사에서 `DirOut`을 0/1/3 성능 정본처럼
> 요약했으나, 전체 transition session 감사 결과 valid `Outcomes`와 89회
> 불일치했고 재학습 파생 helper도 공개되지 않았다. 실제 D3는 완전 코딩된
> `Outcomes[:,0]`을 정본으로 잠가 실행했다. 아래 표와 적격성 문구는 이 후속
> 확인을 반영한다.

## 판정

- 획득: `MARISTANY_2026_ARCHIVE_DOWNLOAD_PASS`
- 형상: `MARISTANY_2026_PAIRED_RELEARNING_SCHEMA_PASS_WITH_DECLARED_EXCEPTION`
- 지위: **준비됨**. 행동 생물학 endpoint는 아직 계산하지 않았다.
- 원 질문에 답했는가: 아니다. 동일 마우스 paired control/opto 재학습 endpoint를
  사전 고정할 수 있는 입력인지 확인했다.
- 반증된 것: 없음. 아래 `NWO12` switch-marker 예외는 결과가 아니라 원시
  스키마 예외다.

## 자료 정본과 무결성

- G-Node DOI: `10.12751/g-node.etlk5k`
- 논문: Maristany de las Casas et al., *Science* 392, `eadx4358` (2026),
  DOI `10.1126/science.adx4358`
- 공급자 archive URL:
  `https://doi.gin.g-node.org/10.12751/g-node.etlk5k/10.12751_g-node.etlk5k.zip`
- license: `CC BY 4.0`
- provider headers: `Content-Length=483324456`,
  `Last-Modified=2026-04-18T15:22:07Z`,
  `ETag="1ccef228-64fbda0f374ce"`
- local bytes: 483,324,456
- local SHA-256:
  `b9962e7760ac7299cc968fa4a23d2c965342d78abdded4f937a4081588f09ba3`
- local MD5: `8e3dbe413c089539d15690fb0367383c`
- ZIP: 129 files, uncompressed 483,295,658 bytes, 전 항목 CRC 통과.
- Europe PMC preprint XML `PMC11952515`: 114,380 bytes, SHA-256
  `5d32c1a4455a3a959319a54b4ceed2c78c0d8456b033f42d0cd4735c5690d2ed`.
  이는 2025 preprint 본문 확인용이며 2026 최종 논문 판본을 대신하지 않는다.

## paired behavior 스키마

공급자 README와 논문은 각 동물이 전체 `A -> B -> A'` 5-session paradigm을
control과 NDNF optogenetic stimulation 조건에서 한 번씩, 무작위 순서로
수행했다고 기술한다. 두 조건 폴더에 동일한 10 mouse ID가 모두 존재한다.

`NWO1, NWO3, NWO4, NWO5, NWO6, NWO9, NWO10, NWO11, NWO12, NWO13`

각 mouse-condition 파일의 `cont_data`는 5개 session이고, session 2가
`A -> B`, session 4가 `B -> A'` transition이다. 각 trial에는 적어도 다음
필드가 함께 있다.

| 필드 | 확인한 코딩/용도 |
|---|---|
| `Relearn` | rule A=`0`, rule B=`2`; transition 경계 표지 |
| `TrialTypes[:,0]` | right instruction=`0`, left instruction=`1` |
| `Outcomes[:,0]` | impulsive=`-1`, incorrect=`0`, correct=`1`, omission=`3`; 시간은 두 번째 열 |
| `DirOut` | raw 값은 0/1/3이고 valid `Outcomes`와도 불일치; endpoint 비사용 |
| `Choice[:,0]` | lick direction; 시간은 두 번째 열 |
| `TrialMode`, `AutoRew`, `Confidence` 등 | trial 보조상태 |

공급자 summary `Figure1Relearning_DataSummary.mat`에는 trial 125를 switch로
맞춘 `ABctr_cont`, `ABopto_cont`, `BActr_cont`, `BAopto_cont`와 5-session
`primer`, `opto`가 있다. 공급자 공개 MATLAB driver는 right/left cumulative
correct trajectory, 20-trial block moving average와 정규화 trajectory를
호출하지만, 호출되는 helper 함수는 archive에 포함되어 있지 않다. 따라서
공급자의 비공개 helper를 추정해 논문 수치를 복제하는 대신 raw per-mouse
필드만으로 완전히 적힌 새 endpoint를 고정해야 한다.

## switch-marker 예외와 고정 가능한 복구 규칙

39/40 mouse-condition-transition strata에서는 `Relearn`이 old rule에서 new
rule로 정확히 한 번 바뀐다. `NWO12/Control/A->B`만

`0` 90 trials -> `2` 1 trial -> `0` 5 trials -> `2` through session end

형태다. 값을 삭제·평활하거나 결과에 맞춰 경계를 고르지 않는다. 모든 strata에
동일하게 적용할 수 있는 공급자 의미 기반 규칙은 다음과 같다.

> switch는 `Relearn`이 기대한 new-rule 값으로 바뀐 뒤 **session 끝까지 그
> 값으로 유지되는 terminal run의 첫 trial**이다.

이 규칙은 39개 정상 strata에서는 유일한 change point와 같고, 예외에서는
97번째 trial을 고른다. 이 경계 뒤 right-instruction이며
`Outcomes[:,0] in {0,1}`인 primary eligible trial은 모든 stratum에서 최소
22개이고, impulsive만 제외한 omission-inclusive eligible trial은 최소 23개다.
따라서 결과값을 보지 않고 고정한 두 20-trial 창을 모두 구성할 수 있다.

## 적격성과 남은 한계

이 자료는 다음 좁은 질문에는 적격하다.

- 같은 10마우스 안에서 NDNF activation이 control보다 rule-switch 직후의
  wrong-direction error를 늘리는가,
- 그 차이가 simple `A -> B`보다 complex `B -> A'`에서 더 큰가.

그러나 다음은 입력에 없다.

1. 실제 control/opto 수행 순서를 mouse별로 복구하는 order variable,
2. trial별 laser-on flag와 manipulation-fidelity readout,
3. 이 10마우스와 Figure 2--5 imaging/electrophysiology 동물의 identity join,
4. 같은 synapse의 물리 가중치, 축삭 경로길이·전도속도, 독립 Fisher metric.

따라서 cross-over carryover·period effect를 직접 조정할 수 없고, 행동 효과를
dendritic calcium, synaptic clustering 또는 리만계량이 매개했다고 결론낼 수
없다.

## 다음 허용 행동

mouse를 독립 단위로 하고 switch 규칙, right-trial 선택, omission 처리,
20-trial 창, paired interaction, exact null과 중단조건을 먼저 문서와 코드로
잠근다. 합성 단위검사와 독립 감사를 통과한 경우에만 실제 endpoint를 한 번
실행한다.
