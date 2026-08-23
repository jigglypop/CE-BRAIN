# BA-SRM5 source lane: recurrent access, memory indexing, and neural geometry

Status: COMPLETE

Date: 2026-08-23

Scope: primary-source verification and candidate-data mapping only. No validation or
confirmation outcome was opened.

## Evidence table

| ID | Established source evidence | Exact provenance | Interpretation and limits |
|---|---|---|---|
| S1 | Masking preserved early visual responses but removed later EEG signatures associated with recurrent/reentrant processing in seen versus unseen trials. | Fahrenfort, Scholte & Lamme (2007), DOI `10.1162/jocn.2007.19.9.1488`, PMID `17714010`, [PubMed](https://pubmed.ncbi.nlm.nih.gov/17714010/), accessed 2026-08-23. | Supports an association between conscious report and recurrent visual processing under masking. EEG, masking, attention, and report confounds do not establish a universal causal consciousness mechanism. |
| S2 | **BACKGROUND_CANDIDATE / NOT USED IN ACTIVE CLAIM:** an eLife article reports a causal perturbation study of NMDA-receptor involvement in recurrent processing and perceptual integration. | Exact primary provenance is recorded as eLife article `100530`, DOI `10.7554/eLife.100530`, [eLife](https://elifesciences.org/articles/100530), accessed 2026-08-23; author metadata was not independently locked in this lane. | Excluded from the active claim until full primary metadata and methods are locked. Even if admitted later, causal evidence would remain intervention-, task-, and region-specific. |
| S3 | Primary monkey motor-cortex recordings showed structured population dynamics during reaching, including oscillatory population activity and preparatory-state dependence. | Churchland et al., "Neural population dynamics during reaching" (Nature, 2012), DOI `10.1038/nature11129`, [Nature](https://www.nature.com/articles/nature11129), accessed 2026-08-23. Gallego et al. (2017), DOI `10.1016/j.neuron.2017.05.025`, PMID `28595054`, is retained as a review synthesis: [PubMed](https://pubmed.ncbi.nlm.nih.gov/28595054/). | Primary evidence supports structured population dynamics, not a universal intrinsic dimension. Neither paper implies dimension 4. |
| S4 | Active dimensions shift over time and depend on task variables in reach-to-grasp population data. | [Condition-Dependent Neural Dimensions Progressively Shift during Reach to Grasp](https://pubmed.ncbi.nlm.nih.gov/30540947/), accessed 2026-08-23. | Direct caution against freezing one dimension across epochs, tasks, subjects, or modalities. |
| S5 | Hippocampal memory-indexing theory proposes that hippocampus stores an index of neocortical areas activated by an event and reactivation can reactivate that cortical array. | Teyler & DiScenna (1986), DOI `10.1037/0735-7044.100.2.147`, PMID `3008780`, [PubMed](https://pubmed.ncbi.nlm.nih.gov/3008780/), accessed 2026-08-23. | This is the original theory, not a direct demonstration of a literal address/hash or lossless cortical reconstruction. |
| S6 | Simultaneous DG/CA3 recordings under degraded/conflicting cues gave direct input-output evidence consistent with DG pattern separation and CA3 pattern completion. | Neunuebel & Knierim (2014), DOI `10.1016/j.neuron.2013.11.017`, [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3904133/), accessed 2026-08-23. | Strong circuit-specific physiological evidence, but not evidence that all hippocampal regions or memories implement one fixed code. |
| S7 | Human high-resolution fMRI found activity in CA3/DG consistent with pattern separation, with CA1/subiculum and cortical regions showing different biases. | Bakker et al. (2008), DOI `10.1126/science.1152882`, [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2829853/), accessed 2026-08-23. | Spatial resolution combines CA3 and DG; this is not a clean causal dissociation. |
| S8 | Optogenetic reactivation of DG neurons tagged during fear conditioning induced context-specific freezing; controls included non-fear and EYFP conditions. | Liu et al. (2012), DOI `10.1038/nature11028`, [Nature](https://www.nature.com/articles/nature11028), accessed 2026-08-23. | Interventional sufficiency evidence for a tagged mouse DG ensemble in a fear task. It is not proof that the ensemble is the complete memory or that human conscious access is the same mechanism. |
| S9 | Optogenetic inhibition/stimulation of fear and extinction ensembles altered retrieval and relapse. | [Distinct hippocampal engrams control extinction and relapse](https://www.nature.com/articles/s41593-019-0361-z), Nature Neuroscience, accessed 2026-08-23. | Interventional necessity/sufficiency evidence in mouse fear extinction; behavioral memory expression is not identical to cortical reinstatement or conscious report. |
| S10 | Public human intracranial data are reported as including hippocampal and cortical ECoG/iEEG, episodic recall, reinstatement, and sharp-wave ripple annotations. | Norman et al. (2019) data, DOI `10.5281/zenodo.3259368`, [NIAID data portal](https://data.niaid.nih.gov/resources?id=zenodo_3259368); Norman et al. (2021) data, DOI `10.5281/zenodo.4759103`, [Zenodo](https://zenodo.org/records/4759103), accessed 2026-08-23. | Candidate only; suitability is unresolved pending schema, electrode-coverage, subject/session-identity, behavioral-report, and preprocessing receipts. |

## Mechanism, theory, measurement, and conjunction

Established mechanisms include recurrent cortical feedback signatures under visual
masking, hippocampal DG/CA3 transformations under controlled cue degradation, and
intervention effects on tagged mouse engram ensembles. The memory-indexing proposal is
a theory connecting hippocampal indices to distributed cortical traces. Neural
manifolds are a measurement/modeling description of population activity; their
dimension is task-, epoch-, sampling-, noise-, and estimator-dependent. The conjunction
"recurrent processing + a shared rank-4 moment + hippocampal index + cortical
reinstatement = a conscious memory state" is UNVERIFIED. No cited source establishes
that conjunction.

## Rank and hash boundary

The sources support testing low-dimensional effective coordinates and similarity-based
retrieval. They do not support a literal cryptographic hash: a cryptographic hash is
designed to destroy neighborhood geometry and makes collisions unpredictable, whereas
hippocampal indexing theories require a cue-dependent, biologically addressable link
that can support partial-cue retrieval. A permissible candidate is a sparse,
similarity-preserving address (for example, sparse random projections or locality-
sensitive coding) whose collision and retrieval behavior are measured against dense,
semantic, cortical-only, and time-shuffled controls. This is a candidate representation,
not an established biological fact.

## Future data and claim ceiling

The Norman 2019/2021 public iEEG datasets are candidates for simultaneous
hippocampal-cortical testing based on their reported modalities and task labels, but
suitability remains unresolved until schema, electrode coverage, identity, and report
window receipts are checked. They do not by themselves provide causal perturbation. A
future test must split by subject/session, freeze electrode inclusion and report
windows, and distinguish association from intervention.

Current ceiling: component mechanisms have external source evidence, but this run's
conjunction remains `CONCEPTUAL_ONLY`; no run-level L1/L2 achievement is claimed.
A possible future L3 held-out predictive test remains prospective. No source licenses
a fixed dimension of 4, a literal hash, consciousness identification, complete memory
reconstruction, or AGI transfer.
