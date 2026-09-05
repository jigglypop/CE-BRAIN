# 고정 뉴런 역치 반응과 저장 TP 시각 검사

유형: 연구 검증 원장. 판본일: 2026-09-05. **지위: 실제 FastRheo 반응의 지정 소신호 영역 부적격(`BIO_EVIDENCE_L1` 관측) / TP 속성·시간 인덱스 확보(`L0`) / 연결 전도도·공간 리만 메트릭 미확립.**

[전체 프로토콜 조사](고정뉴런_전체프로토콜_입력적격성.md)에서 찾은 일곱 독립 입력 방향이, 실제 작은 막 반응을 보이는 시행들에서도 유지되는지 검사했다. 같은 Allen experiment 2771의 뉴런 위치와 정체를 고정하고, FastRheo sweep 16–34의 19×7 기록을 읽었다. **정한 일곱 세포 소신호 기준을 통과한 시행은 16번 하나뿐이어서 입력 rank가 7에서 1로 줄었다.** 따라서 지정한 전체 시간창의 선형 전달 예측은 실행하지 않았다.

동시에 별도 TP 속성 자료에서 24,974개 시각 행과 headstage·ADC/DAC·mode·holding 필드를 확보했다. 원장 TP 시각과 별도 속성 기록 사이의 차이도 확인했다. 이 진전은 실제 측정의 대응 조건을 개선하지만, 전극 교정이나 뇌 계량의 확인을 뜻하지 않는다.

## 1. 고정한 점과 이번 측정모형

대상 네 점은 중심 device 4(cell 15834), 잎 device 1·2·5(cell 15832·15833·15835)다. 함께 기록한 device 0·6·7도 일곱 세포 전달모형의 입력과 관측에 포함한다. 위치 고정은 막전압이나 흥분성을 상수로 가정한다는 뜻이 아니다.

이상적인 IC 단자 모형에서는 $C\dot v+Gv=i$이고, 기록 전압을 $w=v+E_{\rm res}i$로 쓰면

$$
Z_{\rm rec}(s)=(sC+G)^{-1}+E_{\rm res}
$$

이다. $E_{\rm res}$에는 보상 후 남은 전극·기준전극 영향이 들어간다. 실제 기록에는 필터와 주입 전류 교정도 필요하다. 따라서 이번 시간별 전압/전류 전달계수를 곧바로 $G$, 막용량, 접합 전도도나 공간 계량으로 바꾸지 않는다.

FastRheo의 실제 명령은 25–28 ms의 3 ms 양의 펄스다. 여러 시행에서 진폭·활성 채널이 달라져 합친 입력 rank는 7이었다. 이 입력들이 같은 작동점의 작은 반응을 만드는지가 이번 선행 검사다.

## 2. 원파형 개봉 전 고정한 기준

전체 numerical 원장의 응답·QC 요약은 이미 노출됐다. 이번 검사는 **개발 단계**이며 미열람 독립 확인으로 부르지 않는다. 다만 아래 분할·시간창·판정 기준은 해당 FastRheo acquisition 원파형을 처음 읽기 전에 명세와 코드에 고정했다.

| 항목 | 고정값 |
|---|---|
| 학습 | 짝수 16·18·20·22·24·26·28·30·32·34 |
| 평가 | 홀수 17·19·21·23·25·27·29·31·33 |
| 원래 입력 rank/조건수 | 학습 7 / 75.0764, 평가 7 / 156.5068 |
| 기준선 | 시행 시작 5–20 ms의 상수 평균, 반응 이후 자료 사용 안 함 |
| 반응 창 | 25–100 ms, 본 자극과 이후 회복을 포함 |
| 기준선 RMS | 각 채널 ≤0.5 mV |
| 기록 전압 변화 | 기준선 대비 최대 절댓값 ≤10 mV |
| 고전압 배제 | 반응 창 최대 기록 전압 <−20 mV |
| 작동점 범위 | 각 채널 기준선이 16번 기준선에서 ±2 mV 이내 |
| 사용 조건 | 일곱 채널 모두 통과; 초기 기준선 잡음도 적격이어야 함 |
| 예측 실행 조건 | QC 후 학습 rank 7·조건수 ≤100, 평가 ≥3개 |

