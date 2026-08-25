# Mathematics lane

Status: COMPLETE

## N1. Affine-use audit

The predecessor derivative proof uses only: (i) a common graph-independent preimage $x$ for both graphs; and (ii) a uniform upper for the norm of the inverse derivative multiplying on the right. Constancy of that derivative is never used. Replacing $A_t^{-1}$ by $D\phi_t^{-1}(x')$ in each line preserves the slope bound and difference recurrence exactly.

Consequently the full predecessor theorem holds for a $C^1$ diffeomorphism satisfying (N2). A variation bound for $D\phi^{-1}$ first becomes necessary when comparing different output base points at a higher regularity level, not for the same-point C1 graph difference.

## N2. Sine fixture proof

$\phi_a'(x)=1+a\cos x\in[1-a,1+a]$. For $a<1$ the derivative is strictly positive. Moreover $|a\sin x|\le a$, so $\phi_a(x)\to\pm\infty$ as $x\to\pm\infty$. Strict monotonicity and properness give a global bijection, and the inverse function theorem gives a C1 inverse with derivative at most $(1-a)^{-1}$.

At $a=1$, $\phi_1'(\pi)=0$ and the inverse derivative cannot have a finite uniform bound. This is a boundary non-certificate, not evidence that every nonaffine base fails.

Verdict: the affine restriction is removed for triangular C1; the existing certificate applies with any certified $\mu$ from a C1 diffeomorphism.

