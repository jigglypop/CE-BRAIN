# 단일 SPD 계량을 사용하는 관측 예측부

## 1. 예측을 계량의 최소화 문제로 둔다

최신 작업판은 여섯 관측 영역과 한 기준 좌표에서 하나의 SPD 텐서 $G$를 저장한다. 입력 $x$는 양의 대조군 평균, 출력 $y$는 처리군 평균이다. $\phi(x)=x^{0.625}$는 요소별 입력 변환이며, 지수는 개발 설정이지 생물 상수가 아니다.

$$
\Phi_G(y;x)=\frac12\begin{bmatrix}y\\1\end{bmatrix}^TG\begin{bmatrix}y\\1\end{bmatrix}-\phi(x)^Ty,
\qquad G=G^T\succ0.
$$

[정리: 원모형의 최소화] $G$가 SPD이면 $G_{yy}$도 SPD이며 위 에너지는 $y$에 대해 엄격히 볼록하다. 따라서 유일한 최소점은

$$
\widehat y=G_{yy}^{-1}(\phi(x)-G_{yr})
$$

이다. 증명. 미분하면 $G_{yy}y+G_{yr}-\phi(x)=0$이고 Hessian은 $G_{yy}\succ0$다. 선형계를 풀면 위 식을 얻는다. □

이 증명은 예측 계산의 정확성이다. 실제 뇌가 이 에너지를 최소화한다는 생물학적 증명이 아니다.

## 2. 기초 이동도와 공통 결합

기초 이동도 $L$은 유형별 대각 성분과 공통 저차수 성분으로 보정한다.

$$
L=\operatorname{diag}(d_{s(c)})+\rho vv^T\succ0,\qquad
v_c={\sqrt{\overline{\phi(x_c)}_{train}}\over\sqrt{\sum_j\overline{\phi(x_j)}_{train}}}.
$$

$d_{s(c)}$는 유형별 계수, $\rho$는 공통 결합이다. $v$는 해당 훈련 대조군에서만 계산한다. 이 정확한 공식이 실제 APL의 해부학에서 유도됐다는 주장은 하지 않는다.

보정 중의 기준 결합 $b$와 $L$을 다음 텐서로 묶는다.

$$
G=\begin{bmatrix}L^{-1}&-L^{-1}b\\-b^TL^{-1}&1+b^TL^{-1}b\end{bmatrix}.
$$

Schur complement가 1이므로 $L\succ0$이면 $G\succ0$다. 이 결합은 affine 응답과 대수적으로 연결된다. 계량으로 저장했다는 사실만으로 생물학적 기전이 식별되는 것은 아니다.

## 3. 같은 유형의 국소 차이를 제한한다

임시 $b$에 $\lambda_b n[(b_\alpha-b_\beta)^2+(b_{\alpha'}-b_{\beta'})^2]$를 추가한다. $n$은 훈련 조건 수이며 $\lambda_b=0.06$이다. 두 가지가 반드시 같다는 등식이 아니라 과도한 차이를 완화하는 추정 제약이다. 이 항은 최종 추론 파일의 별도 기억 상태로 저장되지 않는다.

최종 설정은 입력 지수 0.625, 측정오차 가중 지수 2.5, 공통 결합 정규화 3.0, SPD 보정 스텝 0.2, 기초 이동도 하한 0.025다. 모두 같은 개발 자료에서 선택한 계산 설정이며 완전한 Gaussian 우도나 생리 상수가 아니다.

## 4. SPD 공간의 보정

전체 훈련 계량 $G$와 훈련조건 하나를 제외한 계량 $G_{-j}$로

$$
T={1\over n}\sum_j\log(G^{-1/2}G_{-j}G^{-1/2}),\qquad
G_{new}=G^{1/2}\exp(-0.2T)G^{1/2}
$$

를 계산한다. 이 연산은 SPD를 유지하지만 불편추정량이나 생물 학습법이라는 정리가 아니다. 고정된 힘을 함께 변환한 좌표 공변성 검사와 전처리 전체의 불변성을 혼용하지 않는다.

저장 상태는 `metric` 하나이고 고정 설정은 `config`에 남는다. 7×7 대칭 텐서의 고유 원소는 28개다. 기초 적합의 11계수 부분족에서 보정 후에도 벗어나지 않는다고 보장하지 않는다.

원문: [첫 개선](../../research/ce_brain_publication_20260919/reports/CE_BRAIN_RIEMANN_IMPROVEMENT_20260919.md), [최신 수정](../../research/ce_brain_publication_20260919/reports/CE_BRAIN_RIEMANN_REFINEMENT_20260919.md).
