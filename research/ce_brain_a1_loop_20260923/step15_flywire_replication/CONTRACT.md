# A1 15단계 — FlyWire(다른 개체, 암컷 뇌)에서 MaleCNS 발견 재현 (사전등록)

작성: 2026-09-23. **FlyWire 자료를 열기 전**(다운로드 진행 중)에 고정한다.

**자료.** FlyWire 783 `proofread_connections_783.feather`(Zenodo 10676866). 뉴런 쌍×neuropil 행을 쌍마다 합산한다. 주석은 `flyconnectome/flywire_annotations@8587524c`의 `Supplemental_file1_neuron_annotations.tsv`다.

**대응.** MaleCNS 슈퍼클래스와 FlyWire `super_class`를 다음처럼 맞춘다.
- cb_intrinsic ↔ `central`
- descending_neuron ↔ `descending`
- ol_intrinsic ↔ `optic`
- 세포 부류: `Kenyon_Cell`, `MBON`, `ALPN`
- 세포 유형: `EPG`

지표와 대조는 13단계(`measures`, `edge_swap_null`, 시드 20260923)와 11단계(`classify`, k=6)를 그대로 쓴다.

## 재현 판정 (MaleCNS 값 → FlyWire 허용 범위)

- **F1 목 잠재 통로** (central → descending, M1). 셋 다 만족해야 한다.
  - rank90 / DN 수가 [0.22, 0.37] 안에 있다(MaleCNS 0.295 ± 25%).
  - rank90 대조 비 ≤ 0.7 (MaleCNS 0.62).
  - PR 대조 비 ≤ 0.5 (MaleCNS 115/402 = 0.29).
- **F2 MB.** ALPN→KC 대조 비가 [0.85, 1.15]이고, KC→MBON 대조 비 < 0.7이다(MaleCNS 1.03 / 0.545).
- **F3 모듈 이분.** (cell_type, side) 가운데 뉴런 8–2,500개인 단위마다 11단계와 같은 방법으로 2차원 분산 비율을 잰다. 두 조건을 만족해야 한다.
  - KC 단위의 중앙값 < 0.4 (MaleCNS 0.24).
  - 단위 20개 이상을 가진 KC 이외 super_class마다 중앙값 > 0.5 (MaleCNS 0.66–0.78).
- **F4 방향 고리.** EPG 좌·우가 모두 11단계 기준의 고리로 분류된다.

**보고:** DN 수, 총 뉴런 수, 각 지표의 원값.

**종합:** F1–F4를 모두 재현하면 "목 잠재 통로, MB 확장·압축, KC 고차원 이분, EPG 고리가 다른 개체(암컷)에서도 성립한다"(L0, 두 개체).

## 고정 코드 (FlyWire 자료를 열기 전)

- `flywire_replication.py` sha256 `79597319625da2681563ea71bce1302c3806367cbc3bde5e934fee4f2faa8273`
