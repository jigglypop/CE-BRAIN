# BA-ERC1 route decision

Status: COMPLETE

## 1. Route comparison

| route | decision | reason / stop boundary |
|---|---|---|
| Nonlinear cable--HH system on a branched metric graph | `SELECTED / L0_AUTHORIZED` | Begins with voltage, axial current, capacitance, ionic current, synaptic current, and Kirchhoff flux; supports cheap unit and conservation falsifiers. |
| Bounded causal-history synaptic conductance | `SELECTED_HYPOTHESIS / AFTER_BASELINE` | Preserves the electrical port $i_{\rm syn}=g(V-E)$ while allowing edge state to depend on normalized past voltage/current/gates. Must beat a finite-state conductance control. |
| Physical reference metric plus observation pullback quotient | `SELECTED_FORMALIZATION / NOT_BIOLOGICAL_METRIC` | Separates state prior from finite measurement sensitivity and preserves the finite-observation no-go. |
| Full Poisson--Nernst--Planck electrodiffusion | `DEFERRED_HIGH_FIDELITY_CONTROL` | More fundamental for ionic concentration and extracellular-potential effects, but too costly for the first equation screen. Open only after cable L0 and independent-solver checks pass. |
| Previous covariance/resolvent $Q_t$ as governing dynamics | `REJECTED_AS_STARTING_LAW` | It is a downstream statistic of observations, not a current/voltage propagation equation. |
| Abstract Riemannian gradient flow without an electrical action, units, or boundary law | `REJECTED` | Does not specify charge conservation, membrane current, or what physical metric is being used. |
| Loop $\Rightarrow4$ dimensions / curvature $=$ consciousness / hippocampus $=$ literal hash | `PROHIBITED_INFERENCE` | None follows from cable electrodynamics or the available evidence. Dimension four receives no privileged candidate status. |

## 2. Ordered execution

1. Run exact unit, sign, causality, counterexample, and continuous-energy audits.
2. Run one deterministic passive manufactured solution and a Y-branch Kirchhoff fixture.
3. If and only if both pass, compare an independent cable solver under the same sealed geometry and stimuli.
4. Then test active HH propagation against point-neuron and passive-cable controls.
5. Only after baseline reproduction may the history functional compete with finite exponential/bi-exponential synapses.
6. Measurement stress precedes all real data. Current-clamp and voltage-clamp coordinates remain separate.
7. Real-data development and held-out/intervention stages require a successor contract.

## 3. Present decision

BA-ERC1 advances only the cable--HH equation and its conditional function-space geometry to L0. The causal-history conductance is an open hypothesis. Effective dimension is a downstream diagnostic and is not scored in this run. Biological validation, behavior, consciousness, memory, hippocampal retrieval, and AGI endpoints remain unopened.
