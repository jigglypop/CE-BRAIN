# BA-OBS-ID4 mathematics lane — frozen observed-reciprocity test

Status: COMPLETE

## Formal closure audit v5 (pre-development, signal-blind)

Status: PASS_AFTER_EXPLICIT_MEASUREMENT_AXIOMS

`00-contract.md` section 6a closes the previously non-unique CAR75 rounding/tie,
baseline scale, trial population, Spearman population, evocation ratio, and
restricted-null child-stream choices. These are classified as measurement/numeric
axioms and definitions, not theorems. The sufficient streaming state is
`Y[T,C,164]`, baseline SSE `S[T,C]`, bipolar cross-products `G[T,Q]`, and the
baseline-only CAR mask; raw trial tiles are not a retained result.

## Concrete findings first

1. **No P0 formula or dimensional contradiction was found in the frozen endpoint.**  The recorded voltage is normalized by a same-contact/site/half baseline SD before every downstream comparison; hence $Z$, $A$, $d$, $u$, $v$, $R$, $p_R$, $\phi$, and $\Delta$ are dimensionless.  The only logarithm has the admissible dimensionless argument $A+10^{-12}$.
2. **The predecessor's fatal raw-ratio counterexample remains real and is addressed only by the restricted null.**  Under exact reciprocal latent response and unequal directional precision, the small-noise raw ratio can reach $\sqrt2>1.25$; therefore $R>1.25$ alone is not a P1 refutation.  The specified source/half-shared residual resampling, with reciprocal location imposed but directional residuals retained, is the required conditional calibration.
3. **The endpoint is a patient-level fixed-label rule, not five pooled edge tests or a population $p$-value.**  Each confirmation subject gets one $(\Delta_i,\phi_i^{\rm mean},\phi_i^{\rm bip})$ label.  The final three-subject pattern is fixed in the contract; no asymptotic or edge-iid inference follows.
4. **P1 remains an open, target-aware empirical proxy, not a theorem about a neural metric.**  Peak magnitude, absolute value, baseline division, receiver aggregation, $C_{\rm ref}$, $R_c$, artifacts, and the unknown causal response all intervene between any putative self-adjoint object and $A$.  A pass neither identifies a metric nor proves reciprocity of $H$; a prescribed composite refutation only rejects this aligned observed-magnitude proxy.

## Definitions recovered from the contract

For a retained receiver contact $c$, stimulating site $s$, and even/odd trial half $h\in\{A,B\}$,

$$
Z_{c\leftarrow s}^{(h)}=
\max_{10\,\mathrm{ms}\le t\le50\,\mathrm{ms}}
\frac{|\overline V_{c\leftarrow s}^{(h)}(t)|}{\sigma_{csh}}.
$$

`mean` averages the two receiver-contact $Z$ values; `bip` differences the two voltage waveforms first and then applies the same normalization/max operation.  Thus both define a nonnegative finite early-magnitude $A_{r\leftarrow s}^{(h,m)}$, provided the decoder rejects nonfinite or zero scales as required.

For each retained unordered reciprocal pair $\{r,s\}$,

$$
d(x,y)=\frac{|x-y|}{x+y+10^{-12}},
$$

$$
u_{rs}=\frac12\left[d(A_{r\leftarrow s}^{A},A_{r\leftarrow s}^{B})+
d(A_{s\leftarrow r}^{A},A_{s\leftarrow r}^{B})\right],
$$

$$
v_{rs}=\frac12\left[d(A_{r\leftarrow s}^{A},A_{s\leftarrow r}^{B})+
d(A_{r\leftarrow s}^{B},A_{s\leftarrow r}^{A})\right],
$$

and, within patient $i$ and readout $m$,

$$
R_i^{(m)}=\frac{\operatorname{median}_{\{r,s\}}v_{rs}+10^{-12}}
{\operatorname{median}_{\{r,s\}}u_{rs}+10^{-12}},\qquad
\Delta_i=\log R_i^{(\rm mean)}-\log R_i^{(\rm bip)}.
$$

The $10^{-12}$ terms make $d$ and $R$ defined at a zero empirical disagreement.  They are numerical regularizers rather than physical scales.  Because $A\ge0$, $d\in[0,1)$; no hidden sign convention enters $u$ or $v$.

## Independent derivation and spot checks

Let equal reciprocal latent magnitudes be $A>0$, with directional half-estimator noise scales $\sigma_1,\sigma_2$.  To first order, same-direction half differences have scales $\sqrt2\sigma_1$ and $\sqrt2\sigma_2$, whereas cross-direction differences have scale $\sqrt{\sigma_1^2+\sigma_2^2}$.  With common denominator $2A$,

$$
\frac{\mathbb E[v]}{\mathbb E[u]}
\approx\frac{\sqrt2\sqrt{\sigma_1^2+\sigma_2^2}}{\sigma_1+\sigma_2}\in[1,\sqrt2].
$$

The upper limit is approached as one directional scale dominates.  Numerical checks give $\sqrt2=1.41421356$, already above the raw 1.25 tolerance; for $(\sigma_1,\sigma_2)=(1,4)$ the expression is $1.16619038$.  This validates the need for, but does not itself validate, the restricted-null calibration.

