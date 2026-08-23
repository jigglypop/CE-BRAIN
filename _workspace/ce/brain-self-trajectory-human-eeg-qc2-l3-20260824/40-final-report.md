# BA-SELF2-L3 최종 보고: scale-free QC의 교차-피험자 실패

Status: COMPLETE

Final disposition: `APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC / R1_KILLED / MODEL_ENDPOINT_UNOPENED`

이 실행은 경로 정보가 현재 EEG 상태만으로는 설명하지 못하는 미래 변화를 예측하는지 시험하기 *전에* 측정 장치의 전이 가능성을 시험했다. 결과는 명확하다. `sub-01`에서 고정한 무차원 품질 게이트가 `sub-02`의 D1-QC에서 총 32쌍 가운데 13쌍만 통과시켰고, 두 세션은 각각 8/16과 5/16이었다. 사전 규칙인 총 24/32 및 각 세션 12/16을 모두 충족하지 못했으므로 R1은 죽었고 D2, C1, C2, C3를 열지 않았다. 이 보고에는 경로 식의 적합도, 미래 target, feature, loss, 모델 선택, 자아 또는 의식의 결과가 없다.

## 질문과 경계

검사하려던 경험적 질문은 현재 관측 quotient, 국소 변화율, 시작점, 길이, 에너지와 증분 통계를 이미 조건으로 둔 뒤에도 순서가 있는 과거 경로가 100 ms 뒤 EEG 변화를 추가 예측하는가였다. 이 질문은 자아가 순간 상태인지, 이어지는 과정의 길인지에 관한 존재론적 판정이 아니다. 유한 EEG 관측에서는 과거를 확장된 현재 상태에 포함할 수 있고, 관측 kernel을 나눈 quotient만 식별한다. 따라서 무한 차원 다양체, 의식, 해마 hash, 뇌 기전, 일반 인구에 관한 주장은 이 실행에서 미완성으로 남는다.

## 바뀐 장치와 변하지 않은 범위

선행 BA-SELF1은 `sub-01`의 절대 진폭 cutoff를 `sub-02`에 옮겼을 때 실패했다. BA-SELF2는 신호 변환, target, 경로 area, 모델 menu, split과 성공 기준을 바꾸지 않고 품질관리만 다음의 scale-free 지수로 바꾸었다. 필터 뒤 창 $X$에서 각 채널 시간 중앙값을 빼고 그 robust MAD를 분모로 삼아 $Q_A$를 만들고, 한 표본 차분의 robust MAD를 분모로 삼아 $Q_D$를 만들었다. 그러므로 두 지수는 공통의 0이 아닌 gain과 시간 불변 채널 offset $X'_{tc}=aX_{tc}+b_c$에 정확히 불변이다. 단, 채널마다 서로 다른 gain, 시간에 따라 달라지는 gain, 또는 더 일반적인 montage/생리 차이에 불변이라는 주장은 하지 않는다.

이 구별이 중요하다. 절대 크기 문제를 공통 gain 문제로 오인하지 않도록 만든 비율이었지만, 그 비율 자체가 피험자 사이의 창 내 구조 차이를 안정적으로 가르는 장치임은 입증하지 못했다. 따라서 여기의 실패는 경로 면적 식의 반증도 아니고, 자아·의식 가설의 반증도 아니다. `sub-01`에서 만든 QC gate가 `sub-02`로 전이되지 않았다는 장치 결과다.

## 사전 고정된 장치 시험

각 task/rest anchor는 5 kHz 원자료에서 정확히 768,256 byte의 HTTP range로 읽고, 63 scalp channel common-average reference, causal 45 Hz FIR, 250 Hz decimation을 거쳐 $126\times63$ 창으로 만들었다. 모든 A1/A2/D1-QC range는 HTTP 206, Content-Range, byte 수, ETag와 A0 lock을 만족했다. nonfinite와 0/비유한 robust scale은 없었다.

