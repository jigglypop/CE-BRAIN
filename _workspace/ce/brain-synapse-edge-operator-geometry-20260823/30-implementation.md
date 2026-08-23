# BA-SRM4 discovery-only 구현 기록

Status: COMPLETE

Date: 2026-08-23

Implementation scope: stable audit가 허용한 schema, typed IC/VC extraction,
LIMS slice-specimen quarantine/split receipt, discovery-only candidate generation만 수행했다.
validation/development와 confirmation/test outcome은 열지 않았다.

## 1. 구현 경계

[관측 비교] outcome을 읽은 1,383개 sequence는 BA-SRM2/3에서 이미 접촉한 frozen eligible
manifest에만 속한다. 새 BA-SRM4 split에서 이들을 모두 `discovery-contaminated`로 강제했다.
나머지 group에서는 `slice` identity와 schema만 읽었고 response, residual, score, rank를 읽지
않았다.

group key는 source/schema 보정 뒤 다음처럼 고정했다.

```text
group_id = slice.lims_specimen_name
semantics = conservative LIMS slice-specimen equivalence class
row identity = slice.ext_id
donor / animal identity = UNRESOLVED_IDENTITY_KEY
```

4,276개 `slice` row는 4,259개 group으로 묶였다. 16개 중복 label이 33개 row를 덮었고,
`ext_id`로 hash했으면 그중 14개 label이 서로 다른 bucket을 가로질렀다. V2 grouping은 동일
LIMS slice-specimen을 하나의 bucket에 원자적으로 둔다.

## 2. mode-aware dataset

`prepare_discovery_dataset.py`는 다음 unit contract를 강제한다.

| channel | stored coordinate |
|---|---|
| presynaptic IC command | $I/I_0$ |
| presynaptic VC command | $V/V_0$ |
| postsynaptic IC response/noise | $V/V_0$ |
| postsynaptic VC response/noise | $I/I_0$ |
| 다른 mode의 typed channel | `NaN` structural missingness |

0으로 빈 channel을 채운 뒤 pooling하지 않는다. pulse 0--7만 input/history로 쓰고 pulse
8--11의 amplitude, latency, rise, decay를 16-coordinate target으로 쓴다. 미래 target 값을
바꾸어도 input feature가 변하지 않는 sentinel test를 통과했다.

[관측 비교] V2 receipt:

| stratum | sequences | LIMS slice-specimen groups | target MAD |
|---|---:|---:|---:|
| ex, pre-IC → post-IC | 713 | 168 | 16/16 positive finite |
| in, pre-IC → post-IC | 641 | 185 | 16/16 positive finite |
| ex, pre-VC → post-IC | 16 | 6 | 16/16 positive finite |
| in, pre-VC → post-IC | 13 | 4 | 16/16 positive finite |

VC strata는 IC와 합치지 않고 `ABSTAIN_INSUFFICIENT_GROUPS`로 남겼다.

V2 group split은 discovery 2,308, discovery-contaminated 414, validation 772,
confirmation 765개다. 이는 group membership 수이며 validation/confirmation outcome support나
성능을 뜻하지 않는다.

## 3. discovery equation bank와 선택

입력은 모두 물리 기준으로 무차원화한 뒤 discovery-fold 안에서 robust location/scale로 다시
표준화했다. 고정 후보군은 order 1 main effect와 사전 지정한 10개 order 2 interaction뿐이다.
LIMS slice-specimen group을 유지한 5 outer × 4 inner nested CV로 term/ridge를 선택했다.

첫 all-discovery greedy V1은 fold마다 불안정한 noise, slope, frequency term까지 포함했다. 이
결과를 성공으로 채택하지 않고, outer-training 5개 모델 중 최소 3개에서 다시 선택된 term만
남기는 stability-core V2를 만들었다. interaction은 두 parent가 모두 안정적일 때만 남긴다.
이 보정은 discovery 안에서만 이루어졌고 validation/confirmation은 계속 봉인됐다.

표준화 좌표를 별표로 쓰면 frozen 16-output 후보식은 다음과 같다.

$$
\widehat{\mathbf y}_{\mathrm{ex}}^*
=\mathbf b_{\mathrm{ex}}
+\mathbf B_{a,\mathrm{ex}}\,\bar a_{0:7}^*
+\mathbf B_{\ell,\mathrm{ex}}\,\bar\ell_{0:7}^*
+\mathbf B_{r,\mathrm{ex}}\,\bar r_{0:7}^*
+\mathbf B_{d,\mathrm{ex}}\,\bar d_{0:7}^*
+\mathbf B_{50,\mathrm{ex}}\,\Phi_{50}^*,
$$

$$
\widehat{\mathbf y}_{\mathrm{in}}^*
=\mathbf b_{\mathrm{in}}
+\mathbf B_{a,\mathrm{in}}\,\bar a_{0:7}^*
+\mathbf B_{\ell,\mathrm{in}}\,\bar\ell_{0:7}^*
+\mathbf B_{r,\mathrm{in}}\,\bar r_{0:7}^*
+\mathbf B_{d,\mathrm{in}}\,\bar d_{0:7}^*.
$$

