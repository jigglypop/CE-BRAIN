# CE-NPF 대체 생물자료 D2 Chen 2025 소스·스키마 사전검사 결과

## 판정

- 자료 획득: `CHEN_2025_D2_SOURCE_DOWNLOAD_PASS`
- 원래 계획한 endpoint: `D2_WEIGHT_LATENCY_ENDPOINT_BLOCKED_SCHEMA`
- 지위: **자료는 준비됐지만 weight--latency 생물 endpoint는 미실행**이다.
- 원 질문에 답했는가: 아니다. 같은 연결의 유효강도·총지연을 동물 단위로
  결합해 검정할 수 있는지만 확인했다.
- 반증된 생물 가설: 없음. 이번 정지는 입력의 join key와 전수 반복자료가 없는
  데 따른 적격성 판정이다.

## 목표와 이 단계가 필요한 이유

최종 목표는 연결 존재, 유효 가중치와 지연의 변화가 국소 출력의 유효계량을
어떻게 바꾸는지 생물자료로 제약하는 세부식을 얻는 것이다. 이 단계에서는
그 사슬 전체를 주장하지 않고, 마우스 V1 L2/3에서 인과적으로 자극한 단일
presynaptic cell과 postsynaptic current 사이의 관측식을 실제 source data가
어디까지 식별하는지만 검사했다.

## 입력 정본과 획득 영수증

- 논문: Chen et al., *Nature Neuroscience* (2025), DOI
  `10.1038/s41593-025-02024-y`, PMCID `PMC12497651`.
- PMC article version: `PMC12497651.1`, `CC BY-NC-ND`.
- 자동화 가능한 현재 공식 배포 정본: NLM PMC Article Datasets의
  `pmc-oa-opendata` 공개 S3 객체. 2026-08-26 종료된 legacy PMC 경로는
  사용하지 않았다.
- 독립 교차확인 경로: Springer Nature `static-content.springer.com`의 동일
  supplementary object. 아래 MD5·SHA-256가 PMC 객체와 일치한다.

| 파일 | bytes | MD5 | SHA-256 |
|---|---:|---|---|
| `41593_2025_2024_MOESM3_ESM.zip` | 19,175,486 | `5e8d9d88940222ee4e5a792b1c0d9d62` | `498f744da73cb90a0c994c5e7e9581a3f722b0e3b3f20b5880936a8ee0dfbfd8` |
| `41593_2025_2024_MOESM4_ESM.zip` | 26,435,183 | `2b5ad484fc8d67c4b3f197a61693a7d2` | `58051c07b54416e2ed8980e126d9c93459fa5eadf90f39ba7039dcfe8b617daa` |
| `PMC12497651.1.json` | 2,789 | `d4767b1e1e710abcd04baa1f1863c7d5` | `ff1e15f3a398c093da2a040010a4a565ab918f8c3fde5d0e4311f5d69e789f7a` |
| `PMC12497651.1.xml` | 301,840 | `4d9154b30600a9d4970383c92ae9e6d2` | `45c20536858c7606f7baf26097bbcea66fe7cdf55d23ad9001872a82971453e1` |
| `41593_2025_2024_MOESM1_ESM.pdf` | 7,091,705 | `53ec63ec82fa5758e1d635d74044875e` | `64f66e1a52e1602ef3bb4540a4b5e7c81343a85e899566dabce6649c711ea3b8` |

두 source ZIP의 전체 CRC를 검사했다. MOESM3의 181 members, MOESM4의
14 nested ZIP과 그 내부 전 항목에서 오류가 없었다.

## 실제로 열린 스키마

논문은 12 FOV, 12 postsynaptic cells, 12 animals에서 549개 후보
presynaptic cells를 자극하고 41개 연결을 식별했다고 보고한다. 각 후보는
24--60회 자극됐고 artifact 제외 뒤 9--42회가 남았다고 기술한다.

| source table | 열린 값 | 보존된 식별자 | 빠진 핵심 값 |
|---|---|---|---|
| Fig. 3B | 연결 41개의 response rate | 행 순서뿐 | FOV·animal·edge ID, 전수 trial |
| Fig. 3C | 같은 41행의 onset/peak latency, peak amplitude, half-width, rise time, decay tau | 행 순서뿐 | FOV·animal·edge ID, 전수 trace |
| Fig. 3D | 11 FOV의 506 후보·40 연결에 대한 2D soma 좌표/거리, 연결별 response rate·peak amplitude | `FOV1`--`FOV11` | latency, 명시적 Fig. 3B/C join key |
| Fig. 4/5 | 일부 FOV·cell과 multi-cell response/reconstruction | 패널 내부 ID | Fig. 3C latency와의 전수 join key |
| raw-like traces | 선택된 예시 세포·pattern의 반복 trace | 예시 내부 열 | 549 candidates 전수 반복 trial |

