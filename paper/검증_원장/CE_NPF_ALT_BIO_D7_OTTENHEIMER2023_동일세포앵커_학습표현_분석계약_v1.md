# CE-NPF 대체 생물자료 D7 동일세포 앵커·학습표현 분석계약 v1

## 목표 정렬

- 계약 ID: `ALT_BIO_D7_OTTENHEIMER_SAME_CELL_ANCHOR_PLASTICITY_v1`
- 최종 목표: 사용자의 강한 가설 2를 생물학적으로 정직한
  `stable cell-specific anchor + context/learning-dependent expression`으로 재구성할 수
  있는지 판별한다.
- 이번 하위 목표: 성체 prelimbic cortex의 동일한 해부학적 세포가 날짜를 넘어 상대적
  cue 반응 서명을 보존하는 동시에, 최초 학습 세션에는 이후 세션의 일반 시간 드리프트를
  넘는 재현 가능한 기능 변화가 있는지 공동 판정한다.
- 필요한 이유: 안정성과 가소성을 서로 다른 세포 표본이나 서로 다른 논문에서 골라 붙이지
  않고 같은 8 mice·같은 추적세포 안에서 함께 시험하기 위해서다.
- 목표 명확성: 명확하다. 이 D7은 출생·청소년기 시점, 시냅스 가중치, 전도속도, 지연,
  리만계량을 측정하지 않는 component test다.
- 계보 분리: `AIND D1`, `ALT_BIO D1-D6`의 번호나 결과를 D7 통과로 대신하지 않는다.
- 다음 게이트: source/schema/registration이 모두 통과하면 아래 고정 endpoint를 한 번만
  실행한다. 실패하면 생물 결과를 내지 않고 해당 `BLOCKED` 상태로 정지한다.

## 입력 잠금

- 원자료: Figshare file `37918065`, DOI `10.6084/m9.figshare.21365598.v1`
- 로컬 archive SHA-256:
  `47ffe1933713f53be720d85023f75c6f487faa8ee39a46ad0af63e3801bc4bd9`
- 저자 코드: Git tag `v2.0`, commit `d06d9c8d1674a791327b3357d2dd683d9dd0e5e0`
- 저자 코드 배포 ZIP SHA-256:
  `594ec93c6d1665dc6e00653e4e6afd74188fd5c96d31efda0dd5148711e35221`
- mice 순서: `PL01, PL02, PL03, PL08, PL10, PL11, PL15, PL16`
- sessions 순서: `o1d1, o1d2, o1d3`, 각각 `A1, A2, A3`
- 추적 열 수: `55,55,33,20,40,64,39,65`, 합계 `371`
- 독립 추론 단위: mouse `n=8`; cell과 trial은 반복측정이지 표본수를 늘리지 않는다.

## endpoint 전 hard gates

다음 검사를 순서대로 모두 통과해야 한다.

1. archive 크기·MD5·SHA-256·225-entry manifest·모든 ZIP CRC가 잠금값과 일치한다.
2. 8 mice 각각에 세 session의 `Fall.mat`, `<mouse><session>events.mat`,
   `ROIs/Masks/<mouse><session>ROImasks.npy`가 정확히 하나씩 있다.
3. `Fall.mat`에는 `spks,F,Fneu,stat,iscell,ops`가 있고, `spks,F,Fneu`는 같은
   `(n_roi,T)`이며 `iscell.shape[0]=n_roi`, `len(stat)=n_roi`이다. 값은 구조적으로
   유효하고 `spks`와 fluorescence의 frame 축은 유한하다.
4. event 파일에는 `frameTimes,cue,cue1,cue2,cue3,lick`가 있다.
   `len(frameTimes)=T`, frame time은 유한하고 엄격히 증가하며, cue와 lick는 기록 범위
   안에 있다.
5. `cue1,cue2,cue3`는 각각 중복이 없고 서로 겹치지 않으며, 원래 순서를 보존한 정확한
   multiset union이 `cue`다. 반올림 timestamp join을 쓰지 않는다.
6. 각 session에는 최소 120 trials가 있고 first 60과 last 60이 겹치지 않는다. 각
   `(phase,cue)`의 시간순 홀짝 fold에는 최소 8 trials가 있다.
