# CE-BRAIN Human Memory 양성대조 R1 계약

Status: `PREREGISTERED / COHORT_LOCKED / ENDPOINT_UNOPENED`

기준일: 2026-08-31

## 1. 목적

P19·P16에서 관계형 retrieval이 미확립된 이유를 두 갈래로 분리한다.

1. 현재 unit 표본과 시간창이 알려진 기억 신호도 검출하지 못하는 **장치 감도 부족**
2. 알려진 old/new 신호는 검출하지만 CE의 exact-item 관계복원만 검출되지 않는 **가설 선택적 긴장**

양성대조는 데이터 논문이 보고한 memory-selective(MS) cell 분석을 따른다. 논문은 recognition stimulus onset 200ms 뒤부터 1초 동안 old 50 대 new 50 firing rate를 비교했고 전체 1,863 cells 중 146 cells(7.8%)를 MS로 분류했다.

## 2. outcome-blind cohort

`CE_BRAIN_HUMAN_MEMORY_독립개체_분할계약.md`의 development 역할만 사용한다. P19·P16은 관계복원 결과가 이미 열렸으므로 양성대조 주 cohort에서 제외한다.

다음 순서로 asset을 열며, 최소 8 subjects와 유효 unit 250개를 모두 채우는 최초 지점에서 enrollment를 멈춘다.

```text
P15HMH → P18HMH → P14HMH → P53CS → TWH100 → TWH088
→ TWH107 → P25CS → TWH101 → P49CS → P55CS → P44HMH
→ P57CS → P37CS → P33CS → ...
```

subject에 object가 여러 개면 분할계약대로 가장 큰 object를 먼저 사용한다. 완전 200-trial 장치 문을 실패한 subject는 과학 음성이 아니라 장치 제외로 보존하고 다음 순서로 이동한다. calibration 14명과 confirmation 9명은 열지 않는다.

## 3. 의미·unit·시간창

- old/new는 metadata 숫자가 아니라 학습 embedded image와 recognition image의 pixel SHA-256 동일성으로 정의한다.
- 100 learning, 100 recognition, exact-old 50, exact-new 50, response 31–36을 장치 문으로 요구한다.
- 전체 session firing rate 0.05Hz 이상이고 recognition `[0.2,1.2]`초 창의 5% 이상 trial에서 spike가 있는 unit을 사용한다.
- 각 unit의 주 통계는 old와 new의 1초 firing-rate 평균 차이 절댓값이다.

## 4. null과 memory-selective 판정

subject별로 old/new label을 visual category 안에서 2,000회 섞는다. 같은 permutation을 그 subject의 모든 units에 적용해 unit 간 상관을 보존한다.

- unit별 two-sided permutation `p<0.05`이면 MS cell
- 각 permutation에서 unit별 95 percentile 문턱을 넘는 전체 cell 수를 계산해 cohort-wide null count를 만든다.

## 5. 양성대조 통과 조건

다음을 모두 만족해야 `KNOWN_MEMORY_SIGNAL_DETECTED`다.

1. MS cell 비율 7% 이상
2. 실제 MS cell 수가 cohort-wide null count 95 percentile보다 큼
3. 최소 3 subjects에서 MS cell이 1개 이상
4. 유효 units 250개 이상, 적격 subjects 8명 이상

통과하면 현재 표현기가 적어도 알려진 old/new 기억신호를 검출할 감도가 있다고 본다. 이때 P19·P16 관계복원 반복 미통과는 관계형 retrieval 가설에 선택적인 긴장으로 승격한다.

미통과하면 `MEMORY_APPARATUS_SENSITIVITY_NOT_ESTABLISHED`다. 이 경우 관계복원 음성을 생물학적 부재로 강화하지 않고 장치·표본 감도 한계로 유지한다.

## 6. 금지

- 양성대조 통과를 CE 관계복원 지지로 부르지 않는다.
- enrollment를 결과에 따라 늘리거나 줄이지 않는다. 적격 subject/unit 문만 사용한다.
- calibration·confirmation으로 부족한 양성대조를 구제하지 않는다.

공식 방법 근거:

- <https://www.nature.com/articles/s41597-020-0415-9>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC7055261/>
