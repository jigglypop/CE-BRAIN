# 17. 유한차수를 넘어 analytic·C∞·Gevrey로 가는 충분조건

## 유한차수를 넘어 analytic·(C^\infty)·Gevrey로 가는 충분조건

각 유한 (n)에서 certificate가 통과했다는 사실만으로 analytic을
주장할 수는 없다. 이를 막으면서 실제 승격이 가능한 별도 경로를
고정한다. 유한차원 기저공간을 복소화하고

$$
F(x)=Ax+N(x),\qquad \|A^{-1}\|\le\alpha^{-1}
$$

로 둔다. (A)는 가역이고, 공통 복소 입력 ball에서 모든 graph에 대해

$$
\|D^jN(0)\|\le A_FB_F^j j!\quad(j\ge2)
$$

가 균일하게 성립한다고 가정한다. (x_F=B_Fr<1)이면 Taylor 급수를
직접 합하여

$$
\boxed{
N_r\le A_F\frac{x_F^2}{1-x_F}
},\qquad
\boxed{
\Theta_r\le A_FB_F\left(\frac1{(1-x_F)^2}-1\right)
}
$$

을 얻는다. (Theta_r<\alpha)이면

$$
Q_y(x)=A^{-1}(y-N(x))
$$

는 수축계수 (Theta_r/\alpha<1)인 사상이다. 따라서

$$
\boxed{
\rho_{\rm avail}=\alpha r-N_r>0
}
$$

이고 (0<\rho<\rho_{\rm avail})인 모든 출력 복소 ball에서 (F^{-1})가
유일하고 holomorphic이다. 이 증명은 단순히 “Jacobian이 0이 아니다”가
아니라, ball 자기포함과 수축을 동시에 수치로 검사한다.

fiber 쪽도

$$
\|Y(0)\|\le Y_0,\qquad
\|D^jY(0)\|\le A_YB_Y^j j!\quad(j\ge1),\qquad B_Yr<1
$$

을 가정하면

$$
\boxed{
M_T\le Y_0+A_Y\frac{B_Yr}{1-B_Yr}
}
$$

이다. 그러므로 (T=Y\circ F^{-1})는 요청한 공통 출력 ball에서
holomorphic이고 sup이 (M_T) 이하이다. analytic graph class의 sup
반경 (M_G)가 (M_T\le M_G)를 만족하고, 바로 그 복소 함수공간에서
graph transform의 C0 수축계수가 (q_{\mathbb C}<1)이면 Banach 반복은
공통 ball에서 균일수렴한다. holomorphic 함수의 균일극한이므로 고정점
graph도 analytic이다.

전 Fréchet (n)-선형 노름에서는 방향 Cauchy 상계만 그대로 쓰면
polarization 비용을 놓칠 수 있다. 안전한 상계는

$$
\|D^nT(0)\|
\le\frac{n^nM_T}{\rho^n}
\le
\boxed{M_T\left(\frac3\rho\right)^n n!}
$$

이다. 마지막 부등식은 (n^n\le3^nn!)을 사용한다. 따라서 이 branch는
analytic일 뿐 아니라 (C^\infty)이고, 모든 실수 (s\ge1)에 대해

$$
\|D^nT(0)\|
\le M_T(3/\rho)^n(n!)^s
$$

이므로 Gevrey-(s)에도 속한다.

고정 exact fixture에서는

$$
N_r=\frac1{120},\qquad
\Theta_r=\frac7{90},\qquad
\rho_{\rm avail}=\frac{29}{120},\qquad
\rho=\frac15,\qquad
M_T=\frac1{30}
$$

이고 안전한 factorial rate는 (3/\rho=15)다. 모든 엄격 margin이
양수다.

반대로 (x>0)에서 (e^{-1/x^2}), (x\le0)에서 0인 함수는
(C^\infty)이고 원점의 모든 미분이 0이지만 원점에서 analytic이
아니다. 따라서 임의의 유한 jet tuple은 물론, 한 점의 무한 Taylor
jet조차 위의 **공통 복소 반경과 균일 majorant**를 대신하지 못한다.

이번 결과로 무한 정칙성의 조건부 수학 경로는 생겼지만, 실제 neural
map이 복소 확장·기하급수 majorant·복소 C0 수축을 만족한다는 증거는
아직 없다. 이는 인간 의식의 존재나 4--6차원 식별을 뜻하지 않는다.

analytic 충분조건 확장은 `_workspace/ce/brain-analytic-implicit-graph-transform-20260825/40-final-report.md`를 따른다.

