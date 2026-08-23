# BA-ERC1-E2 source lock

Status: COMPLETE

## 1. Evidence boundary

E2 introduces no empirical datum and no new biological mechanism. Its physical input is the predecessor's already source-locked passive cable limit; its new evidence is mathematical and numerical only. The exact manufactured fields are consequences of the frozen boundary-value problem, not observations of a brain.

## 2. Frozen inherited sources

| source | role retained at E2 | admissible statement |
|---|---|---|
| Rall, *Branching dendritic trees and motoneuron membrane resistivity* (1961), PMID 14435979 | branched passive-cable lineage | Cable reductions and branch-current conditions are established modelling tools; no exact morphology claim is inherited. |
| Hodgkin & Huxley, *A quantitative description of membrane current and its application to conduction and excitation in nerve* (1952), DOI 10.1113/jphysiol.1952.sp004764 | broader electrical-model boundary | Active channel dynamics motivate later stages but are not executed at E2. |
| Pods, Schönke & Bastian, *Electrodiffusion models of neurons and extracellular space using the Poisson–Nernst–Planck equations* (2013), PMCID PMC3703912 | higher-fidelity boundary | PNP remains a deferred control and is not silently identified with the passive cable. |
| BA-ERC1 `10-sources.md` | SHA-256 `6fb05ae378257ed666d34ca5c5cdd2611e7f6ce1fcf070dd988c9a231b9c0f35` | Complete predecessor source map; no biological success is inherited. |

Primary links retained from the predecessor source lock:

- Rall: <https://pubmed.ncbi.nlm.nih.gov/14435979/>
- Hodgkin–Huxley: <https://physoc.onlinelibrary.wiley.com/doi/10.1113/jphysiol.1952.sp004764>
- PNP boundary model: <https://pmc.ncbi.nlm.nih.gov/articles/PMC3703912/>

## 3. Numerical apparatus provenance

The two paths use formulas frozen in `00-contract.md` and derived in `11-math.md`:

- FV: an independently written conservative cell-centred star-graph stencil plus classical RK4.
- FEM: assembled linear-element consistent mass/stiffness matrices plus the installed `scipy.linalg.eigh` generalized symmetric eigensolver.

The installed environment was checked before implementation: system Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1, bytecode disabled. A library routine is implementation provenance, not empirical support for the cable equation.

## 4. Source-status ledger

| item | formal status |
|---|---|
| Passive Y-cable PDE and junction law | `[adopted model]`, inherited and hash-bound |
| Exact symmetric/antisymmetric modes | `[derived]`, proved in `11-math.md` |
| FV/FEM agreement thresholds | `[preregistered numerical decision rule]`, not a literature fact |
| D0 disconnected-junction response | `[prediction/adverse control]` |
| Biological fidelity, real morphology, channel parameters | `[unfinished/unopened]` |
| Consciousness dimension, hippocampal hash, memory, AGI | `[no active claim]` |

No source in this lane licenses promotion above synthetic E2 numerical equivalence.
