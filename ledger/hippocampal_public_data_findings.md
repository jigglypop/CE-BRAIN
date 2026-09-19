# 해마의 내용 재활성화: 공개 자료의 실제 분석 범위

2026-09-19. [복원 포인트 검토](hippocampal_reinstatement_findings.md)의 후속이다.
질문은 부분 단서가 들어왔을 때 단서에 없는 경험 내용이 신경활동으로 재현되는가다.
보유 원장과 기존 분석을 먼저 검색한 뒤 공개 후보를 확인했다. 다운로드 성공이나
논문의 유의한 결과를 CE 식의 새 검증으로 취급하지 않는다.

## 1. Rey2025 처리 spike 자료 확보

[Rey Laboratory 공식 페이지](https://www.mcw.edu/departments/neurosurgery/research/rey-laboratory/software-and-datasets)는
CC BY 4.0으로 자료를 제공한다. [MCW Box 원본 폴더](https://mcw.app.box.com/s/00umgwgfmb6fd0w2cw1iehjiuq0nxgwm)에서
미보유 README와 MAT 두 파일만 받았다. Box 갱신시각은 2024-11-27 17:21:23 UTC다.
README의 논문 연도는2024이며 [정식 논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC11781864/)은
2025년1월 출판됐다. 기존 파일은 덮어쓰지 않았다.

| 파일 | Box ID | 바이트 | SHA-256 |
|---|---|---:|---|
| README.txt | 1711264158092 | 2,031 | `2fcda5b4414368d0ccefa7266fab9c5109e12b9ee4fa4ac99e34e667722eb81e` |
| Reyetal_CR_dataset.mat | 1711267381966 | 1,775,611 | `736ad3947a0185a65a9194b0bfc8140b14d14185cab622923980dcc98cd19a08` |

보유 위치는 `data/external/hippocampal_reinstatement/rey2025_processed_v1`이며 합계
1,777,642바이트다. 파일 해시를 분석 소스에 고정했다. 이 자료는 부호화에서 반응한
33유닛의 선별 처리자료다. 전체 모집단·원전압·LFP·음성이나 spike-sorting 재검증 자료는 없다.

## 2. 구조와 시간축 진단

자료에는21세션33유닛(해마19·편도체14)이 있고, 회상 배열은14세션22유닛(해마16·편도체6)에만
있다. 부호화는1,776 neuron-trials, 회상은1,169 neuron-trials다. 동일 행동 시행에 기록한
여러 유닛을 독립 행동 표본으로 세지 않는다. session/story/trial을 묶으면728개다.

회상 배열은4개 story별 trial spike 벡터이고 `trecall_phasic_ms`와 길이가 일치한다.
두 변수의 기준은 문맥 단서 onset이며, story index는 MATLAB의1-based다.
VP 배열은 stimulus별 trial×가변 열수 행렬로,10000은 spike가 아닌 padding이다.
실제 필드명에는 `responsive_stilmulus`라는 오타가 있으며 `cluster`는 `class1`과 같은
문자열이다. 이 자료의 세포 식별자는 session/channel/원문 cluster 조합으로 보존한다.

회상 시각 범위는−658.009부터30,003.028ms이고, 저장 spike 시각은 최대49.209s다.
논문에 기술된 단서1초·회상12초와 바로 일치한다고 가정할 수 없다.
고정1.5초의 회상 전 창이 단서 뒤이면서 명목상13초 안에 있도록 제한하면
1,095/1,169 neuron-trials,680/728 행동 시행이 후보로 남는다. 경계 밖48행동 시행 중
3개는1.5초보다 이르고45개는13초보다 늦다. 음수 시각 하나가3유닛에 반복돼 있다.
이 후보 제한은 **자료 진단용 조건**이며, 정답 판정이나 관측 완전성 보장이 아니다.

초기 MAT 진단에서는 개별 시행의 정오답, 환자ID 대응, 기록 시작·끝과 결손 마스크가
없었다. 환자 대응은 이후 공식 Table S1에서 확보했다(아래 §3). 마지막 spike가
일찍 끝났다고 이후를 미관측으로 확정할 수도, 그 뒤를 모두 무발화로 확정할 수도 없다.
회상 유의성 변수 `is_signif_recall`로 유닛을 재선택하지 않았다.
따라서 현재 결과로 복원 성공률·환자 모집단 효과·유닛 사이 인과성을 계산하지 않는다.

저자의 회상 분석창은 identity 발화 시작 기준[-1500,+500]ms다. 이는 발화 뒤도 포함한다.
회상 baseline은 단서 전이라고 기술되어 있으나 숫자 범위는 지정되지 않았다.
[-900,-100]ms는 부호화 반응 검출 기준이므로 회상에 저자 규칙으로 옮겨 쓰지 않는다.
VP도 기억 과제 전후를 합친 자료여서 순수 학습 전 localizer라고 부르지 않는다.

재현 경로는 [입력 진단 소스](../verify/Q-NPF-04/hippocampal_reinstatement/rey_input_audit.py)와
[결과](../verify/Q-NPF-04/hippocampal_reinstatement/rey_input_audit_result.json)다.
결과는 유닛·시행·중복 행동 키별 원 시각과 제외 이유를 보존한다. 효과창 최적화나
CE 계수 적합은 하지 않았다. 전체 자료를 금지하는 판정은 아니며, 시간축과 관측지원
가정을 명시한 제한적 재분석은 가능하다.

입력 parser 검증에서 cluster의 문자열 형식과 VP의 가변 열수를 반영했다. 최종 출력은
764,900바이트이며 SHA-256은
`df9a25f791c5feb62da0ab700fdc360bc1fcaf1950786ce709e9abea139f1eda`다.
소스 SHA는 `f2735d12933f1ba14cc8a1c3c54e25dc22dd3d7f0c76308fab69b6e29bb1d176`이다.
별도 읽기 전용 집계가 위 수치와 전부 일치했다. 728개 중복 행동 키의 시각은 유닛들
사이에서 모두 같았고,469개 VP 행렬의176,833개 padding은 모두 행 끝에 있었다.
이 일치는 parser·집계의 검증이며 원기록의 시간축·관측지원 문제가 해결됐다는 뜻은 아니다.
실행은 보존 실행기로 `python verify/Q-NPF-04/hippocampal_reinstatement/rey_input_audit.py`다.

## 3. 공식 보조표와 코드로 보완한 입력 경계

[Document S1](https://pmc.ncbi.nlm.nih.gov/articles/instance/11781864/bin/mmc1.pdf)의 PDF9쪽
Table S1 설명은 sessions1–4=P1,5–6=P2,7–8=P3,9=P4,10=P5,11=P6,
12–15=P7,16–18=P8,19–21=P9라고 명시한다. 전체9명의 연구 내 익명 식별자다.
따라서 MAT에 환자 필드가 없다는 초기 진단을 환자 대응 자체가 불가능하다는 뜻으로
확대하지 않는다. 원 입력 진단 파일은 당시 상태로 보존하고, 새 분석에만 이 매핑을 넣는다.
파일은 `data/external/hippocampal_reinstatement/rey2025_support_v1/session_participants.json`이다.

[공식 저자 코드 v1.0.0](https://zenodo.org/records/14260489)은 CC BY4.0이며,
`surro_strength_recall.m`은 저장 spike에서 `trecall_phasic_ms`를 빼고
[-1500,+500]ms를 직접 센다. 13초 제한·개별 정오답·관측지원 검사는 없다.
`plot_all_responses_matrix.m`의6–7줄은 `tmin_base=-600`, `tmax_base=-100`이지만,
92·94줄은 `x < -tmin_base`와 `x > -tmax_base`를 사용한다. 실제 구간은 단서 기준
**+100부터+600ms**이며, mention 정렬은105–106줄에서 나중에 수행한다.
이는 논문의 단서 전 baseline 설명과 구현이 일치하지 않는다는 진단이다.
저자 원본을 수정하지 않으며, 새 단서 전 구간을 저자의 원 규칙이라고 주장하지 않는다.

공식 설명과 코드에서도 저장 spike 최대 시각이 세션마다 다른 이유, 명목13초보다
늦은 mention의 의미, 개별 시행의 관측 범위는 해명되지 않았다. 특히 session19의
mention 최대30.003초와 저장 spike 최대20.024초를 획득 종료·시계 오차의 증명으로
해석할 수 없다. 마지막 발화와 기록 종료는 다르다. 정확한 place/person/action 회상이라는
논문 기준은 있지만, MAT의 각 시행을 확인할 정오답 필드와 제외 전 ID는 없다.

보조PDF2,459,524바이트와 code ZIP18,552바이트는 조사 중 받은 Temp 원본을 복사해
보존했다. SHA-256은 각각 `9676809de4309c0184e5030ef720bc67204c8078bbd99f601a96a86e56702b5a`,
`302491a6e6592a1635b47c4f31cd246b69d650a157e1b0d98af94ce532b9f075`다.
획득 예외도 남긴다. Europe PMC supplementaryFiles의1바이트 Range 탐색에 서버가
206 대신200으로 전체13,809,303바이트 ZIP을 보내 조사 상한8MiB를 넘었다.
조사 에이전트가 신규 임시 payload를 즉시 삭제했고 해시는 확보하지 못했다.
이를 정상적인 범위 수집으로 기록하지 않는다. 응답 header와 예외 경위는 같은 디렉터리의
`range_probe_headers.txt`, `acquisition.json`에 보존했다. 이후에는 응답 상태 확인 뒤
상한을 적용하는 스트리밍 수신을 사용하며 이번 조사에서 추가 다운로드는 하지 않았다.

## 4. 문맥과 내용의 별도 표현을 확인할 후속 근거

[Bausch et al., Nature2026](https://www.nature.com/articles/s41586-025-09910-2)는
내용과 과제 문맥을 주로 다른 신경집단이 나타내고 함께 활성화되는 결과를 제시한다.
따라서 ‘내용에 반응하는 한 유닛’을 곧바로 ‘특정 사건의 주소’와 동일시할 수 없다.
이 논문은 다음 회로 가설의 근거이며 CE 연결식의 검증 결과는 아니다.

[공식 GitHub](https://github.com/mabausch/ContentContextNeurons)의 커밋
`ea7f8ef6c95fd6f2c442df171ebf10f97fc8079c`에는30개 blob,합계3,609,432바이트가 있다.
MIT 라이선스이며 `all_unitinfo.mat`은 metadata, `rmANOVA.mat`은 효과크기·p값,
`fig4data.mat`·`fig5data.mat`은 cross-correlation·decoding 등의 처리 그림 자료다.
공개 코드의 site/session 조건을 metadata에 적용하면3,109유닛·49세션·16환자가 된다.
trial spike 변수 `q_sptimes`, `im1_sptimes`, `im2_sptimes`, `strialinfos`는 주석 속
재계산 코드에만 있고 파일 트리에는 없다. 공개 그림 결과의 재검산은 가능하지만,
새 spike-level 방향성·지연 모형의 적합 자료가 확보된 것은 아니다.

보조 후보 [OpenNeuro PAL1](https://openneuro.org/datasets/ds005059)은 단서와 응답 행동을
함께 제공하지만, 함께 보인 A+B와 회상에 다시 보이는 A를 비교하는 것만으로 비제시
B의 신경표현을 분리하기 어렵다. [Norman2019](https://zenodo.org/records/3259369)는
해마–피질 회상 자료와 코드를 제공한다. 개별 사진 단서는 없지만 얼굴/장소 범주 지시가
있는 자유회상이다. 최초 조사에서는 두 대형자료를 다운로드하지 않았다. 2026-09-20
[후속 입력 확인](hippocampal_norman_inputs_findings.md)에서 Norman의 작은 항목71개를
확보하고 부호화–회상 내용과 전기 활동의 실제 대응을 조사하기 시작했다.

## 5. 다음 조건

후속 원문 점검에서 네 story는 **각각 다른 전체 문맥**임을 확인했다.
`R1`과 `NR1`의1은 공유 문맥 ID가 아니다. 논문 Methods의21세션 중5세션은
identity가 장소여서 같은 장소·다른 사람이 등장한다. 따라서 모든 identity를 인물로
한정하지 않는다. MAT의 실제 identity partition도 sessions1–15의{1,2}/{3,4}에서
sessions16–21의{1,3}/{2,4}로 달라져 유닛별 제공 index를 써야 한다.
원문 XML의 `p0035`, `p0170`, `p0180`, `p0185`와 README를 근거로 하며,
기존 Temp XML147,079바이트를 `data/external/hippocampal_reinstatement/rey2025_story_metadata_v1`
에 복사했다. SHA-256은 `90d795666e0d0cd98b22d215e8067936699a30e886bba9649f1416085b1467d1`이다.
새 다운로드는 없다.

논문은 block마다 네 story를 pseudorandom 순서로 반복했다고 기술하지만 MAT에는
block·절대시각·교차 story 순서·cue 이미지와 story 내용이 없다. 저장된 반복 행을
시간 순서로 단정하거나 R1/NR1을 공유 문맥의2×2 요인 설계로 분석하지 않는다.
가능한 검토는 같은 identity의 다른 story를 남긴 전이와, 같은 identity 안의
두 story 조건 구별이며, 어느 쪽도 해마 사건 주소 자체를 측정한 것은 아니다.

[발화 전 판독 분석](hippocampal_premention_readout_findings.md)에서 시간 제한과 보조표
환자 대응을 적용했다. 발화 전 내용 구별 신호는 남았으나 VP에서 옮긴 확률 예측은
동일확률 기준보다 나빴다. 시간축·관측지원은 여전히 가정이며, 창 선택과 확률 보정을
같은 평가 자료 전체에 다시 맞추지 않았다. [후속 story 전이](hippocampal_story_transfer_findings.md)에서
training story로만 보정한 내용 판독의 확률 이득은 남았으나, 같은 내용의 다른 story 조건
구별은 미지지였다. 전체 자료를 이미 본 후향적 교차검증이며 독립 전향 실험은 아니다.
Bausch 처리 자료는 문맥-내용 결합과
전후 lag의 별도 재검산에 쓸 수 있으나, 공통 입력·선택 편향을 제거한 새 인과식으로
승격하지 않는다. 목표는 내용 재활성화·사건 구별·방향성·계량을 각각 관측으로 연결하는 것이다.

2026-09-20 [냄새–장소 집단 기록의 입력 연결](hippocampal_odor_place_input_findings.md)을
추가했다. DANDI001539의 CS39_06 NWB에 누락된 냄새·정오답을 공식 Figshare v3 라벨과
정확한 시각으로 연결했다. 23시행이며 초기 지역 집계2/9는 표 행 해석 오류였다.
원 tetrode 대응으로 CA1 5유닛·PFC 6유닛이다. 이 최초 입력 단계에서는 신경 배열을
분석하지 않았다. 후속 [조건부 선택 판독](hippocampal_choice_readout_findings.md)은 별도
적격 세션 집합을 평가했다. 냄새와 목표 방향이 결합돼 있어 단서 판독만으로 기억 검색을 입증하지 않는다.
기존 사람 자료의 제한은 그대로이며 새 쥐 자료가 그것을 소급해 해결하지 않는다.