7. 각 mouse의 세 mask가 모두 `(2,N_m)`이고 열 수·열 순서가 일치한다. 합계는 정확히
   371이다.
8. `processROIs` 수정판으로 남은 ROI의 `stat.med=(y,x)`에 각 수동 `(x,y)`를 매칭한다.
   최근접 거리는 유일해야 하고, `d_1 <= 5 px`, `d_2-d_1 >= 2 px`, 모든 target은
   1:1이어야 한다. 충돌한 좌표를 차선 ROI로 강제 재배정하지 않고 그 triplet을 제외한다.
9. 세 날짜 중 한 날짜라도 실패한 열은 세 날짜 모두 제외한다. mouse마다 원래 열의 80%
   이상이면서 최소 15 triplets가 남아야 하고 8 mice 모두 통과해야 한다.
10. endpoint 계산에 들어가는 모든 vector와 mouse statistic이 유한해야 한다. 실패 시
    결측 mouse를 버리지 않고 `D7_NUMERICAL_BLOCKED`로 정지한다.

실패 상태는 각각 `D7_SOURCE_BLOCKED`, `D7_SCHEMA_BLOCKED`,
`D7_REGISTRATION_SCHEMA_BLOCKED`, `D7_NUMERICAL_BLOCKED`다. 이것들은 가설의 음성
결과가 아니다.

## ROI 전처리와 등록

원래 `iscell[:,0]`이 참인 ROI 가운데 다음을 제외한다.

1. ROI pixel이 네 FOV 경계 `xpix=0,511` 또는 `ypix=0,511`에 닿음.
2. 해당 ROI의 `F` trace에 정확한 0이 하나라도 있음.
3. 다른 후보 ROI의 pixel union과 겹친 비율이 0.5보다 큼.

세 번째 규칙은 저자 `processROIs`의 나머지 본문과 같은 판본으로 구현한다. primary는
우측 x 경계 오타만 수정한다. 저자 원문 오타 판본은 sensitivity에서만 쓴다.

동일세포 키는 활동과 독립적인 `(mouse,k)`다. 등록 이후 얻은 session별 raw ROI index를
`j_{mks}`라 쓰며, 활동 유사성으로 `j`를 다시 고르지 않는다.

## 누수 없는 cue 반응 서명

frame rate 기준값은 15 Hz다. 실제 `frameTimes`의 중앙 간격이 `1/15 s`에서 5% 넘게
벗어나면 schema 실패다. deconvolved activity `spks`에 저자와 같은 300 ms causal
half-normal을 적용한다. `h=0,...,15`에 대해

\[
w_h=\exp\!\left[-\frac12\left(\frac{h/15}{0.3}\right)^2\right],
\qquad
x_{isk}=
\frac{\sum_{h=0}^{\min(15,k)}w_h\,spks_{is,k-h}}
{\sum_{h=0}^{\min(15,k)}w_h}.
\]

cue onset `u_r`에 대해 같은 trial의 baseline을 빼고 0.1 s bin 15개를 만든다.

\[
r_{isrcb}=
\operatorname{mean}_{t_k-u_r\in[0.1b,0.1(b+1))}x_{isk}
-\operatorname{mean}_{t_k-u_r\in[-1,0)}x_{isk},
\quad c\in\{1,2,3\},\ b=0,\ldots,14.
\]

빈 bin 또는 baseline frame이 있으면 그 session은 schema 실패다. 세 cue의 공통 gain을
제거한다. phase `p`, fold `f`의 trial 평균을 `s`라 하면

\[
q_{ispfcb}=s_{ispfcb}-\frac13\sum_{c'=1}^3s_{ispfc'b}.
\]

반응성, A3 선호도, GLM category 또는 endpoint 크기로 세포를 사후 선택하지 않는다.

## 공동주요 A: 동일세포 앵커

각 날짜의 모든 trial을 cue별 평균해 45차원 `q_{is}`를 만들고 mouse-session population
mean을 뺀다.

\[
u_{is}=q_{is}-\frac1{N_m}\sum_{j=1}^{N_m}q_{js}.
\]

