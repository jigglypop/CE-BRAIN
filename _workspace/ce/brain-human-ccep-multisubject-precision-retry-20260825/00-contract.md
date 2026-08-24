# BA-OBS-DISC2R 연구 계약 — pre-range linkage 구현 재시도

Status: COMPLETE

Implementation: PENDING

Scientific endpoint: UNOPENED

PREDECESSOR: `_workspace/ce/brain-human-ccep-multisubject-precision-20260825`

## 0. 목적과 변경 상한

이 run은 predecessor의 실제 인간 CCEP 검증을 과학적으로 재설계하지 않는다. predecessor는
D0 open marker를 쓴 뒤 첫 HTTP request보다 앞선 `_ordered_trials()`에서 25.7 ms 만에
`sealed event/sample crosswalk mismatch`로 중단됐다. range/endpoint/result receipt는 없고
전압 endpoint는 관측되지 않았다.

허용되는 변경은 하나뿐이다.

> record-level crosswalk **집계**를 event별 lookup으로 오독한 구현을 제거하고, 선택 trial을
> hash-locked source manifest의 정확한 `clean_trials` 행과 직접 대조한다.

식, split, source/receiver/trial 선택, 전압 구간, bin, endpoint, optimizer, threshold,
bootstrap/permutation, claim ceiling은 predecessor run-lock SHA-256
`2ea67d6728e1b1573d5efa15adef2e9f14ad0127bed458f43b265a3d376d9e6d`의 판본을 그대로
상속한다. 그중 하나라도 바뀌면 이 run은 무효다.

## 1. 상속되는 과학 계약

| 항목 | 고정값 |
|---|---|
| dataset | OpenNeuro `ds004080` v1.2.4, DOI `10.18112/openneuro.ds004080.v1.2.4`, tree `c4fd7418883e33b024292468eb14da1649f51aae` |
| source manifest | `../brain-human-ccep-multisubject-precision-20260825/artifacts/metadata-source-manifest.json`, SHA `9ed8cb9d7a12cf293f8a899aa9a04de7951109b0fad0505e08ebe93f9e11b3c3` |
| split manifest | `../brain-human-ccep-multisubject-precision-20260825/artifacts/endpoint-blind-split-manifest.json`, SHA `d4b03a984f03529c870df6d2c62034443b08611ddacd3cfe4244067bb5ff96f7` |
| participants | patient-disjoint D0/D1/D2/D3 = `24/8/12/30`; participant당 8 sources |
| source targets | 4 anchor + 12 query, clean trials 10 |
| raw range | zero-based `[anchor-f_s, anchor+floor(0.120f_s)]`, version-locked HTTP 206, multiplexed little-endian float32 |
| endpoint | contact baseline median; bipolar; pooled 10-trial baseline `1.4826 MAD`; ten-trial mean; five-bin dimensionless RMS; `log(E+10^-6)` |
| bins | `[10,18),[18,30),[30,50),[50,80),[80,120] ms`; matched pre is `-300 ms` shift |
| candidates | `S0/SC/SAC/SH0/SHA0`; 식과 bounds는 predecessor contract §5–6 |
| D0 | six-fold patient-blocked; all numerical gates; relative improvement `>=0.005`; wins `>=4/6` |
| D1/D2/D3 | predecessor의 `511/1023/4095` geometry permutations, participant bootstrap 8,192, 순차 barrier |
| controls | D0 temporal/orientation/post-pre apparatus; D3 prestimulus negative control and contact-mean diagnostic |
| fixture | unseen-v2 `0/64` false selection, receipt SHA `f313ad0a5b9994d53533c4629a1b6f24a19319e3a0f78ad4c05fe4d8ec8e9341` |

## 2. 전기식과 후보식

상속되는 출발식은

$$
\mathcal C_\ast\dot v=-\mathcal A_\ast v+\mathcal B_sQ_s\delta(t),
\qquad
v(t)=e^{-t\mathcal C_\ast^{-1}\mathcal A_\ast}
\mathcal C_\ast^{-1}\mathcal B_sQ_s
$$

다. local elliptic/heat와 cable leading grammar만 제한적으로 비교하며, 공통항은 자유 source
offset과 정확히 겹치는 intercept/current coefficient를 제거한