Fig. 3B와 3C의 행 정렬은 같은 workbook 안에서 동일 연결을 나타내는 것으로
읽을 수 있다. 그러나 그 41행을 Fig. 3D의 11 FOV·40 spatial edges에 붙이는
공급자 key는 없다. 값 순서나 중복 response rate를 이용해 사후 추정한 join은
계약 입력으로 허용하지 않는다. Fig. 3D의 FOV는 논문상 서로 다른 동물에
대응하므로 거리--연결의 범위고정 재현에는 쓸 수 있지만, 원래 D2의
동물-clustered weight--latency 검정에는 충분하지 않다.

## 식별 가능한 관측식

자극 반복을 `k`, 연결 존재를 `A_{uij}`, photo-induced AP 성공을
`Q^{(k)}_{ui}`, synaptic response/detection 성공을 `B^{(k)}_{uij}`라 두면,
이 preparation에서 허용되는 최소 관측모형은

\[
I^{(k)}_{uij}(t)
=A_{uij}Q^{(k)}_{ui}B^{(k)}_{uij}
w^{\mathrm{eff}}_{uij}h_{uij}(t-\tau^{\mathrm{obs}}_{uij})
+\epsilon^{(k)}_{uij}(t)
\]

이다. 여기서 peak 또는 10--15 ms STA amplitude는
`w^{eff}`의 관측 proxy이고,

\[
\rho^{\mathrm{obs}}_{uij}
\simeq P(Q_{ui}=1)P(B_{uij}=1\mid Q_{ui}=1)
\]

이다. 논문이 보고한 presynaptic AP 확률은 0.9보다 크므로 response rate는
release·response·detection 실패가 합쳐진 확률이지 순수 release probability가
아니다.

관측 onset latency는

\[
\tau^{\mathrm{obs}}_{uij}
=\tau^{\mathrm{opto/AP}}_{ui}
+\frac{\ell^{\mathrm{axon}}_{uij}}{v_{uij}}
+\tau^{\mathrm{syn}}_{uij}
+\tau^{\mathrm{post/filter}}_{uj}
\]

로만 쓸 수 있다. 자료의 2D soma 거리는 `ell^axon`이 아니고, 각 항을 분리할
경로길이·presynaptic spike time·postsynaptic membrane/readout 측정이 없어
`v`를 역산할 수 없다.

## 차단 이유와 주장 상한

다음 필수조건이 빠져 원래 D2 endpoint를 열지 않는다.

1. latency 행을 동물/FOV/edge에 붙이는 명시적 공급자 key,
2. 전 549 candidates 또는 41 connections의 trial-level trace와 반복 ID,
3. 독립적인 axonal path length와 지연 성분 분해,
4. 학습 전후 또는 기전 개입 전후의 `delta W`, `delta tau`,
5. 같은 동물의 population representation·행동 endpoint.

따라서 이 자료는 이 preparation에서 `A`, response rate,
`w^{eff}`, `tau^{obs}`라는 구성요소가 관찰된다는 범위고정 L1 근거를 제공할
수는 있으나, `delta(A,W,tau) -> delta g -> delta behavior` 통합사슬의
`BIO_EVIDENCE_L0 / BIOLOGICAL_MEDIATION_UNTESTED` 지위는 바꾸지 않는다.

## 원래 질문·반증·생존·다음 허용 행동

- 원래 질문에 답했는가: 연결 강도와 지연을 동물 단위로 결합하거나 이들이
  표현기하를 바꾼다는 질문에는 답하지 못했다.
- 무엇이 반증되었는가: 생물학적 명제가 아니라 “공개 source data만으로
  animal-clustered weight--latency endpoint를 실행할 수 있다”는 입력 가정이
  기각됐다.
- 무엇은 살아 있는가: 위의 인과 edge 관측식, FOV가 보존된 정적
  distance--connectivity scaffold 재현, 그리고 별도 종단·개입자료에서
  `delta W`, `delta tau`를 시험하는 경로다.
- 다음에 허용되는 행동: Chen 자료에서 값 순서를 추정해 누락 key를 복원하거나
  pooled 41 edges를 독립 표본으로 취급하지 않는다. 다음 독립 계보는 같은
  동물의 paired learning/control intervention과 행동을 보존한 자료로 연다.
