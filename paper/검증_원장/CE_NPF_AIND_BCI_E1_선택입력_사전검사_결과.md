# CE-NPF AIND BCI E1 선택 입력 사전검사 결과

Status: `SELECTED_INPUT_PREFLIGHT_FAIL / E1_BLOCKED_INPUT`

Claim ceiling: `BIO_EVIDENCE_L0 / BIOLOGICAL_MEDIATION_UNTESTED`

Stage 10: `STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE`

판정일: 2026-08-31

## 1. 목표와 판정 경계

**최종 목표.** 국소 회로의 물리·시냅스·전도 상태가 출력-상대 Riemann
계량을 바꾸고 그 변화가 독립 행동을 매개하는지를 동일 생물계 자료로 판정한다.

**이번 하위 목표.** 생물 endpoint를 열기 전에 AIND BCI v2의 pre/BCI/post
epoch와 dF/F clock이 사전등록한 분석 코호트를 지탱하는지 검사한다.

**왜 필요한가.** clock·epoch가 맞지 않으면 이후 target response나 계량 변화가
생물학적 변화인지 자료 정렬 오류인지 구별할 수 없다.

**목표 명료성과 이탈.** 이번 A gate는 입력 장치 검사다. 통과해도 생물 가설을
지지하지 않으며, 실패해도 생물 가설을 반증하지 않는다. A 실패 뒤 B/C를 열면
계약 이탈이므로 즉시 정지한다.

**다음 gate.** 현재 잠금 코호트에는 없다. 공급자가 clock·epoch를 교정한
versioned source 또는 독립적으로 잠근 새 코호트에서 A를 새로 사전등록해야 한다.

## 2. 불변 계약과 실행 계보

- [사전등록 E1 계약](CE_NPF_AIND_BCI_E1_동일세포_개입계약.md)
- [선택 입력 auditor](../6_뇌/국소회로_상태다양체_흐름_대응/repro/audit_aind_bci_v2_selected_input_preflight.ps1)
- [기계 판독 receipt](../../artifacts/brain/ce_npf_aind_bci_e1_selected_input_preflight_v1/receipt.json)

SHA-256은 다음과 같다.

| 대상 | SHA-256 |
|---|---|
| 사전등록 계약 원문 | `23fe688c9dba568b8594509cd21cc28ae1de9fcb16baa60c6fbe53c641a4f22c` |
| auditor | `a43e3f2dd8018641ab3d1ed2fd7fcc21058198c848089338272f4cdc8344ef84` |
| receipt | `6aec99dc72eade652d886724199fb604423fc6989b8d77b3309be043c7b832fd` |
| canonical selected-object manifest | `2711a627397ee7887da4b8089fc31b08a41553fbdf49e00910f1293d1500cbc7` |

계약 원문은 결과로 덮어쓰지 않았다. receipt의 `preregistered_contract_sha256`와
현재 계약 bytes가 일치하므로 독립 재실행에서 같은 hash gate를 통과할 수 있다.

## 3. 열린 입력과 열지 않은 endpoint

22개 consolidated `.zmetadata`는 VersionId·opaque ETag·byte length·원문
content SHA-256으로 잠갔다. A에 허용한 176개 `/0` 값 chunk는 같은 원시
content 잠금에 decoded-payload SHA-256을 더했다. 누락된 VersionId·content
hash와 중복 요청은 0건이다.

값으로 연 것은 epoch의 `id`, `stimulus_name`, start/stop frame/time, dF/F
`starting_time`, 독립 `imaging_rate`뿐이다. 다음은 모두 열지 않았다.

- dF/F response data chunk
- PhotostimTrials·Trials의 B 단계 값
- `hit`, lick, reward, threshold, zaber 행동 endpoint
- ROI table 값과 image-mask 값

`forbidden_chunk_request_count=0`이고 biological endpoint 관련 요청 flag는 모두
`false`다.

## 4. A gate 결과

