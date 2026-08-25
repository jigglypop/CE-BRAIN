# BA-OBS-DISC2R 실제 뇌 D0–D3 최종 상태 감사

Status: COMPLETE

## 판정

`PASS`.

독립 read-only 감사자는 retry run-lock
`d70f83387143145bb1c40258c1f1a3974c168c30c677d2f67cc5819ffdccd291`과
D0–D3의 stage marker, range receipt, endpoint, endpoint receipt, result를 고정된
스냅샷에서 재검사했다. P0와 substantive P1은 없다.

## 실행 무결성

| 단계 | 환자 | source | target | raw range | 결과 |
|---|---:|---:|---:|---:|---|
| D0 | 24 | 192 | 3,072 | 1,920 | `PASS_SELECTION_ONLY` |
| D1 | 8 | 64 | 1,024 | 640 | `PASS_INTERMEDIATE` |
| D2 | 12 | 96 | 1,536 | 960 | `PASS_INTERMEDIATE` |
| D3 | 30 | 240 | 3,840 | 2,400 | `PASS_FINAL` |

네 단계의 74명은 서로 겹치지 않는다. 모든 source에는 정확히 10개의 byte range가
있고, 모든 range/endpoint receipt의 `raw_payload_persisted`는 `false`다. 각 opened
marker의 predecessor hash, endpoint의 range hash, result의 endpoint-receipt hash는
단계별로 일치한다.

수치 적합은 D0 후보 rank 5 또는 7, 최대 condition number 약 212였고, D1–D3의
winner rank는 5, condition number는 약 11.6–12.3이었다. 모두 사전 고정한
condition 한계 `10^7`보다 충분히 낮다.

## 단계별 경험적 판정

| 단계 | 평균 개선 또는 CV 개선 | 환자/fold 일관성 | permutation | 판정 |
|---|---:|---:|---:|---|
| D0 SC | 0.063820222 | 6/6 fold | 구조 선택 단계 | 선택 |
| D0 SAC | 0.064045780 | 6/6 fold | 구조 선택 단계 | SC와 0.005 tie band 안; 더 단순한 SC 선택 |
| D1 SC | 0.0203434 | 7/8 환자 | `p=1/512` | 통과 |
| D2 SC | 0.0168684, 80% LCB 0.0127012 | 10/12 환자 | `p=1/1024` | 통과 |
| D3 SC | 0.0173522, 97.5% LCB 0.0102676 | 23/30 환자 | `p=1/4096` | 최종 통과 |

D3 matched prestimulus 음성대조는 평균 개선 `0.0000445`, 16/30 환자,
97.5% LCB `-0.0001462`, permutation `p=0.0568848`로 gate를 통과하지 않았다.
contact-mean 진단은 통과해 `REFERENCE_CONCORDANT`로 분류됐다.

## P2와 해소

잠긴 pre-D0 linkage 테스트의 세 번째 검사는 D0 marker가 없어야 한다고 주장한다.
따라서 실제 실행 뒤 재호출하면 의도적으로 `2 PASS / 1 FAIL`이 된다. 이는 과학적
회귀가 아니라 수명주기 한정 테스트다. 그 테스트는 성공으로 고쳐 쓰지 않았고,
별도의 read-only `artifacts/validate_disc2r_postrun.py`가 실행 뒤 해시 연쇄·분할·개수·
수치 gate와 control을 검사한다.

## 형식 지위와 주장 상한

- `[검증 산출]` 새 환자에 대한 다중 피험자 human SPES CCEP observed-kernel 예측에서,
  frozen nuisance와 source anchor calibration을 통제한 단순 Euclidean distance
  attenuation 식 SC가 temporal baseline보다 일반화 성능을 보였다.
- `[검증 산출]` 이 결과는 D3 bipolar primary의 최종 gate와 matched prestimulus
  negative control을 함께 통과한 의미의 `PASS_FINAL`이다.
- `[미완성]` 좌표는 fsaverage/MNI305-derived proxy이며 실제 axonal path 또는
  conductance tensor를 측정하지 않았다.
- `[주장 제한]` 생물학적 Riemannian metric·geodesic, 무한차원 상태공간,
  의식·자아·해마·AGI를 검증한 결과가 아니다.
