# Mathematics lane

Status: COMPLETE

## NMB.1 Observation and coordinate contract

For session `s`, let recorded observations obey a declared model

$$
z_{s,t}=C_su_{s,t}+\varepsilon_{s,t},
$$

and let frozen preprocessing and coordinate maps produce normalized base and
fiber variables `(x,y)`.  This equation is a measurement definition, not an
assumption that the latent state `u` or map `C_s` has been identified.

Before held-out access, freeze the map family, preprocessing, scales, maximum
order, parameter bounds, domain/collar radii, and one target theorem level.
Their canonical bytes receive separate hashes.  GLOBAL requires C0 and raw
map/graph moduli; LOCAL adds core/open-collar coverage; MATCHED additionally
adds exact inverse/forward contacts and zero boundary residuals.

## NMB.2 Simultaneous envelope event

Let `Q` be the complete list of scalar norm/conorm claims routed to the chosen
theorem.  For every admitted session `s`, the measurement procedure must
produce upper and lower confidence endpoints satisfying the single event

$$
\mathcal E=
\left\{
L_{s,q}\le q_s\le U_{s,q}
\quad\text{for every }(s,q)\in\mathcal S\times\mathcal Q
\right\},
$$

$$
\Pr(\mathcal E)\ge1-\eta,
\qquad 0<\eta<0.05.
$$

The declared family size must equal

$$
M=|\mathcal S|\bigl(|\mathcal Q_{\rm upper}|+
|\mathcal Q_{\rm lower}|\bigr).
$$

Pointwise intervals, winner-only intervals, or an omitted derivative order do
not imply this event.  The bridge does not calculate `E`; it checks that the
declared family is complete and that every supplied endpoint lies inside the
frozen family:

$$
U_{s,q}\le U_q^{\rm frozen},
\qquad
L_{s,q}\ge L_q^{\rm frozen}.
$$

Thus coverage validity remains an explicit statistical premise.

## NMB.3 Theorem routing

On the event `E`, the frozen bounds instantiate the existing exact chain

$$
\text{measurement envelopes}
\Longrightarrow C^0 + C^n
\Longrightarrow \text{full global}
\Longrightarrow \text{local}
\Longrightarrow \text{exact matched},
$$

stopping at the level frozen before analysis.  A matched failure does not
invalidate a predeclared global theorem, and a global request does not demand
unmeasured boundary contacts.  Every predecessor failure remains visible.

The conclusion is conditional for the supplied sessions.  It does not imply
out-of-sample population coverage unless the statistical design separately
proves that generalization.

## NMB.4 Split and provenance gate

Canonical metadata assignments must exactly equal the envelope session set.
Every session's specimen and split must match, session IDs must be unique, and
calibration/development/held-out must each contain at least two specimens.
This prevents represented specimen leakage; it does not prove biological
independence of source identifiers.

The present E1 receipt is local only.  Therefore

$$
\boxed{
\texttt{external_remote_metadata_receipt_verified=False}
}
$$

and both graph and rank empirical flags remain false even if a caller supplies
the string `SOURCE_LOCKED_EMPIRICAL`.  This repairs the former string-only
promotion path in the rank protocol.

## NMB.5 Graph dimension versus signal rank

The joint adapter requires the dimension spectra to correspond exactly to the
held-out session IDs.  It reports whether the graph base dimension `d_G` and
selected neural signal rank `d_S` are numerically equal, but always keeps

$$
\boxed{d_G=d_S\ \text{numerically}\ \not\Rightarrow\
\text{same mathematical object or consciousness dimension}.}
$$

Consequently graph/rank identity and consciousness claims remain false at
both equality and inequality fixtures.