−20 mV 규칙은 큰 고전압 사건을 제외하는 계산 기준이며 완전한 발화 검출기가 아니다. 10 mV와 ±2 mV도 이번 모형 적용 영역의 운용 기준이다. 이를 통과해도 신경 회로의 선형성이 증명되지는 않는다. 탈락한 평가 시행을 학습으로 옮기지 않는다.

조건을 통과했다면 학습 자료만으로 시간별 전체 7×7 전달과 자기 입력만 쓰는 대각 모형을 맞춰 같은 평가 기준선 아래 비교하도록 구현했다. 실제 판정에서는 선행 조건이 충족되지 않아 이 적합과 예측을 실행하지 않았다.

## 3. 실제 반응과 rank 변화

![역치 자극의 기록 전압과 적격성](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_fastrheo_response.png)

그림의 파형은 0.1 ms 평균이고 QC는 원래 0.02 ms 표본에 적용했다. 원장 결과에는 전체 19×7 파형의 0.1 ms 평균과 각 기준·실패 이유를 남겼다.

| 실제 결과 | 값 |
|---|---|
| 일곱 세포 모두 적격 | sweep 16만 |
| 적격 학습 / 평가 | 1 / 0개 |
| 적격 학습 입력 rank | 1 |
| sweep 16 입력 | 일곱 세포 모두 약 100 pA |
| sweep 16 최대 기록 변화 | 8.488917 mV |
| sweep 17 입력 / 최대 변화 | 모두 약 200 pA / 17.203768 mV |
| 전체 예측 | 미실행: QC 후 학습 rank와 평가 수 부족 |
| 원자료 추가 다운로드 | 0 byte; 보유 범위 재사용 |

기준선 변화도 별도 원인이었다. device 0의 기준선 범위는 약 −68.519~−62.926 mV였고, 19개 중 14개가 16번 대비 ±2 mV 범위를 벗어났다. device 6은 반응 크기 기준을 16번에서만 통과했다. 이 원인들을 묶어 실제 뉴런 자체의 비선형성이나 전극 이상으로 단정하지 않는다.

대상 네 점만 보면 16·30·31·32·33번이 기준을 통과했다. 하지만 **30–33번에는 네 대상 뉴런의 명령이 모두 0이고 device 6만 약 1,110–1,140 pA로 구동됐다.** 이것을 네 점의 독립 입력 표본으로 세면 안 된다. 다른 기록 세포의 큰 반응과 경계 영향을 지운 채, 네 점만의 닫힌 전달행렬을 역산하지 않았다.

현재 판정은 **지정한 25–100 ms 전체 창에서 작은 기록 반응과 충분한 독립 입력을 동시에 확보하지 못함**이다. 연결 부재, 실제 전도도 0, 일반적인 예측 실패, 모든 시간창의 비선형성을 의미하지 않는다. 큰 반응까지 포함하는 선형·비선형 모형이나 더 이른 국소 반응을 새로 검사할 수 있지만, 그것은 별도 개발 질문이며 이 결과의 성공으로 바꾸어 부르지 않는다.

## 4. 별도 TP 속성의 실제 구조