The conditional null is correctly shaped for that purpose if implemented exactly: resample trial indices jointly for all receivers sharing a source/site and half; recompute baseline, SD, maximum, and readout on every draw; form centered log residuals $e_e^{(h,m,b)}$; then impose a common reciprocal pair location while retaining the particular directional/half residuals.  It preserves source-shared dependence and heteroscedasticity while removing only the pairwise reciprocal location difference.  It does **not** establish exchangeability across pairs or patients, so pooling pairs/patients, independently resampling receiver edges, or treating $p_R$ as a population $p$-value would be P0 changes.

For $B=8192$,

$$
p_{R,i}^{(m)}=\frac{1+\#\{b:R_{0,i,b}^{(m)}\ge R_i^{(m)}\}}{8193}.
$$

The minimum is $1/8193=0.0001220554$.  The frozen $0.025$ condition permits tail count at most $203$ ($204/8193>0.025$).  This is a valid finite Monte-Carlo rank convention conditional on the stated null/resampling construction; it is not exact unconditional type-I control for arbitrary CCEP distributions.

## Domain, split, and hidden-freedom audit

| Item | Finding / required boundary |
|---|---|
| Voltage scale | $\sigma_{csh}>0$ and finite is necessary.  The frozen nonfinite/zero-scale fail-closed fixture prevents division-by-zero or arbitrary clipping. |
| Time units | $t$ is compared only with $10$ and $50\,\mathrm{ms}$ in the same decoded clock.  Exact sample/time/unit validation is therefore part of the mathematical domain, not bookkeeping. |
| Subject labels | `sub-1, sub-5` are development; `sub-4, sub-3, sub-2` are confirmation by the frozen SHA-256 ordering.  The subject string/serialization must be byte-defined in implementation; changing display order is not a new randomization. |
| Pair labels | Canonical node order is channels-TSV order, and the pair hash includes snapshot, subject, and both canonical nodes.  Sorting node names lexically instead changes the allocation and is prohibited. |
| Half labels | Per-site, onset-ordered, zero-based even/odd trial indices are required.  Reordering after seeing response values, or using receiver-local trial indices, changes the null. |
| Polarity | A canonical node occurring under both stimulation-polarity labels is entirely excluded before signal access.  Without this exclusion, direction can be confounded with a reversed physical stimulation definition. |
| Pseudoreplication | Edges share sites, trials, reference, and subject.  Median-over-pairs is an estimand compression only; it does not supply independent observations. |
| Reference transform | CAR75 and bipolar are matched readouts, not mutually invertible truth measurements.  Their agreement/disagreement cannot identify $H_s$, $R_c$, or $C_{\rm ref}$. |

## Counterexamples and consequences

**C1: nonlinear observation counterexample.**  A symmetric signed transfer coefficient can yield unequal peak absolute magnitudes after different baseline scales, artifacts, receiver gains, or reference transforms.  Thus P1 is not necessary for a biological/self-adjoint mechanism without the extra observation assumptions explicitly disclaimed by the contract.

**C2: ratio-degeneracy counterexample.**  If within-direction split halves happen to agree exactly while reciprocal magnitudes differ, $u=0$ and $v>0$, so the regularized $R$ is extremely large (for $A_{r\leftarrow s}^{A,B}=2$ and $A_{s\leftarrow r}^{A,B}=1$, it is approximately $3.33\times10^{11}$).  This is defined, but demonstrates why $R$ is a tolerance statistic and why the tail calculation and minimum evocation/repeatability gates are indispensable.

**C3: reference-nuisance nonidentifiability.**  From

$$
V^{\rm obs}_{c\leftarrow s}=C_{\rm ref}R_c[H_s*u_s]+a_{cs}+\eta_{cs},
$$

finite observations cannot uniquely factor $C_{\rm ref}$, $R_c$, $H_s$, and $a_{cs}$.  Two factorizations can have the same observed CAR75/bipolar data but different latent transfer symmetry.  Therefore neither result label is evidence for a neural Riemannian metric, geodesic, ambient dimension, consciousness, memory, self, hash, or AGI.

## Lane conclusion

`MATH_READY_FOR_INDEPENDENT_STATUS_AUDIT`.  The frozen analysis is internally defined and dimensionless under its explicit fail-closed domain.  Its only admissible scientific output is the predeclared five-subject, finite observed reciprocity/reference-comparison label.  P1's empirical/open status requires the separate routes recorded in `12-routes.md`; no raw signal was accessed in this lane.

## Signal-blind precision addendum: lexical-ULP v4

The real `sub-5` metadata supplied a counterexample to the former exact-integrality
apparatus rule: 331/344 eligible onset lexemes had nonintegral exact products with
2048 despite lying within their printed last-place uncertainty of one integer
sample. This is P0 for executable trial eligibility, not biological evidence.

For a finite exact Decimal lexeme $x$ with exponent $e$, define
$q=2048x$ and $b=2048\,10^e/2$. If $q$ is already integral, retain that exact
sample. Otherwise accept only when the integer set
$\{n\in\mathbb Z:|n-q|\le b\}$ has exactly one member; zero, multiple, or tied
candidates fail closed. The implementation computes the lower and upper integer
bounds using exact Decimal ceiling/floor, so it has no float or rounding-mode
choice. For `415.5825195`, $q=851112.9999360$ and $b=0.0001024$, giving the unique
sample 851113. The acquisition/baseline/early/prestim cardinalities remain
1127/1014/82/82. This rule is an adopted representation assumption that the
hash-locked TSV lexeme was nearest-rounded at its written decimal place; it is not
a claim of sub-sample physiological timing accuracy.
