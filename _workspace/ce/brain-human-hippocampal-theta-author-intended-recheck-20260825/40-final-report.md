# 인간 해마 iEEG 시간축 교정의 실제 QC 재검산 보고

Status: COMPLETE

최종 처분: `QC_RECHECK1_COMPLETE_ONLY / NO_RAW_RESULT / NO_ENDPOINT / NO_BIOLOGICAL_VERDICT / ENDPOINT1_BLOCKED`

## 요약

이 보고서는 공개 인간 해마 iEEG 자료 두 객체에서 발견한 시간축 오산이 trial 품질관리(QC) 통과 수를 실제로 바꾸는지 재검산한 기록이다. 결론은 제한적이지만 분명하다. 교정한 시간축으로 재계산하자 TS/p17/post의 임상 접촉부 clean trial 수는 11에서 12로, PB/p17/pre의 임상 접촉부 수는 22에서 24로 바뀌었다. 이 변화는 공개 원자료를 다시 내려받아 무결성을 확인한 뒤 계산한 결과이며, 임의로 문턱을 낮춰 만든 결과가 아니다. 다만 이 보고서는 theta, P2P, 조건 효과, 생물학적 기전, 인과, 기억, 의식, CE 또는 AGI를 증명하지 않는다. endpoint 단계는 권한 검증의 P0 결함 때문에 실행하지 않았고, `raw_result.json`도 존재하지 않는다.

이 문서는 시간축이 수 밀리초만 어긋나도 정수 주기 DFT 제거와 QC 경계 근처 trial의 판정이 달라질 수 있다는 점을 실제 데이터로 확인하려는 독자를 대상으로 한다. 순서는 선행 계산의 문제를 정확히 고정하고, 문턱 조정이 아닌 측정 정의의 교정임을 구분한 뒤, 두 공개 객체의 재검산과 그 해석 한계를 제시하는 방식이다.

## 배경과 선행 기록