날짜쌍 `(A1,A2),(A2,A3),(A1,A3)`에서 cosine similarity를

\[
\rho_{ij}^{st}=\frac{u_{is}^{\mathsf T}u_{jt}}
{\lVert u_{is}\rVert\lVert u_{jt}\rVert}
\]

로 계산한다. 0 norm이 하나라도 있으면 numerical blocked다. source cell `i`의 진짜
target `j=i`가 같은 mouse의 모든 target 중 차지하는 normalized ascending midrank를

\[
R_{i,s\to t}=\frac{\operatorname{midrank}
(\rho_{ii}^{st};\{\rho_{ij}^{st}\}_{j=1}^{N_m})-1}{N_m-1}\in[0,1]
\]

로 둔다. 이는 sampling 없는 완전한 within-mouse mismatch null이다. 방향을 대칭화해

\[
a_i^{st}=\frac{R_{i,s\to t}+R_{i,t\to s}}2-\frac12,
\qquad
A_m=\operatorname{median}_i\frac{a_i^{12}+a_i^{23}+a_i^{13}}3
\]

를 얻는다.

필수 A 조건은 모두 다음과 같다.

- `mean_m(A_m)>0`;
- 모든 true same-cell/date-pair cosine의 중앙값 `>0`;
- 최소 `6/8` mice에서 `A_m>0`;
- 8 mouse 부호를 전수 열거한 one-sided exact sign-flip `p_A<=0.05`.

## 공동주요 P: 최초 학습세션의 재현 가능한 기능 변화

각 session의 첫 60 trials를 early, 마지막 60을 late로 고정한다. 각 `(phase,cue)` 안에서
시간순 홀수·짝수 trial을 독립 fold `f=0,1`로 둔다. 45차원 변화는

\[
\delta_{isf}=q_{is,L,f}-q_{is,E,f}
\]

이고, 두 fold에서 변화 방향이 재현되는지 bounded cosine으로 측정한다.

\[
c_{is}=
\begin{cases}
\dfrac{\delta_{is0}^{\mathsf T}\delta_{is1}}
{\lVert\delta_{is0}\rVert\lVert\delta_{is1}\rVert},&
\lVert\delta_{is0}\rVert\lVert\delta_{is1}\rVert>0,\\[6pt]
0,&\text{두 변화가 모두 정확히 0일 때},
\end{cases}
\qquad
C_{ms}=\frac1{N_m}\sum_i c_{is}.
\]

한 fold만 0 norm이면 numerical blocked다. 두 필수 plastic contrast는

\[
P_m^{(0)}=C_{m,A1},\qquad
P_m^{(specific)}=C_{m,A1}-\frac{C_{m,A2}+C_{m,A3}}2.
\]

각 contrast마다 모두 다음을 요구한다.

- mouse grand mean `>0`;
- 최소 `6/8` mouse 값 `>0`;
- 8 mouse 부호의 one-sided exhaustive sign-flip `p<=0.05`.

`P^(0)`는 A1 early-to-late 변화의 fold 재현성, `P^(specific)`은 그 재현성이 A2/A3의
일반적인 session-time drift보다 큰지를 시험한다.

## 행동 해석 게이트

trial `r`의 cue 전후 lick contrast는 경계점을 제외하고

\[
L_r=N_{lick}(0<t-u_r<2.5)-N_{lick}(-2.5<t-u_r<0)
\]

다. 저자 코드의 cue 정의에 따라 `cue1=CS+`, `cue3=CS-`로 고정한다. A1의 first/last 60
trial에서

\[
B_m=
\left[(\bar L_{CS+}-\bar L_{CS-})_{late}
-(\bar L_{CS+}-\bar L_{CS-})_{early}\right]_{A1}
\]

를 계산한다. `mean(B)>0`이고 one-sided exact sign-flip `p_B<=0.05`여야 신경 변화에
`learning-associated`라는 말을 허용한다. 실패하면 신경 P가 통과해도
`WITHIN_SESSION_FUNCTIONAL_CHANGE_ONLY`로 제한한다.

## exact sign-flip

어떤 mouse statistic `z_m`, `n=8`에도 동일하게

