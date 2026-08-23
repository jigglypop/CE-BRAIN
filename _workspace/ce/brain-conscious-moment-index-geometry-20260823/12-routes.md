# BA-SRM5 대안 경로와 강한 반증 조건

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-conscious-moment-index-geometry-20260823`

## Route A — spectral rank-4 moment + sparse index

목표는 독립 source-locked recording에서 isolated rank-4 tangent spectral subspace,
4D shared observation quotient, 그리고 hippocampal address의 cortical reinstatement
increment를 하나의 사슬로 검정하는 것이다. 자유도는 dimension menu 9개,
window, encoder, covariance, sparsity, quantizer, nuisance model을 discovery 안에서
고정한 수와 함께 보고해야 한다.

가장 강한 falsifier는 paired held-out dimension sweep에서 $d=4$가 다른 차원보다
$\Delta\mathrm{ELPD}>2SE$를 보이지 못하거나, mode 4/5 gap과 recurrent perturbation
stability가 사라지는 경우다. 이때 `MOMENT_RANK4_NOT_SUPPORTED` 또는
`LOOP_SELECTION_NOT_IDENTIFIED`다. 수학상 loop 또는 BA-SRM4의 숫자 4는 사전확률을
올릴 근거도 아니다.

## Route B — dimension-free recurrent workspace

recurrent processing은 인정하되 fixed rank를 부여하지 않는다. latent dimension은
held-out likelihood로 선택하고, shared index는 필요한 경우만 별도로 검정한다.

가장 강한 falsifier는 Route A가 같은 split·nuisance·parameter budget에서 B보다
반복적으로 우세한 경우다. B가 같거나 낫다면 recurrentity가 4라는 수를 선택한다는
주장은 지지되지 않는다. 이 route는 A의 가장 중요한 matched control이다.

## Route C — high-dimensional recurrent state, no common collapse

각 region의 고차원 state와 modality-specific decoder만 사용한다. shared R4보다
예측·cross-decoding이 좋다면 common index가 불필요하다.

가장 강한 falsifier는 regularized shared quotient가 modality-held-out decoding과
perturbation stability에서 C를 이기면서 information-loss cost를 명시적으로 감당하는
경우다. 단, 우세해도 lossless compression이나 phenomenology 동일성을 뜻하지 않는다.

## Route D/E의 폐쇄 유지

BA-TR11/13의 폐쇄 때문에 curvature/holonomy를 memory 또는 consciousness와
동일시하는 Route D는 재개하지 않는다. curvature는 representation diagnostic일 수
있어도 selector나 memory identity의 충분조건이 아니다. literal cryptographic
hippocampal hash Route E도 충돌·근사·data-processing 한계 때문에 재개하지 않는다.
허용되는 것은 collision 가능한 sparse address와 그 독립 incremental evidence뿐이다.

## 공통 controls와 상태

필수 control은 raw high-dimensional state, unconstrained latent dimension, PCA/CCA,
feedforward-only, dimension-free recurrent model, random sparse projection,
cortical-only similarity, semantic-only retrieval, time-shuffled address다. 모든 비교는
subject/session-held-out split과 동일 time windows, target, nuisance regression을
공유해야 한다.

현재 `NO_DATA_OPENED`이므로 A/B/C의 empirical 우열은 [미완성]이다. 이 routes 문서는
새 숫자 4를 생성하지 않으며 BA-SRM4 finite-output quotient를 whole-brain rank로
변환하지 않는다.
