# 04. 대칭 계량과 방향성 drift

## 4. 대칭 계량과 방향성 drift

연결에는 두 성질이 섞이기 쉽다. 대칭 계량은 어느 접방향으로 움직이는 데 드는 비용을 정하고, 방향성 연결은 실제 시간이 흐르는 방향을 정할 수 있다. 전자를 후자로 대체하면 비가역성 때문에 에너지 논리가 잘못된다.

**[정의]** 퍼텐셜 $\mathcal V$와 역사항 $R_x(h)$를 두고 동역학 후보를

$$
\dot x=-A_x^{-1}\nabla\mathcal V(x)+S_xx+R_x(h)
\tag{10}
$$

로 둔다. 첫 항은 (2)에서 정한 이동 비용에 따른 gradient 흐름이고, $S_xx$는 방향성 drift다. $S_x$가 skew-adjoint일 수 있으나, 그 사실 하나만으로 퍼텐셜에 일을 하지 않는다고 결론 내릴 수 없다.

**[정리: drift energy identity]** (10)의 해가 미분 가능하면

$$
\frac{d\mathcal V}{dt}
=-\langle\nabla\mathcal V,A_x^{-1}\nabla\mathcal V\rangle
+\langle\nabla\mathcal V,S_xx\rangle
+\langle\nabla\mathcal V,R_x(h)\rangle.
\tag{11}
$$

증명. 연쇄법칙으로 $d\mathcal V/dt=\langle\nabla\mathcal V,\dot x\rangle$를 쓰고 (10)을 대입하면 된다. 첫 항은 $A_x^{-1}$의 양의 정부호성 때문에 0 이하이지만, 나머지 두 항의 부호는 추가 조건 없이는 정해지지 않는다. □

**[산출: 반례]**

$$
S=\begin{pmatrix}0&-1\\1&0\end{pmatrix},
\quad x=(1,0),
\quad \mathcal V(x)=x_2
\tag{12}
$$

를 두면 $S^*=-S$이지만 $\langle\nabla\mathcal V,Sx\rangle=1$이다. 따라서 “skew이므로 zero-work”라는 부모 주장은 반례로 폐기되었다. **[공리: 모델 선택]** drift를 중립적 수송으로 쓰려면 별도로 $D\mathcal V(x)[S_xx]=0$을 가정해야 한다. 예컨대 $S_xx=J\nabla\mathcal V$와 $J^*=-J$이면 이 조건이 성립한다. 뇌 연결의 방향성은 이 중립성 공리를 만족할 수도 있고 아닐 수도 있으므로, 자료 없이 둘 중 하나를 선언하지 않는다.

