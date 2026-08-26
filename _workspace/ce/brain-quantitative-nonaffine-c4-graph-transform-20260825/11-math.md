# Mathematics lane

Status: COMPLETE

## N4.1 Exact common-inverse fourth chain

Let `S_h=B h+g compose (I,h)` and let the base inverse `psi` be independent of
the graph. Put

`||Dpsi||<=mu`, `||D2psi||<=nu`, `||D3psi||<=tau`, and
`||D4psi||<=upsilon`.

The order-four set partitions give

$$
\begin{aligned}
D^4(S_h\circ\psi)={}&D^4S_h[D\psi]^4
+6D^3S_h[D^2\psi,D\psi,D\psi]\\
&+3D^2S_h[D^2\psi,D^2\psi]
+4D^2S_h[D^3\psi,D\psi]+DS_hD^4\psi.
\end{aligned}
$$

With `r=1+kappa`, `s=q*kappa+L_x`, define

$$A_2=q\Lambda_2+K_2r^2,$$

$$A_3=q\Lambda_3+3K_2\Lambda_2r+K_3r^3,$$

$$
A_4=q\Lambda_4+4K_2\Lambda_3r+3K_2\Lambda_2^2
+6K_3\Lambda_2r^2+K_4r^4.
$$

Therefore

$$
\Lambda_{4,\mathrm{out}}^{\mathrm{na}}
=\mu^4A_4+6\mu^2\nu A_3+(3\nu^2+4\mu\tau)A_2+\upsilon s.
$$

The class gate is `Lambda4_out_na<=Lambda4`.

## N4.2 Exact five-layer recurrence

For value/derivative distances `(delta,d,e,f,j)`, slotwise telescoping gives

$$j'\le\beta_4j+c_{43}f+c_{42}e+c_{41}d+c_{40}\delta,$$

where `beta4=q*mu^4` and

$$c_{43}=4\mu^4K_2r+6\mu^2\nu q,$$

$$
c_{42}=\mu^4(6K_2\Lambda_2+6K_3r^2)
+18\mu^2\nu K_2r+(3\nu^2+4\mu\tau)q,
$$

$$
\begin{aligned}
c_{41}={}&\mu^4(4K_2\Lambda_3+12K_3\Lambda_2r+4K_4r^3)\\
&+18\mu^2\nu(K_2\Lambda_2+K_3r^2)
+2(3\nu^2+4\mu\tau)K_2r+\upsilon q,
\end{aligned}
$$

$$
\begin{aligned}
c_{40}={}&\mu^4(K_2\Lambda_4+4K_3\Lambda_3r+3K_3\Lambda_2^2
+6K_4\Lambda_2r^2+K_5r^4)\\
&+6\mu^2\nu(K_2\Lambda_3+3K_3\Lambda_2r+K_4r^3)\\
&+(3\nu^2+4\mu\tau)(K_2\Lambda_2+K_3r^2)
+\upsilon(H_y\kappa+H_x).
\end{aligned}
$$

Strict `q*mu^4<1`, together with all predecessor gates, makes the nonnegative
upper-triangular five-layer recurrence converge.

## N4.3 Scalar inverse and reductions

For `phi_a(x)=x+a sin(x)`, `0<=a<1`, put `gamma=1-a`. Direct implicit
differentiation gives the rigorous scalar bound

$$
\|D^4\phi_a^{-1}\|\le
\frac{a}{\gamma^5}+\frac{10a^2}{\gamma^6}
+\frac{15a^3}{\gamma^7}.
$$

At `a=1/10` this is `620000/1594323`. Setting
`nu=tau=upsilon=0` reduces the output and every recurrence coefficient
exactly to affine triangular C4. At `q*mu^4=1`, the invariant family
`h_c(x)=c*x*abs(x)^3` is C3 but not C4, so equality cannot be promoted.

The exact fixture has

`Lambda4_out=152045000/1594323`, margin `7387300/1594323`, and

`(beta4,c43,c42,c41,c40)=(5000/6561,25000/19683,2320000/531441,15940000/1594323,31673125/1594323)`.

No step selects the input dimension.