여기서 $\bar a$, $\bar\ell$, $\bar r$, $\bar d$는 각각 과거 pulse 0--7의 fitted
response amplitude, latency, rise, decay 평균이다. post-IC에서 $a_k/V_0$를 쓰며 시간은
$T_0$로 나눈다. 50 ms causal trace는

$$
\Phi_{50}
=\sum_{k=0}^{7}\frac{a_k}{V_0}
\exp\!\left[-\frac{t_8-t_k}{50T_0}\right],
\qquad T_0=1\,\mathrm{ms}
$$

이다. exp 인자는 무차원이다. 각 $\mathbf B$는 16-vector이고 전체 coefficient, input/target
location/scale은 `discovery-equation.v2.json`에 고정했다.

[경험식][미완성] ex 안정 term은 5개, ridge 10, estimated df 5.194다. in 안정 term은
4개, ridge 1, estimated df 4.778이다. 둘 다 독립 group 수의 절반보다 훨씬 작다.

## 4. finite quotient geometry

출력은 global discovery OOF residual covariance를 0.5 diagonal shrinkage하고 positive floor를
더해 whiten했다. 입력 reference는 all-discovery robust-standardized finite base chart의 identity
metric이다. 따라서 이번 $\widetilde G$는 finite positive-semidefinite matrix라 trace-class다.
이는 전체 history Hilbert 공간의 reference가 아니라 이 fitted finite chart만의 receipt다.

[관측 비교] relative singular threshold $10^{-4}$에서 pointwise 결과는 다음과 같다.

| stratum | stable terms | pointwise hard rank | $d_{\rm eff}(1)$ median |
|---|---:|---:|---:|
| ex IC→IC | 5 | 4 (713/713) | 3.2945 |
| in IC→IC | 4 | 4 (641/641) | 3.5620 |

ex의 `history_amp_trace_tau50_typed`는 conditional hard-rank increment가 0/713이다. 따라서
이 term은 frozen tolerance에서 별도 관측 차원을 만들지 않는다. coefficient가 정확히 0이거나
모든 표현에서 전역적으로 불필요하다는 뜻은 아니다. 실제 V2 coefficient vector norm은 작지만
0은 아니다. 나머지 ex 네 방향과 in 네 방향은 각 sample에서 conditional rank increment 1이다.

$d_{\rm eff}(10^{-4})$는 ex 4.0279, in 3.9999이고 hard rank와 정확히 같지 않다. 이는 hard
threshold 아래의 작은 mode를 $d_{\rm eff}$가 연속적으로 세기 때문이다. raw term 수, hard
rank, effective dimension을 서로 바꾸어 쓰지 않는다.

## 5. 활성 artifact와 폐기 artifact

활성 V2 artifact:

| path | SHA-256 |
|---|---|
| `artifacts/prepare_discovery_dataset.py` | `db41af69f53769b72a6740a5953ea325eb7f32662c3c3f3676c80144f908addf` |
| `artifacts/test_prepare_discovery_dataset.py` | `12c73e15cc7075df5833ce4f6a140d8edd7ddfa5827220afbff75920169486cd` |
| `artifacts/discover_edge_equation.py` | `e8edbdf398f5a06a43aeec7e6385a3ff0f036fdea4c24a87ab671163c621369f` |
| `artifacts/test_discover_edge_equation.py` | `d0606b49ffc41c1bd04f8803fa2fb52c12a648502d3e35febf338cbc84a65b52` |
| `artifacts/split-groups.v2.jsonl` | `9848d5dce89fd668cf5b4b4a07b894961b549d300e4169f00008939b91b9f93d` |
| `artifacts/discovery-dataset.v2.npz` | `5516a7523f7525218ad628ef2586ad0ea042e4e9dc5214a58b22d665905e2773` |
| `artifacts/discovery-dataset-receipt.v2.json` | `07a1b2743359eeb3383e307de464cc9ea6d7b833025b595608b3af46ef3ef167` |
| `artifacts/discovery-equation.v2.json` | `127489197d7fa7d5047e475ec2203dba354c2610873104f36515ab4c653fb1f1` |

다음 V1 artifact는 `SUPERSEDED / DO NOT CITE`다.

- `split-groups.jsonl`, `discovery-dataset.npz`, `discovery-dataset-receipt.json`:
  `slice.ext_id`를 group hash에 사용해 반복 LIMS slice-specimen leakage를 막지 못했다.
- `discovery-equation.json`, SHA-256
  `1a76f6c1a23ebdf354c0a5433b30ada6a4972771cc8641b3fb10d478c8cf538d`:
  stability-core rule 전의 all-discovery greedy 후보다.

## 6. 구현 상태

구현은 discovery-only에서 완료했다. frozen candidate는 `[경험식][미완성]`이다. nested discovery
$\Delta$MSE는 후보 생성 진단이지 validation evidence가 아니다. source-mechanistic baseline,
raw-RBF, time shuffle, clamp swap을 동일 validation split에서 비교하기 전에는 Route A의 우세나
생물학적 법칙을 주장하지 않는다.
