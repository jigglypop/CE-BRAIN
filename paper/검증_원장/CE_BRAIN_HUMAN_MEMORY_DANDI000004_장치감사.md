# CE-BRAIN 인간 기억 DANDI 000004 장치 감사

Status: `HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE`

기준일: 2026-08-31

## 목적과 계보

X-미로에 빠졌던 encoding/recognition 의미를 명시적으로 가진 자료가 있는지 감사한다. 긴 로드맵은 DANDI 000004를 인간 기억 후보로 지정했지만, 현재 동물 기억·통합모델이 확립되지 않았으므로 이 자료는 **Phase 14 confirmation이 아니라 인간 개발 장치**로만 사용한다.

## 잠금

- DANDI: `000004@0.220126.1852`
- asset: `77e12554-96c7-4ee4-97b3-50aaba00ed9f`
- file: `sub-P19HMH_ses-20080601_obj-1tmj21e_ecephys+image.nwb`
- bytes: 72,614,400
- SHA-256: `451697a72654a4d742c872a66edc56ab59f94cfdbfa1cbb37f93f0a70b39f998`

## score-blind schema 결과

- 학습 100 trials, 인식 100 trials
- 인식 response code 31–36가 모두 유효
- embedded image pixel SHA-256으로 학습 자극과 인식 자극을 대조하면 exact-old 50, exact-new 50
- 학습·인식 각각 중복 이미지 없음
- amygdala 계열 unit 15개 존재
- spike time 값은 이 감사에서 분석하지 않음

## 발견된 metadata 모순

NWB 열 설명과 논문은 `new_old_labels_recog: 0=old, 1=new`라고 적는다. 그러나 embedded image의 pixel SHA-256을 직접 비교하면 이 파일에서는 label 1의 50개가 학습 이미지와 정확히 같고, label 0의 50개는 하나도 같지 않다.

따라서 후속 분석은 설명 문자열을 믿지 않고 **학습 이미지와의 exact pixel identity**로 old/new를 정의한다. 이 차이는 과학 결과가 아니라 변환/metadata 의미 오류다.

## 판정

**[장치 판정]** `HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE`.

동일 이미지의 encoding–recognition pair 50개가 정확히 구성되므로 좌표 복제가 아니라 pair similarity와 전체 관계거리 보존을 검사할 수 있다.

**[claim ceiling]** 한 명의 인간 development session이다. 통과해도 인간 일반화나 전체 CE-BRAIN의 Phase 14 완료로 세지 않는다.

공식 근거:

- DANDI: <https://dandiarchive.org/dandiset/000004/0.220126.1852>
- 데이터 논문: <https://www.nature.com/articles/s41597-020-0415-9>
- PMC 원문: <https://pmc.ncbi.nlm.nih.gov/articles/PMC7055261/>
