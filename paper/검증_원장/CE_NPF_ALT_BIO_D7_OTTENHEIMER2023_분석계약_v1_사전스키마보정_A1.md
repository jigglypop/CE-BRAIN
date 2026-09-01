# D7 Ottenheimer 분석계약 v1 사전 스키마보정 A1

## 보정 지위

- 기준 계약:
  `CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_동일세포앵커_학습표현_분석계약_v1.md`
- 결합 계약 ID:
  `ALT_BIO_D7_OTTENHEIMER_SAME_CELL_ANCHOR_PLASTICITY_v1+A1`
- 보정 시점: 원자료 `spks`의 값, 세포별 반응 서명, A/P/B endpoint를 계산하거나 보지
  않은 source/schema 단계.
- 보정 이유: `whosmat`, event-only 검사, 저자 `processROIs` 코드 대조에서 공개 파일의
  실제 저장 형상과 구현 세부가 기준 계약의 예상과 다름을 확인했다.
- 변경 범위: A1-1의 말단 frame 정렬, A1-2의 phase-cue fold 최소수, A1-3의 저자
  `processROIs` duplicate 규칙, A1-4의 one-third sensitivity 반올림·최소수다. cohort,
  동일세포 좌표 원천, signature, 공동주요 통계량, 방향, alpha, 판정표는 바꾸지 않는다.

이 보정문은 기준 계약과 함께 읽으며, 충돌하는 위 네 항목에 한해서만 A1이 우선한다.

## A1-1. 말단 neural frame 1–2개

24개 session 모두 `F,Fneu,spks`의 frame 길이는 서로 같았지만 `frameTimes`보다 1개 또는
2개 길었다.

\[
T_F=T_{Fneu}=T_{spks}=T,\qquad T-T_{frameTimes}\in\{1,2\}.
\]

따라서 기준 계약의 `len(frameTimes)=T`를 다음으로 교체한다.

1. 세 neural 배열의 원래 길이는 서로 정확히 같아야 한다.
2. `T-len(frameTimes)`는 정확히 1 또는 2여야 한다. 다른 값이면 `D7_SCHEMA_BLOCKED`다.
3. 저자 `processROIs`의 `F==0` 검사는 저자와 같이 원래 full-length `F`에 적용한다.
4. 시간 정렬이 필요한 `spks`만 마지막 여분 1–2 samples를 버려
   `spks[:,:len(frameTimes)]`로 고정한다. 앞쪽을 버리거나 interpolation하지 않는다.

이는 저자 MATLAB 코드가 `frameTimes` logical vector로 neural trace의 앞쪽 대응 sample을
선택하는 저장 형상과 일치하는 최소 결정이다. 어떤 cell activity 크기도 이 결정에 쓰지
않았다.

## A1-2. phase-cue fold 최소수

first/last 60 안의 cue별 trial 수 최솟값은 13이었다. 시간순 홀짝 분할 뒤 작은 fold는
6 trials가 된다. 기준 계약의 “각 `(phase,cue)` fold 최소 8”을 다음으로 교체한다.

\[
n_{m,s,p,c,f}\ge 6
\]

모든 24 session·2 phase·3 cue·2 fold가 이 조건을 만족해야 한다. 6 미만이면
`D7_SCHEMA_BLOCKED`다. first/last 60, 홀짝 규칙, 45차원 signature는 그대로다.

## A1-3. `processROIs` duplicate 규칙의 정확한 이식

기준 계약의 ROI 전처리 3번에 쓴 “다른 ROI와 0.5보다 많이 겹치면 제외”는 저자 코드의
정확한 규칙이 아니므로 폐기한다. `imagingAcquisition.m:1745-1754`의 실제 규칙은 초기
`iscell` 후보 안에서 각 ROI pixel 중 다른 후보의 pixel union에도 들어 있는 비율
`overlap_r`를 계산하고,

\[
remove_r=
\mathbf1\!\left[overlap_r=1\ \land\
r\le N-\frac{\#\{j:overlap_j=1\}}3\right]
\lor flag_r
\]

로 완전 중복 merge entry의 앞부분만 지우는 것이다. 여기서 `r=1,...,N`은 초기
`iscell` 후보 순서이고 `flag`는 edge 또는 full-length `F`의 정확한 0 검출이다. D7은
이 규칙을 그대로 이식하며 primary와 저자오타 sensitivity의 차이는 edge 식 하나뿐이다.

## A1-4. one-third sensitivity의 반올림과 최소수

first/last one-third sensitivity는 `k=floor(n_trial/3)`으로 고정해 첫 `k`와 마지막 `k`를
쓴다. 이 sensitivity에서 시간순 홀짝 fold의 최소수는 5다. 5 미만이면 primary를 막지
않고 해당 sensitivity를 `SENSITIVITY_SCHEMA_UNAVAILABLE`로 보고한다. 모든 sensitivity는
한 번에 하나의 축만 primary에서 바꾸며 factorial 조합을 만들지 않는다.

## 보정 전 확인한 비-endpoint 사실

- `T-len(frameTimes)`: 모든 session에서 1 또는 2.
- trial 수: 145–225; first/last 60은 모두 비중첩.
- `cue1,cue2,cue3`의 정확한 disjoint union이 각 session의 시간순 `cue`와 일치.
- first/last 60의 cue별 최소 trial 수: 13.
- median frame interval: 약 0.066948–0.067205 s; 15 Hz 기준의 5% 안.
- 모든 cue와 lick timestamp는 기록 범위 안.

이 확인은 event timestamp와 MAT header shape만 사용했으며 `spks` 값, 동일세포 등록 결과,
mouse statistic 또는 p-value는 열지 않았다.

## 다음 게이트

수정 결합 계약을 source lock에 함께 해시한다. 그 뒤 full `F/stat/iscell` 기반 등록
preflight가 mouse별 80%·15-cell gate를 통과해야 endpoint runner를 잠글 수 있다.