허용 clock 잔차는 start와 stop 각각 1 frame 이하이고 모든 stop은 start보다
엄격히 뒤여야 한다. `photostim`과 `photostim_post`는 각각 정확히 한 번,
`BCI`는 한 번 이상이어야 한다.

| asset | animal | 실패 사유 | 최대 clock 잔차(frame) |
|---|---:|---|---:|
| `a9b68b93-c445-4809-9cab-d6282ae64483` | 740369 | `photostim_post` 0개 | 0 |
| `cf8baa51-6086-4f5a-aeca-b685b59f1662` | 740369 | epoch frame--time 불일치 | 10.709439 |
| `c7470968-816b-49ae-9ebd-b4579e458cb4` | 767715 | epoch frame--time 불일치 | 160.768474 |
| `81b6cb9b-5885-4b29-8354-5d44065fc5a7` | 767715 | epoch frame--time 불일치 | 134.596571 |
| `3a82e844-4bd9-4f0e-a017-56419a967c79` | 767715 | epoch frame--time 불일치 | 147.573732 |
| `b28d6321-1b1b-4110-87fb-0e19325c1dfe` | 767715 | epoch frame--time 불일치 | 18.435250 |

세션 통과/실패는 16/6이다. A 뒤의 유효 세션은
`731015:4, 740369:3, 754303:5, 766719:3, 767715:1`이다. 5개 animal과
총 15세션 이상은 남지만 animal 767715가 1세션뿐이어서 모든 animal의 최소
2세션 gate를 실패한다.

| 단계 | 판정 |
|---|---|
| A: epoch/clock | `AIND_BCI_E1_SELECTED_INPUT_PREFLIGHT_FAIL` |
| B: target/ROI join | `NOT_RUN_PREREQUISITE_FAILED` |
| C: endpoint byte lock | `NOT_RUN_PREREQUISITE_FAILED` |
| E1 | `E1_BLOCKED_INPUT` |

provider metadata는 22/22 `Invalid`이므로 선언 rate를 사후 재추정하거나 다른
metadata로 보정하지 않았다. NWB TimeSeries에서 균일 표본의 시간은
`starting_time + frame/rate`로 정해지므로 이 불일치는 입력 gate 실패다.

## 5. 결론과 한계

1. **원래 질문에 답했는가:** 아니다. 생물 endpoint를 열기 전 입력에서
   정지했으므로 국소 Riemann 계량, 기능적 접힘, 발달 의미 또는 행동 매개를
   판정하지 않았다.
2. **무엇이 반증되었는가:** 현재 AIND BCI v2 22-session 잠금 코호트가 이 E1
   계약의 물리 clock·pre/post 코호트 조건을 만족한다는 명제만 반증되었다.
3. **무엇이 살아 있는가:** 조건부 Riemann 모형과 세 생물 가설은 모두
   미검정으로 남는다.
4. **다음 허용 행동:** 교정된 source 또는 새 코호트에서 A부터 다시 잠근다.
   1-frame 문턱, animal당 2세션 문턱 또는 선언 rate를 사후 완화하지 않는다.
   새 A가 통과해도 PhotostimTrials·Trials clock은 B에서 별도로 검사한다.

이 잠금은 per-object VersionId를 순차 수집한 비원자적 S3 snapshot이고 수집 뒤
latest VersionId를 다시 확인하지 않았다. A에서 관측한 Blosc flag는 `0x33`뿐이므로
compressed LZ4 split/unshuffle 분기의 실행 검증으로 확장하지 않는다. 약 58 Hz
calcium timing은 calcium kinetics·synaptic·hardware delay가 합쳐진 scale이므로
millisecond 축삭 전도속도를 식별하지 못한다.

## 6. 자료 정의

- [Allen SWDB BCI dataset fields](https://allenswdb.github.io/physiology/ophys/BCI/BCI-dataset.html)
- [Allen SWDB BCI stimuli](https://allenswdb.github.io/physiology/ophys/BCI/BCI-stimuli.html)
- [NWB TimeSeries format](https://nwb-schema.readthedocs.io/en/latest/format.html)
