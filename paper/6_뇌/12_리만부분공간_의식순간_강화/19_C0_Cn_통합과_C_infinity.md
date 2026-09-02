# 19. C0에서 임의의 유한 Cn까지 한 판본으로 묶기와 C∞ 조건

## C0에서 임의의 유한 Cn까지 한 판본으로 묶기

앞 절의 유한차수 미분 정리는 C0 불변볼·수축 정리를 별도 가정으로
남겨 두었다. 실제 한 모델을 인증하려면 두 층이 같은 정규화 상수를
사용한다는 확인이 더 필요하다. 새 어댑터는 이 접합부를 닫는다.

$$
q=b+g_y,\qquad
\alpha=\mu^{-1}-f_x-f_y\Lambda_1,\qquad
r_x=\frac{f_y}{\alpha},
$$

$$
s=q\Lambda_1+g_x,\qquad
q_0=q+\frac{s f_y}{\alpha}<1.
$$

임의차수 인증서는 같은 기저 차원, 같은 `alpha`, 같은 `Lambda_1`,
그리고 base/fiber raw envelope 양쪽에서 같은 `r_x`를 사용해야 한다.
첫 fiber 합성미분 상계도 C0 기울기 분자 `s`보다 작을 수 없다. 이 다섯
접점 가운데 하나라도 어긋나면 두 인증서를 한 판본으로 합치지 않는다.

접합이 통과하면 두 그래프 사이의 오차 벡터는 한 번에 갱신된다.

$$
\boxed{\Delta_0^{(m+1)}\le q_0\Delta_0^{(m)}}
$$

$$
\boxed{
\Delta_j^{(m+1)}
\le \sum_{k=0}^{j}c_{jk}\Delta_k^{(m)},\qquad 1\le j\le n
}
$$

모든 우변은 갱신 전의 동일한 오차 벡터를 사용한다. 따라서 기존
조건부 jet 반복처럼 `Delta_0`를 외부 입력으로 고정하지 않고, 값
성분의 실제 C0 수축이 모든 고차 층에 전달된다. 로컬 collar에서는
같은 derivative 인증서와 base 기준척도를, exact-matched 층에서는
같은 local 인증서와 fiber 기준척도를 다시 확인한다.

이 결론은 **조건부 정리**다. 선행 정리 내부의 부등식 margin은 엄격할
수 있지만 판본·척도·상수의 동일성은 등식 접점이므로 robust interior로
부르지 않는다. C2, C4, C6과 차원 1, 4, 5, 6, 100에서 검증됐고 차원은
입력값으로 보존될 뿐 선택되지 않았다. 따라서 이 완결은 신경계가 실제로
4--6차원이라는 경험 결과나 의식의 현상적 차원이 4--6이라는 동일시를
추가하지 않는다.

정식 기록은 `_workspace/ce/brain-full-coupled-arbitrary-order-graph-transform-20260825/40-final-report.md`를 따른다.

## analytic 가정 없이 C-infinity로 가는 정확한 조건

유한 Cn 정리를 아무리 높은 차수까지 계산해도 그것만으로 C-infinity를
말할 수는 없다. 그러나 무엇을 추가하면 승격되는지는 정확히 쓸 수 있다.
같은 변환의 인증서가 모든 자연수 차수에서 존재하고, 높은 차수 인증서를
낮은 차수로 제한한 값이 기존 인증서와 정확히 같으며, 모두 하나의 공통
궤도를 기술한다고 하자. 각 유한 차수의 오차 재귀를 행렬로 모으면

$$
\Delta^{(m+1)}\preceq A_n\Delta^{(m)},
$$

이고 `A_n`은 하삼각행렬이다. 대각성분은

$$
q_0,\beta_1,\ldots,\beta_n<1
$$

이므로 `A_n^m`은 0으로 가며 그 거듭제곱 급수는 각 성분에서 수렴한다.
이 결과를 연속한 두 반복의 차이에 적용하면 궤도는 모든 Cn seminorm에서
Cauchy가 된다. 공통 정의역 위 `C^infinity` 공간의 projective Fréchet
완비성과 각 유한 층의 연속성을 가정하면 하나의 매끄러운 극한 `h_*`가
존재하고 `T h_*=h_*`이다. C0 수축의 유일성 때문에 이 고정 그래프도
유일하다.

이 정리는 analytic보다 약한 가정으로 얻는 **조건부 비해석적 C-infinity
정리**다. 차수에 따른 공통 factorial·지수 majorant가 없으므로 analytic
또는 Gevrey 결론은 나오지 않는다.

반면 기계가 확인할 수 있는 유한 목록 C2부터 CN까지는 오직 호환 접두부다.
예를 들어 국소화한 `|x|^(N+1/2)`는 CN이지만 C(N+1)이 아니므로, 큰 유한
N을 무한 차수로 외삽할 수 없다. 따라서 새 장치는 접두부의 exact restriction,
하삼각행렬, 수렴 margin을 검증하면서도 항상 다음을 유지한다.

- `every_finite_order_hypothesis_verified=False`
- `projective_limit_completeness_hypothesis_verified=False`
- `common_orbit_hypothesis_verified=False`
- `cinfinity_claim_admitted=False`

즉 수학적 승격 조건은 닫혔지만 실제 neural map이 그 전칭 조건을 만족한다는
증거는 아직 없다. 정식 기록은
`_workspace/ce/brain-smooth-projective-graph-transform-20260826/40-final-report.md`를 따른다.