\[
T_{obs}=\frac18\sum_m z_m,
\qquad
p_+=2^{-8}\sum_{s\in\{-1,+1\}^8}
\mathbf1\!\left[\frac18\sum_ms_mz_m\ge T_{obs}\right]
\]

를 쓴다. 0은 제거하지 않고 `+0/-0` 배정도 각각 전수 경우에 포함한다. 비교는 수치
허용오차 없이 `>=`다. A, P0, Pspecific은 모두 필요한 conjunction/IUT 구성요소이므로
각각 `alpha=0.05`를 통과시킬 때 별도 Bonferroni를 적용하지 않는다. 행동 B는 해석
자격 게이트다.

## 고정 sensitivity

Primary를 구제하거나 판정을 재조정하지 않고 다음을 모두 기술한다.

1. 수정된 edge QC 대 저자 원문 오타 판본.
2. 전체 non-self rank 대 target 날짜 좌표상 가장 가까운 non-self 5개만 사용한
   local-spatial rank. local 결과의 mouse mean advantage도 양수여야 한다.
3. causal smoothing 대 raw unsmoothed `spks`.
4. cue window `[0,1.5)` 대 `[0,2.5)`.
5. first/last 60 대 first/last one-third.
6. population-mean residualization 유/무.
7. 날짜 전체 세 쌍 대 adjacent pairs `(A1,A2),(A2,A3)`만.

저자 원문 등록판 또는 local-spatial sensitivity에서 primary A의 방향이 뒤집히면 양성
주장을 `D7_REGISTRATION_OR_LOCAL_TUNING_SENSITIVE`로 강등한다. 다른 sensitivity의
실패는 강건성 한계로 보고하되 primary를 바꾸지 않는다.

## 고정 판정표

- `D7_STABLE_ANCHOR_AND_LEARNING_PLASTIC_EXPRESSION_SUPPORTED`:
  모든 hard gate, A, P0, Pspecific, B 통과; 등록/local sensitivity도 같은 방향.
- `D7_STABLE_ANCHOR_AND_WITHIN_SESSION_CHANGE_SUPPORTED`:
  A, P0, Pspecific은 통과하지만 B가 실패; `learning-associated` 표현 금지.
- `D7_REGISTRATION_OR_LOCAL_TUNING_SENSITIVE`:
  primary 공동주요는 통과하지만 지정 등록/local sensitivity 방향이 뒤집힘.
- `D7_COMPONENT_CONJUNCTION_NOT_SUPPORTED`:
  hard gate는 통과했지만 A, P0, Pspecific 중 하나 이상 실패.
- 앞서 정의한 `BLOCKED` 상태: endpoint 전에 입력·구조·수치 게이트 실패.

Primary 실패를 sensitivity, 세포 pooling, 반응세포 사후선택, 다른 p-value 또는 다른
window로 구제하지 않는다. 첫 endpoint 실행 뒤에는 같은 계약 이름으로 재실행·retune하지
않는다.

## 허용되는 생물학적 결론의 상한

모든 게이트가 통과해도 허용되는 결론은 다음뿐이다.

> 성체 PL에서 동일한 해부학적 세포는 다른 세포보다 자기 cue-locked 반응 서명을 더 잘
> 유지하는 한편, 행동 습득이 일어난 첫 세션에는 이후 세션의 일반 시간 드리프트를 넘는
> 재현 가능한 기능 변화도 보였다. 이는 stable cell-specific anchor와
> training-associated plastic expression의 공존을 지지한다.

다음은 이 자료로 결론내리지 않는다.

- 학습이 신경 변화를 인과적으로 만들었다.
- 뉴런이 출생 시 의미를 갖거나 청소년기에 그 의미가 고정됐다.
- cue 반응 서명이 세포의 내재적 의미다.
- 시냅스 가중치 `W`, 전도속도 `v`, 지연 `tau`, 리만계량 `g`가 변했다.
- 수동 등록이 독립적·맹검으로 검증됐다.

따라서 D7 양성도 재구성 가설 2의 component-level support이며,
`Delta(A,W,tau)->Delta g->Delta behavior` 사슬이나 전체 CE-NPF 생물학을 닫지 않는다.