[MIES의 현재 공식 NWB1 설명](https://alleninstitute.github.io/MIES/IPNWB/doc/nwb1.html)은 `StoredTestPulses`와 TP property 저장 영역을 구분한다. 이 문서는 경로 탐색에 사용했고, 2019년 파일의 구조와 의미를 현재 버전 그대로라고 가정하지 않았다. 실제 보유 파일에서 직접 다음을 확인했다.

| 자료 | 확인 내용 |
|---|---|
| `StoredTestPulses_*` | 1,250×7 또는 ×8 float32 |
| `IGORWaveNote` | UTC timestamp 문자열 |
| 시간 scaling | 0.02 ms 간격, 1,250표본 |
| 파형 데이터 단위 속성 | 비어 있음; 전류·전압 단위는 별도 대응 필요 |
| `TPStorage` | 32,768×8×22, float64, 실제 layout version 10 |
| 실측 property 필드 | UTC 시각, headstage, ADC/DAC, clamp mode, holding, ValidState 등 |
| 시각이 채워진 행 | 0–24,973의 24,974개, 시간 순서 단조 증가 |
| 시간 범위 | 2019-03-13T22:46:10.050Z~2019-03-14T00:03:46.911Z |

선택한 property 열만 읽고, TP의 Peak/Steady resistance·baseline 열과 별도 TP 파형 본문은 읽지 않았다. 8개 파형 표본(번호 0·1·10·100·1000·10000·10001·10002)에서는 같은 번호 property 행이 최근접이었고, property 시각은 파형 note보다 **7–10 ms 뒤**였다. 이는 번호·시각의 대응 근거이며 모든 번호의 완전한 동일 사건 대응을 증명한 것은 아니다.

TPStorage의 headstage 축은 8칸이다. 뒤쪽 대상 시각에서 headstage 3은 NaN/ValidState 0이고 나머지 일곱 칸은 headstage 0·1·2·4·5·6·7, ADC 0·1·2·8·9·10·11, DAC 0·1·2·4·5·6·7로 대응한다. **파형의 압축된 7열 순서가 곧 이 순서라고 아직 가정하지 않는다.** ValidState 1도 생물학적 교정 완료를 의미하지 않는다.

## 5. 원장 TP와 별도 property 시각·holding

[이전 TP 검사](고정뉴런_시험펄스_교정가능성.md)에서 선택한 원장 TP 시각에 가장 가까운 property 행은 다음과 같다. 이는 시간상 후보 대응이며 원장에 기록한 저항값을 계산한 바로 그 파형인지 확인한 단계는 아니다.

| VC sweep | property 행 | property−원장 TP 시각 (초) |
|---:|---:|---:|
| 0 | 17611 | −1.365 |
| 1 | 17644 | −1.519 |
| 2 | 17671 | −1.509 |
| 3 | 17700 | −1.498 |
| 4 | 17727 | −1.512 |
| 5 | 18085 | −1.394 |
| 6 | 18111 | −1.510 |
| 7 | 18140 | −1.468 |
| 8 | 18169 | −1.529 |
| 9 | 18198 | −1.485 |

각 후보 행의 유효 headstage 간 timestamp 차이는 0–1 ms다. 동일한 UTC epoch 변환을 사용해도 원장 TP 기록보다 1초 이상 앞선다. 따라서 **원장 timestamp를 실제 TP 파형 취득 시각과 동일하게 취급하지 않는다.** 기록·계산·저장의 지연 원인은 과거 실행 코드와 실제 파형을 더 대조해야 한다.

이 열 개 후보의 `HoldingCmd_VC` 원시 수는 유효 일곱 칸에서 모두 약 **−70**이다. 그런데 acquisition VC 5–9번의 기록 설정은 약 **−55 mV**였다. field 자체에는 물리 단위나 업데이트 의미가 충분히 기재되지 않아, 이를 실제 단자막전압 −70 mV로 확정하지 않는다. 이 값이 mV holding을 뜻한다면 뒤쪽 acquisition 설정과 차이가 있다. 시간·mode가 가깝다는 이유만으로 동일 holding에서의 교정이라고 가정할 수 없다는 기존 한계를 구체화한다.

이전 삽입 TP의 직접 계산값이나 원장 저항 비교는 해당 관측으로 보존한다. 새 property 대응으로 참 전극저항을 얻었다고 승격하지 않고, 원장 값·저장 파형·삽입 파형이 어떤 조건에서 대응하는지 확인한다.

## 6. 다음 조건과 실제 메트릭의 남은 다리

이번에 확인한 것은 입력의 독립성, 기록 전압의 운용 영역, TP 시각·채널 속성이다. 뉴런 위치를 고정한 채 연결과 전류의 방향으로 공간 메트릭을 표현하려면, 여전히 **관측 전압/전류 → 전극·막·경계 분리 → 연결 효능 → 열린 경계의 계량 사상 → 구성에 쓰지 않은 방향별 비용**의 근거가 필요하다.

다음 직접 검사 대상은 특정 property 행에 대응하는 `StoredTestPulses_*`의 **note 시각·7열 순서·단위 → 해당 TP 파형과 property 저항의 일치 → 원장·삽입 TP와의 조건 차이**다. 공통 TP만으로 기준전극과 접합을 분리하지 못한다는 반례는 유지한다. 역치 자극 경로는 현재 전체 창 소신호 모델을 채택하지 않으며, 조기 응답이나 상태 의존 모델을 검토할 때 새 조건과 예측을 명시해야 한다. 기존 원파형·응답 요약의 노출 상태도 유지한다.

## 7. 재현과 인계

| 산출물 | 경로 |
|---|---|
| FastRheo 반응·조건부 예측 코드 | [code](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_fastrheo_response.py) |
| 개봉 전 고정한 명세 | [specification](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_fastrheo_response_specification.json) |
| 실제 반응 결과 | [result](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_fastrheo_response_result.json) |
| 관련 계산 검사 | [tests](../../tests/test_electrical_star_fastrheo_response.py) |
| 그림 | [renderer](../../verify/Q-NPF-04/fixed_points_metric/render_electrical_star_fastrheo_response.py), [SVG](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_fastrheo_response.svg) |
| 저장 TP·property 구조와 속성 | [code](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_stored_tp_metadata.py), [result](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_stored_tp_metadata_result.json) |
| TP 시간·headstage·state 인덱스 | [code](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_stored_tp_index.py), [result](../../verify/Q-NPF-04/fixed_points_metric/electrical_star_stored_tp_index_result.json) |

FastRheo 결과 SHA-256은 `9ab47533e5719ebd838da48d0d3a33b06c6adf879d44ed2fa94f1912edeac1a1`, TP 속성 결과는 `ee4044e97be74d7689e98d894c54dd86562d47f38028cd63ffacd409a7e3fe69`, TP 인덱스 결과는 `0a20a9b05d1f95769a226bac225371a2d6cd72324cd466990a8aaa64d6c724f2`다. 각 결과에 코드·입력·reader 해시와 원격 판본·block 목록을 남겼다.

새 다운로드는 TP 속성 327,680 byte와 property 인덱스 9,502,720 byte, 합계 **150 block / 9,830,400 byte**다. FastRheo 원파형은 기존 cache를 재사용했다. 최종 cache는 **2,085 block / 136,642,560 byte**이고 전체 NWB는 636,162,713 byte다. 자료와 산출물은 [데이터 원장](../../ledger/data_registry.md)에 등록한다.

검사: `.codex/hooks/python.cmd pytest tests/test_electrical_star_fastrheo_response.py -q` **3개 통과**. 25–28 ms 자극 포함, 양의 독립 입력으로 교차 반응 복원, 평가 입력으로 학습 rank를 보충하지 않는 조건을 확인했다. 문서 검사 `.codex/hooks/python.cmd python .codex/hooks/repository_harness.py`도 통과했다. 원장 결과와 시각·열 대응은 읽기 전용 독립 검토를 마쳤다.

인계: 저장소 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`, HEAD와 마지막 확인 원격 tip `cfcbc894b83f838c9ced5401297c3a10f11e1f8f`. 변경은 위 산출물·PNG·본 원장, `.codex/PRD.md`, 데이터 원장과 새 raw block이다. 기존 변경은 보존했고 커밋·배포하지 않았다. **뇌 구조·공간 리만 메트릭 검증 목표는 미완료다.**