$$
T_i^\star(x)=\beta_1\log x+\beta_2x
+\gamma_1\widetilde A_i\log x+\gamma_2\widetilde A_i x
$$

다. 후보 geometry 항은 `0`, $-ar$, $-ad_G$, $-\kappa r^2/x$,
$-\kappa d_G^2/x$다. 모든 입력은 predecessor와 동일하게 무차원이다.

## 3. 수정되는 linkage의 정확한 의미

metadata audit code는 electrical event마다

$$
\delta_e=\texttt{sample\_start}_e-operatorname{round}(f_s\,\texttt{onset}_e)
$$

를 검사하고 `Counter(str(delta_e))`를 record의 `event_sample_crosswalk`에 저장했다. 따라서
정상 record의 값은 event lookup이 아니라 정확히

```json
{"0": <electrical_event_count>}
```

이어야 한다.

새 linkage는 다음을 모두 요구한다.

1. record 집계가 위 형태와 정확히 일치한다.
2. `(subject, record_id, source site_id)`로 source manifest의 한 source를 유일하게 찾는다.
3. split의 10 trials 각각에 대해 같은 `event_index`의 manifest `clean_trials` 행이 정확히
   하나 존재한다.
4. `anchor_sample_zero_based`와 원 `orientation_site`가 manifest 행의
   `anchor_sample_zero_based`와 `site`에 정확히 일치한다.
5. split의 source contacts, stimulation type, current, frequency, pulse width도 source manifest와
   일치한다.

하나라도 다르면 raw request 전에 `SOURCE_TRIAL_LINKAGE_STOP`이다.

## 4. predecessor 실패의 비노출 증거

- marker: `d0-opened.json`, SHA
  `ff4ac42a44d34c3a4438250392d042133f84dcb8ee341537a05dfcdf8a85661e`
- failure: `d0-failure.json`, SHA
  `15e711b64cb0fe2b73aa3b1c1c8235ab80961b63e40f97fdf8969d3f686d0c1a`
- marker time: `16:32:20.023673Z`; failure time: `16:32:20.049343Z`
- missing: range receipt, endpoint file, endpoint receipt, D0 result
- call order: `_ordered_trials` precedes the `fetch_trial` closure execution and thread pool

따라서 같은 endpoint-blind split의 재사용은 response를 보고 고른 재시도가 아니다.

## 5. claim ceiling과 falsifier

- **BIO_STARTING_MECHANISM:** short-window human SPES response의 cable/heat leading proxy.
- **CE_DELTA:** 74명 patient-disjoint observed-kernel prediction.
- **MEASUREMENT_MODEL:** electrode/reference/volume-conduction/artifact/noise가 섞인 bipolar readout.
- **DATA_PROVENANCE:** predecessor lock 및 두 manifest SHA를 재검증한다.
- **DATA_SPLIT:** predecessor split byte를 그대로 사용한다.
- **OBSERVABLES:** predecessor의 dimensionless bipolar energy와 controls.
- **RESIDUAL_RULE:** anchor-only profiled source offset; source-equal, participant-equal Huber loss.
- **FALSIFIER:** linkage/apparatus/D0/D1/D2/D3/negative-control 중 하나라도 실패하면 즉시 stop.
- **MODEL_SELECTION:** 구조 선택은 D0 한 번뿐이다.
- **REVISION_TRIGGER:** 이 run에서 D0 marker 뒤 실패하면 재실행하지 않는다.
- **CLAIM_CEILING:** `MULTI_SUBJECT_HUMAN_SPES_CCEP_OBSERVED_KERNEL_PREDICTION`까지만. 생물학적
  metric/geodesic, latent dimension, 무한차원, 의식·자아·해마·AGI 검증을 주장하지 않는다.

## 6. 실행 순서

1. corrected linkage test를 전체 74명/592 selected sources에 실행한다.
2. new run-lock과 독립 pre-D0 감사를 봉인한다.
3. D0 raw range를 한 번만 열어 apparatus를 계산한다.
4. apparatus PASS일 때만 D0 fit, 이후 D1→D2→D3 barrier를 따른다.
