# BA-OBS-ID1 source lane

Status: COMPLETE

## 판정

이번 run의 T3, C2, W1은 외부 문헌의 정리를 이름만 바꿔 인용하지 않고 `11-math.md`에서
직접 증명한다. 아래 문헌은 structural identifiability, controlled observability, metric
gradient flow라는 문제의 계보와 용어만 뒷받침한다. 뇌·의식·자아·AGI에 대한 경험적
출처는 이번 계약의 정의역 밖이므로 사용하지 않았다.

| 출처 | 이 run에서 지지하는 범위 | 지지하지 않는 범위 |
|---|---|---|
| Bellman, R. & Åström, K. J. (1970), “On Structural Identifiability,” *Mathematical Biosciences* 7(3–4), 329–339, [doi:10.1016/0025-5564(70)90132-X](https://doi.org/10.1016/0025-5564(70)90132-X) | 알려진 입력·출력으로 유한 매개변수 모델의 구조 식별성을 묻는 고전적 문제 설정 | 본 run의 weighted $L^2$ Gramian 정리, infinite spectator witness, 뇌 해석 |
| Hermann, R. & Krener, A. J. (1977), “Nonlinear Controllability and Observability,” *IEEE Transactions on Automatic Control* 22(5), 728–740, [doi:10.1109/TAC.1977.1101601](https://doi.org/10.1109/TAC.1977.1101601), [author PDF](https://www.math.ucdavis.edu/~krener/1-25/10.IEEETAC77.pdf) | 알려진 제어·출력과 동역학을 함께 써서 관측가능성을 판정하는 기하학적 배경 | metric parameter에 대한 T3의 직접 증명이나 전역 식별성 |
| Ambrosio, L., Gigli, N. & Savaré, G. (2008), *Gradient Flows in Metric Spaces and in the Space of Probability Measures*, 2nd ed., Birkhäuser, [doi:10.1007/978-3-7643-8722-8](https://doi.org/10.1007/978-3-7643-8722-8) | metric-dependent gradient flow라는 표준 수학 배경 | 계약의 특정 $G_\theta$, potential, 식별성 결론 |
| Absil, P.-A., Mahony, R. & Sepulchre, R. (2009), *Optimization Algorithms on Matrix Manifolds*, Princeton University Press, [publisher record](https://press.princeton.edu/books/hardcover/9780691132983/optimization-algorithms-on-matrix-manifolds) | Riemannian metric이 differential을 gradient vector로 바꾸는 convention | $\ell^2$ spectator block, synthetic 수치, 뇌·의식 주장 |

## 출처-주장 분리

| 주장 | 지위 | 근거 |
|---|---|---|
| structural identifiability는 알려진 입력-출력에서 내부 매개변수의 유일성을 묻는다. | 문헌 배경 | Bellman–Åström (1970) |
| 개입을 포함한 동역학적 output은 수동 점별 map보다 더 많은 관측가능성 정보를 가질 수 있다. | 문헌 배경 | Hermann–Krener (1977) |
| $q'=-G^{-1}\nabla V$는 metric $G$에 대한 gradient-flow convention이다. | 문헌 배경 + 계약 정의 | Ambrosio–Gigli–Savaré (2008); Absil–Mahony–Sepulchre (2009) |
| $\mathcal I\succ0$이면 계약의 $\Phi$가 국소 단사다. | 이 run의 조건부 정리 | `11-math.md`의 직접 증명 |
| $G_\theta$ witness에서 $\theta=-\log(y''(0+)/u_0)$다. | 이 run의 구성적 정리 | `11-math.md`의 직접 계산 |
| 실제 brain metric, consciousness 또는 AGI가 식별되었다. | 주장 금지 | 이번 source set에는 그런 증거가 없음 |

모든 링크의 접근일은 2026-08-24다. DOI와 출판사·저자 제공 record를 우선했으며
2차 해설을 근거로 사용하지 않았다.
