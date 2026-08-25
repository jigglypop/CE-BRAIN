# Source lane — public neural recording and biological baseline

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

Access date: 2026-08-25

No dataset bytes, endpoint values, session lists or model results were opened.
This lane verifies only primary papers, official documentation and the current
provenance boundary.

## Source-lock table

| Contract input | Status | Verified content | Remaining stop |
|---|---|---|---|
| Allen Visual Coding public dataset identity | VERIFIED | de Vries et al. (2020), DOI `10.1038/s41593-019-0550-9`, describes the Allen Brain Observatory Visual Coding resource and its public access path | the optical and electrophysiology resources must not be conflated; this contract requires the Neuropixels/electrophysiology subset |
| Allen Neuropixels release and schema family | VERIFIED_PARTIAL | official Neuropixels Visual Coding white paper v1.0 and AllenSDK documentation describe the October 2019 release, probe recordings, visual cortex/hippocampus/thalamus coverage and session/unit/spike metadata access; current `EcephysProjectCache.MANIFEST_VERSION` is `0.2.1` | exact cache manifest bytes, checksums, data-use terms and eligible session IDs were not queried |
| 2026 recurrence–dimensionality analysis | VERIFIED | Stringer et al. (2026), `s41593-026-02395-w`, uses Allen visual electrophysiology, state-conditioned spike-count covariance, participation ratio, finite-neuron correction and network-size extrapolation | the recurrence relation is model-dependent and observational; it is not an intervention result |
| Binning and robustness | VERIFIED | reference spike bin is 100 ms with 50 ms and 200 ms robustness analyses; HMM states and cross-validated latent-factor analysis are distinct preprocessing/model steps | exact code revision and eligible-session receipt remain unfrozen |
| Participation-ratio observable | VERIFIED | $D_{\rm PR}=(\operatorname{tr}C)^2/\operatorname{tr}(C^2)$ for the declared covariance convention, with neuron-count dependence and extrapolation treated explicitly | covariance debiasing and extrapolation code must be frozen before any local score |
| Activity versus synaptic datasets | VERIFIED | the 2026 paper's Allen Neuropixels activity data and separate mouse/human in-vitro synaptic physiology are different datasets; associated analysis/code is archived under Zenodo DOI `10.5281/zenodo.18503652` | they may not be merged into one subject/session likelihood or treated as direct edge/state pairs |
| Intervention status | VERIFIED | visual electrophysiology is observational with stimuli/behavior/state segmentation and optotagging, not a causal perturbation of recurrent strength | maximum empirical ceiling is L3 compatibility, never L4 mechanism identity |
| Count observation model | VERIFIED_PARTIAL | sorted spike counts and source-declared binning support a state-conditioned count/covariance baseline | Poisson versus negative-binomial likelihood, conduction delay and continuous-time GLM are not fixed by the recurrence paper alone |
| E1 within-resource held-out split | UNVERIFIED_PENDING_METADATA | official API exposes session/subject metadata, so whole-session splitting is technically plausible | exact eligible Neuropixels IDs, repeats, missingness and leakage-free assignment require a metadata-only query |
| Predecessor dataset-family/namespace nonoverlap | VERIFIED | predecessor closed Allen data are ex-vivo `aisynphys` Synaptic Physiology (`slice/experiment/cell/pair`); E1 is in-vivo Visual Coding Neuropixels (`subject/session/probe/unit`) | cross-resource numeric ID comparison is `NOT_APPLICABLE / SEMANTICALLY_INVALID`; animal-level donor overlap remains unresolved but is not a session-leakage key |

## Biological and measurement separation

The source-supported biological hypothesis is restricted to state-dependent
recurrent cortical population dynamics. The measured object is not the hidden
state or an anatomical edge but sorted extracellular spikes, binned into a
declared time window and summarized by a finite-sample covariance estimator.
Thus the admissible starting decomposition remains

$$
dx_t=F_{\rm bio}(x_t,u_t;\theta_{\rm bio})dt+G(x_t)dW_t,
$$

$$
y_{ik}\mid x(t_k)\sim
\operatorname{CountModel}(\Delta t\,\lambda_i(x(t_k));\psi_i).
$$

The source locks $\Delta t\in\{50,100,200\}$ ms as reported analysis scales,
with 100 ms primary. It does not uniquely select Poisson, negative-binomial or
another count likelihood. A full delayed point-process GLM therefore remains
`UNVERIFIED` and cannot be smuggled into $F_{\rm bio}$ as an established fact.

The paper's homogeneous-network expression relating normalized participation
dimension and recurrence is a conditional model relation, not a universal
biological law. The exact hypotheses and estimator must be carried into any
future baseline reproduction.

## Provenance stop and evidence ceiling

The next permitted empirical action is a metadata-only source-lock query that
freezes release identity, official manifest/schema, eligible E1 subject/session
IDs, exclusions, repeated epochs, license/data-use receipt, and a canonical
within-resource split receipt. Signal arrays and scientific endpoints remain
unopened. The predecessor dataset-family namespace is already distinct; the
remaining leakage question is entirely within the Neuropixels resource.

The official compatibility documentation records a breaking AllenSDK 2.0
revision: Visual Coding Neuropixels NWB files released before 2020-06-11 are
not guaranteed to work with the reorganized 2.0.0 format. The future source
receipt must therefore freeze both manifest version `0.2.1` and the actual NWB
release generation; a bare session ID is insufficient provenance. The same
documentation discloses default unit filters—`presence_ratio < 0.95`,
`isi_violations > 0.5`, or `amplitude_cutoff > 0.1` are hidden by default.
Those filters affect covariance and dimension estimates, so the future
contract must explicitly choose filtered or complete units before endpoint
access and must retain the alternative as a measurement control.

Even after a clean metadata lock, observational held-out prediction can reach
at most `BIO_EVIDENCE_L3`: recurrence/history/dimensionality compatibility.
It cannot establish a causal edge deformation, whole-brain Riemannian metric,
consciousness, selfhood or a preferred dimension $4$–$6$.

## Primary and official references

1. de Vries et al., *A large-scale standardized physiological survey reveals functional organization of the mouse visual cortex*, Nature Neuroscience (2020), https://doi.org/10.1038/s41593-019-0550-9.
2. Allen Institute, *Neuropixels Visual Coding white paper v1.0*, https://brainmapportal-live-4cc80a57cd6e400d854-f7fdcae.divio-media.net/filer_public/80/75/8075a100-ca64-429a-b39a-569121b612b2/neuropixels_visual_coding_-_white_paper_v10.pdf.
3. Allen Institute, AllenSDK documentation, https://alleninstitute.github.io/AllenSDK/index.html.
4. Stringer et al., *Strong and localized recurrence controls the dimensionality of neural activity across brain areas*, Nature Neuroscience (2026), https://www.nature.com/articles/s41593-026-02395-w.
5. Associated 2026 analysis/code archive, Zenodo, https://doi.org/10.5281/zenodo.18503652.
6. AllenSDK, *Visual Coding – Neuropixels: AllenSDK 2.0 and Data Compatibility*, https://allensdk.readthedocs.io/en/stable/visual_coding_neuropixels.html.
7. AllenSDK `EcephysProjectCache` reference (`MANIFEST_VERSION = 0.2.1`, session-table API), https://allensdk.readthedocs.io/en/bound-dependencies/allensdk.brain_observatory.ecephys.ecephys_project_cache.html.