분석 대상은 OpenNeuro의 version-pinned `ds006065` 공개 자료에 속한 인간 해마 인접 접촉부 iEEG다. 이 자료와 원 연구의 맥락은 [OpenNeuro 데이터셋](https://openneuro.org/datasets/ds006065/versions/1.0.0), Kragel 등의 [2025년 논문](https://doi.org/10.1038/s41467-025-59417-7), 그리고 [저자 공개 코드](https://zenodo.org/records/14735080)에서 확인할 수 있다. 여기서 분석은 연구의 모든 통계 모델을 복제하려는 것이 아니라, 공개 코드가 암시하는 artifact QC와 시간축 정의를 Python에서 author-intended emulation으로 점검하는 데 한정한다.

선행 HPC4 실행은 18개 객체와 총 723,560,000 bytes의 출처 무결성을 확인했지만, clean-trial 판정에 사용한 시간축이 잘못되어 있었다. 그 실행은 `j/999 × (1000/499.5) - 0.5` 초를 사용했다. 그러나 저자 처리의 1,000점 구간과 BrainVision의 표본 간격은 retained sample $j$에 대해 $t_j=j/499.5-0.5$ 초를 요구한다. 두 식은 끝점에서만 다르게 보이는 근사가 아니다. 앞 식은 표본 간격을 약 2.004006 ms로 만들고, 뒤 식은 약 2.002002 ms로 만든다. 그 차이는 999개 점에서 60, 120, 180 Hz를 정확한 정수 주기로 제거해야 하는 DFT 기저와 시간 창 경계를 동시에 흐린다.

따라서 HPC4의 `11/25` 및 `22/11` clean count는 당시 실행이 실제로 낸 기록으로는 보존하되, 교정된 author-intended 측정값으로는 사용하지 않는다. 이 보고서에서는 그 선행 수치를 `APPARATUS_INVALID`인 역사적 기록으로만 부른다. 이는 자료 자체가 잘못되었다는 뜻이 아니라, 그 자료에 적용한 시간 정의가 잘못되었다는 뜻이다.

## 교정 원칙

이번 경로는 MIN20을 MIN10으로 낮춘 완화가 아니다. 공개 저자 코드에는 모든 접촉부·시점·조건이 20개 이상이어야 한다는 전역 MIN20/all-cell endpoint gate가 없었다. 선행 실행의 MIN20은 하네스가 endpoint 실행 전에 붙인 보수적 중단 조건이었다. 반대로 관측된 11개에 맞추어 10개라는 새 문턱을 고르는 일은 outcome tuning이므로 명시적으로 배제했다.

새 하네스는 먼저 시간축과 DFT 정렬을 바로잡고, 그 정의 아래 QC를 통과한 모든 trial을 available-clean 분석의 입력으로 남긴다. clinical 주 분석에서 필요한 최소 조건은 각 고정 cell에 clean trial이 하나 이상 존재한다는 것뿐이다. 그러나 이 원칙은 이번 단계에서 생물학적 결과를 계산해도 된다는 허가가 아니다. 이번에 허가된 것은 두 개의 실패 지점만 다시 계산하는 `QC_RECHECK1`이며, endpoint 단계 `ENDPOINT1`은 별도 권한 검증이 해결될 때까지 막혀 있다.

교정한 격자는 retained sample 0–998 위에서 latency 50–649, baseline 225–245, early 258–274, late 275–374, prestim 100–199를 사용한다. 기본값이 0인 DFT 대체가 sine/cosine 성분을 적합·제거하고 시간창 끝점을 최근접 표본으로 고르는 처리는 [FieldTrip DFT 전처리](https://github.com/fieldtrip/fieldtrip/blob/master/preproc/ft_preproc_dftfilter.m)와 [전처리](https://github.com/fieldtrip/fieldtrip/blob/master/ft_preprocessing.m), [baseline 처리](https://github.com/fieldtrip/fieldtrip/blob/master/ft_timelockbaseline.m)의 공개 구현을 참조했다. 저자 공개 archive에는 p17/p19 PB 호출의 필수 인자 누락과 FieldTrip 버전 미고정이 있으므로, 이 경로는 exact MATLAB 실행이나 출판된 `fitlme`의 동일 복제라고 주장하지 않는다.

## 실제 공개 자료의 재검산

`QC_RECHECK1`은 TS/p17/post와 PB/p17/pre의 version-pinned 원자료 두 객체만 대상으로 한 번 실행했다. 내려받은 총량은 83,300,000 bytes이며, 각 객체에서 기대 SHA-256, 크기, version ID, ETag가 관측값과 모두 일치했다. 완료 receipt의 SHA-256은 `04edcbe5c290985f6a59c230989f4d13d83323e193767559ec4e15562de9e6e6`이고, 상호 결박된 progress journal의 SHA-256은 `da9d5d5f77d31632640faef11b3fb8cc7b44068c849c051d0db658938a06d679`이다.

| 대상 | 이전 grid clinical | 교정 clinical | 이전 grid bipolar | 교정 bipolar |
|---|---:|---:|---:|---:|
| TS / p17 / post | 11 | 12 | 25 | 25 |
| PB / p17 / pre | 22 | 24 | 11 | 11 |

변화는 임상 접촉부의 amplitude 배제에서만 발생했다. TS의 amplitude reject는 48에서 47로, PB의 amplitude reject는 38에서 36으로 줄었다. TS 임상부의 kurtosis·z-score·nonfinite 배제는 각각 6·2·0으로, PB 임상부의 값은 각각 3·2·0으로 이전과 같았다. bipolar 접촉부의 모든 이유별 count도 TS에서 34·1·0·0, PB에서 49·2·2·0으로 이전과 같았다. 즉 교정 효과는 “모든 자료가 더 잘 통과했다”는 일반 주장보다, DFT·시간창 경계에 걸린 특정 임상 trial들의 amplitude 판정이 바뀌었다는 좁은 사실로 읽어야 한다.

동일한 교정 알고리즘을 직접 계산 경로와 SOS 필터 경로로 각각 수행한 A/B 비교도 통과했다. 두 경로의 최대 파형 차이는 $6.071\times10^{-11}$ µV 이하였고, 사전에 고정한 허용차 $10^{-6}$ µV보다 작았다. 이 결과는 두 구현 경로가 이번 두 객체의 QC 판정에서 수치적으로 일치한다는 확인이며, 생물학적 효과의 크기나 방향에 관한 증거는 아니다.

## 형식 지위와 해석 경계

이 보고서의 직접 결과는 `[경험적: 공개 원자료의 사후 측정 교정]`이다. 실제 인간 iEEG 두 객체를 다시 계산하여 시간축 교정이 clean-trial count를 바꾼다는 사실은 확인했다. 또한 source identity, reason mask, amplitude margin, dual-path 허용차를 receipt로 남겼으므로, 단순히 문서 속 숫자를 바꾼 것이 아니라 고정된 원자료에서 같은 현상을 다시 계산했다.

그러나 관측된 두 count 변화는 theta 효과의 존재를 뜻하지 않는다. 이 실행은 late/early/prestim P2P, participant-equal effect $D$, bootstrap 신뢰구간, leave-one-out, p17/p19 짝 비교를 계산하지 않았다. `raw_result.json`과 endpoint progress가 없으며, 현재 권한 상태는 `QC_RECHECK1_COMPLETE_ONLY`다. endpoint receipt 검증기가 trialwise P2P를 raw clean trial에서 독립적으로 되계산하지 못하고 bipolar sensitivity 누락을 권위 있게 배제하지 못하는 P0 문제가 남아 있으므로 `ENDPOINT1`은 `BLOCKED`다.

그러므로 이 결과에서 뇌의 인과 기전, 기억 과정, 의식, CE 또는 AGI에 관한 결론을 이끌 수 없다. 표본은 두 객체의 QC 재검산일 뿐이며, 독립 표본 확인도 아니다. 이 보고서가 증명하는 범위는 더 좁다. 선행 하네스의 시간축 오산이 실제 공개 인간 iEEG의 QC 결과를 바꾸었고, corrected author-intended emulation에서 그 변화가 재현 가능한 receipt로 기록되었다는 점이다.

## 재현 경로

재현은 이 run의 계약, 출처, 수학, 경로 선택, 감사, 구현 및 검증 기록을 함께 읽는 방식으로 가능하다. [계약](00-contract.md)은 두 단계와 claim ceiling을 고정하고, [출처](10-sources.md)와 [수학](11-math.md)은 grid와 자료 identity의 근거를 제공한다. [감사 기록](20-audit.md)은 Stage Q만 허가한 이유와 Stage E를 막은 P0 사유를, [검증 기록](31-validation.md)은 no-network 시험과 실제 one-shot 명령을 보존한다. 실제 QC 산출물은 [receipt](artifacts/qc_recheck1.json)와 [progress journal](artifacts/recheck_progress.json)에 있다.

원자료를 다시 받는 재실행은 이 완료 receipt를 덮어쓰는 방식으로 해서는 안 된다. 이번 run은 one-shot record이므로, endpoint 권한 문제를 해결하거나 다른 표본에서 확장 검증을 하려면 새 계약과 독립 감사가 필요하다. 그 다음 단계에서도 이번의 QC 확인을 biological endpoint나 이론적 증명으로 승격하지 않는 경계가 유지되어야 한다.

## 참고 자료

OpenNeuro, *ds006065: Human hippocampal electrophysiology dataset*, version 1.0.0. [데이터셋 페이지](https://openneuro.org/datasets/ds006065/versions/1.0.0).

Kragel, J. E., et al. (2025), *Nature Communications*. [DOI: 10.1038/s41467-025-59417-7](https://doi.org/10.1038/s41467-025-59417-7).

저자 분석 코드 archive, [Zenodo record 14735080](https://zenodo.org/records/14735080).

FieldTrip, [DFT filter 구현](https://github.com/fieldtrip/fieldtrip/blob/master/preproc/ft_preproc_dftfilter.m), [전처리](https://github.com/fieldtrip/fieldtrip/blob/master/ft_preprocessing.m), [baseline](https://github.com/fieldtrip/fieldtrip/blob/master/ft_timelockbaseline.m).