A2의 64개 창만으로 고정한 cutoff는 $c_{Q_A}=17.42618346743071$ 및 $c_{Q_D}=18.530899806141665$였다. 이 값은 A2의 각 지수에 대해 median $+6\,$MAD로 한 번만 계산했고 이후 바꾸지 않았다. A1과 A2는 exact-range 및 hard-domain 장치 gate를 통과했다. 그러므로 D1의 실패는 range 응답, byte schema, 비유한 값 또는 영 scale의 실패가 아니다.

D1-QC에서는 32 task/rest 쌍 중 19쌍이 거절되었다. 창 수준 초과 사유는 $Q_A$ 22회와 $Q_D$ 4회였으며, 한 쌍은 둘 중 하나의 창만 실패해도 거절했다. 통과한 13쌍은 통계 효과의 표본이 아니라, 사전 정의된 장치 통과 수를 채우지 못한 잔여물이다. 이 결과가 뜻하는 것은 이 particular cutoff와 비율 정의가 두 피험자에 걸친 QC 전이 gate로 충분하지 않다는 것뿐이다.

## 열리지 않은 분석

D1은 명시적으로 QC 전용이었다. quotient 좌표 $z$, 미래 target, ordered-path feature, 손실, $M_0/M_1$, ridge fit, 모델 선택을 계산하지 않았다. 따라서 “경로가 예측력을 더했는가”에는 긍정도 부정도 없고, `STOP_NO_ORDERED_HISTORY_GAIN`도 아니다. D1 32쌍은 새 모델 실행에 재사용할 수 없으며, D2 132쌍과 `sub-03`의 C1/C2/C3 25/50/175쌍은 미개봉·봉인 상태다.

현재 동결 원장 SHA-256 `d1cc612c7f27a219b577b641145e95cdff467ea928b43be6d670616544b13232`은 이 상태를 장치 실패로만 기록한다. 경로 식과 그 제한된 관측-quotient 해석은 `[미완성]`, 이번 D1 전이 실패는 `[결과: 장치 검증]`이며, 생물학적·존재론적 결론으로 승격하지 않는다.

## 재개 조건

R2는 이 실행의 threshold를 낮추거나 D1을 다시 돌리는 수리가 될 수 없다. 새 계약은 D1을 이미 소진된 QC signal로 보존하고, D2와 `sub-03`을 계속 봉인한 채, 새롭고 signal-blind한 장치 subset에서 독립적인 QC 정의·cutoff·adverse control을 먼저 고정해야 한다. 그 새 apparatus 계약이 교차-피험자 통과 조건을 만족한 뒤에만 별도 model-development 계약을 열 수 있다.

## 재현 기록

핵심 실물 산출물은 A1 receipt `37f82cea31a36f4d036422dcaea8b92fa2d8198f2d8d62d740f78eb7f2a4a79e`, A2 receipt `0427207665cd3411ade82fcef157187e199cbaa5923e337f100790db39ed121b`, D1-QC receipt `7ea150e088625774b75ce1ceec35b8529e3abae470348fa4f693188e3820d28a`이다. 장치 구현은 `scale_free_qc.py` SHA-256 `9740d04ab8198a403d94d9c825b1a8f7279c159854fb6403f84da8c4a48685a4`, focused synthetic test는 `test_scale_free_qc.py` SHA-256 `ad14e403d8c647a433f7dccedfa736c5730b3e821636cf7b687c177aed651cf8`이며, 해당 test는 Python 3.11.9 / NumPy 2.4.6에서 `10 passed in 0.11s`였다. 이는 affine-invariance와 fail-closed 구현 검증이지 생물학적 증거가 아니다.

계약·출처·수학·경로·감사는 각각 SHA-256 `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`, `54c318e3d42af474c253e97c2a9b56f83fe906959239b380c81365027defe55f`, `403c7d73d01d8d736aff2db220d74f985cbcf9b4ff3d6aeb1c7173c1e8d7f827`, `b4cb7f0115a9158c9b9b02e2835845104eefaa4a7f398de8884ef2e8ece7206c`, `c91670bfc8e3fd1d9d95b22fe5ff886996408db10e958098f2f2a9dfc43e548d`로 동결했다.
