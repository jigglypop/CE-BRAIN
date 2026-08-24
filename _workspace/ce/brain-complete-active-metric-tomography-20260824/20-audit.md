# BA-OBS-ID2 stable-snapshot audit

Status: COMPLETE

Gate: PASS

P0: none.  
P1: none.

## 1. 감사한 고정 입력

| lane | SHA-256 |
|---|---|
| `00-contract.md` | `2d4fa1a6010137a599984413cf1305479e776b7b5ea5a34a9d0a0b6aa1bbff0d` |
| `10-sources.md` | `52121090fcb85757a2a46778c4f6d59f63d54b5d50c18be09120795eeec70056` |
| `11-math.md` | `2ed549a01d11ad4c209f766a329085bbf1065fcc64aaf460029e46eb113ddbab` |
| `12-routes.md` | `94d42d9dc281d1a0f7d0051cac28d689312b449ef9f0620b475047f2f03684b3` |

감사 중 위 네 파일은 수정하지 않았다. 각 hash는 감사자가 독립적으로 재계산해
일치함을 확인했다.

## 2. 정리별 판정

- **T4 — PASS.** 열린 convex 실 Hilbert parameter domain에서 선분 적분과 uniform
  strong monotonicity가 stated global lower-Lipschitz bound를 준다. 전역 단사성과
  image 위 Lipschitz inverse만 주장하며 surjectivity를 주장하지 않는다.
- **T5 — PASS.** Real polarization이 가산 완전 basis query로 모든 mobility matrix
  coefficient를 복원한다. Complete ONB와 boundedness로 $M_1=M_2$, inversion으로
  $G_1=G_2$가 따른다.
- **C3 — PASS.** Identity-tail finite section은 uniformly coercive하고 $M_N\to M$,
  $G_N\to G$ strongly다. $M=2I$ 예시는 추가 decay 없는 operator-norm convergence를
  올바르게 반박한다.
- **C4 — PASS.** Symmetric raw block, $\eta_N$의 off-diagonal factor, Frobenius
  spectral clipping, weighted-HS tail, inverse perturbation constant가 모두 일관된다.

## 3. 합성 witness 판정

- Stable rank-one tail 식은 subtraction cancellation을 피하며 계약의 네 $N$ 값과
  일치한다.
- $w_N$은 unit vector이고 $w_N\perp v$다.
- $M^{\rm alt,N}$은 원래 $[1,1.5]$ mobility class에 남는다.
- 첫 $N^2$ query에는 exact하게 보이지 않고 held-out $w_N$ response에서 $0.10$만큼
  갈린다.

## 4. no-go 경계와 claim ceiling

감사자는 다음 경계가 논리적으로 양립함을 확인했다.

$$
\text{finite queries}
\Longrightarrow
\text{orthogonal blind tail remains},
$$

$$
\text{all countably complete exact queries}
\Longrightarrow
\{m_{ij}\}_{i,j\ge1}
\Longrightarrow M\Longrightarrow G.
$$

따라서 countably complete exact active regime에서는 arbitrary bounded strong metric의
유일 식별 no-go가 제거된다. 유한 passive 또는 유한 exact active data에 대해서는
full-recovery no-go가 그대로 남는다. 실제 뇌·의식·자아·해마·AGI 검증으로의 승격은
금지된다.

## 5. 감사 결론

`Gate: PASS`. 구현 lane은 동결된 계약의 rank-one exact/noisy/tail/adverse protocol만
재현할 수 있다. 계약식, $N$ menu, noise, threshold 또는 norm을 결과에 맞춰 바꾸면
이번 PASS는 무효다.
