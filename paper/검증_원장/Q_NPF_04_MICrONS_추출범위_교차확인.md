# Q-NPF-04 — MICrONS 추출 범위와 개체 출처 교차 확인

작성일: 2026-09-05. 지위: **관측 자료의 범위·출처 점검**. 연결 기전이나 전체 뇌 구조의 확증이 아니다.

## 질문과 자료

[구조 자료 확보](Q_NPF_04_MICrONS_구조자료_확보.md)에서 사용한 작은 V1 column 파일이 선택된 세포 사이의 시냅스 표지를 빠뜨렸는지 확인했다. 같은 공개 commit `513a6fe738f91ce179650f1cadf26d4a4728b21a`의 `v1718_proofread_output_synapses.feather`를 추가 확보했다. 공식 notebook은 작은 파일을 V1 column 부분집합으로 설명한다. [판본 고정 원문](https://github.com/AllenInstitute/connectomics_at_cosyne/blob/513a6fe738f91ce179650f1cadf26d4a4728b21a/examples/Cosyne_Data_Access.ipynb)

기존에 정한 1,348개 root ID를 유지했다. 넓은 파일과 작은 파일 모두에서 전·후세포가 이 집합에 속한 시냅스를 고른 뒤 ID로 정렬해 비교하도록 계약을 먼저 고정했다. 불일치가 생겨도 선택 조건을 바꾸지 않는 검사다.

## 추출물 간 결과

| 항목 | 결과 |
|---|---:|
| 넓은 파일의 전체 시냅스 행 | 2,493,674 |
| 넓은 파일에서 선택된 두 partner 사이 행 | 145,598 |
| 작은 파일의 같은 선택 행 | 145,598 |
| 넓은 파일에만 있는 선택 시냅스 ID | 0 |
| 작은 파일에만 있는 선택 시냅스 ID | 0 |
| 선택 부분의 중복 시냅스 ID | 0 |

시냅스 ID뿐 아니라 전·후세포 ID, 크기, 중심 위치, 표적 분류의 여섯 필드가 모두 일치했다. 따라서 **넓은 공개 추출물에 비해 작은 파일에서만 누락되거나 달라진 선택 연결은 찾지 못했다.**

두 파일은 같은 제공자와 재구성 자료를 공유한다. 이 일치는 두 파일이 함께 가진 누락, 잘못된 분할·병합, 시냅스 검출 오류나 원 데이터 쿼리의 완전성을 독립 검증하지 않는다. 미표지 쌍은 여전히 “이 추출물에 표지가 없음”으로 해석한다. 생물학적 연결 부재로 바꾸지 않는다.

## 개체 출처 점검

MICrONS 주 논문은 단일 수컷 생쥐와 생년월일 2017-12-19를 명시한다. [논문 Methods의 Mouse lines 및 Timeline](https://www.nature.com/articles/s41586-025-08790-w)

앞선 synphys 상호 연결 분석에 실제 포함된 생쥐 slice 2,561개의 생년월일을 원 DB에서 대조했다. 전부 날짜가 존재했고 전부 달랐다. 일치 후보 0개, 결측 후보 0개였다. **메타데이터상 같은 개체일 후보는 없다.** 이 판단은 양쪽 출처 메타데이터가 정확하다는 조건 아래 성립한다. 공통 개체 식별자로 직접 대응한 검증은 아니며, 생년월일이 같았더라도 그 사실만으로 동일 개체라고 판정하지 않았을 것이다.

따라서 표본 비중복을 지지하는 출처 근거는 확보했다. 그러나 다른 개체라는 사실이 전자현미경 구조 표지와 전기생리 기능 판정을 동일한 관측량으로 만들지는 않는다. 한 EM 부피의 여러 세포를 여러 독립 동물로 세지도 않는다.

## 판정과 다음 조건

원래 질문에는 자료 신뢰성 측면에서 진전이 있었다. 작은 파일만의 선택 연결 누락을 우려한 경로와 날짜 기준의 개체 중복 후보는 이번 검사에서 발견되지 않았다. 기존 78,301개 유향 구조 연결·9,869개 상호 연결 집계는 수정하지 않았다.

다음에는 이 관측 부분망 안에서 세포 종류·거리·입출력 수를 보존하는 구조 비교를 정의할 수 있다. 그 분모는 “선택된 교정 세포 집합의 표지된 관측 그래프”로 제한한다. 모든 미표지 쌍을 확정 음성으로 가정하는 생물학적 연결 확률과 구분한다. 계산법이 연결 수를 보존하는지, 충분히 다양한 그래프를 탐색하는지 확인하기 전에는 상호 연결의 초과나 독립 재현을 주장하지 않는다. 전체 뇌 구조와 인과 기전은 계속 미확립이다.

## 자료와 검증

넓은 추출물 95,916,378바이트를 새로 받아 출처·판본·위치·SHA-256을 원장에 등록했다. 기존 세포·column 파일은 재사용했다. 비교 결과와 개체 날짜 점검은 로컬 자료에서 재현됐다.

- [추출 비교 계약](../../verify/Q-NPF-04/allen_synphys/microns_export_overlap_contract.json), [추출 비교 결과](../../verify/Q-NPF-04/allen_synphys/microns_export_overlap_result.json), [비교 코드](../../verify/Q-NPF-04/allen_synphys/microns_export_overlap.py)
- [넓은 파일 수집 영수증](../../verify/Q-NPF-04/allen_synphys/microns_broad_acquisition_receipt.json)
- [개체 출처 점검 결과](../../verify/Q-NPF-04/allen_synphys/microns_specimen_screen_result.json), [점검 코드](../../verify/Q-NPF-04/allen_synphys/microns_specimen_screen.py)
- [데이터 원장](../../ledger/data_registry.md)

```powershell
.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_export_overlap.py --verify
.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/microns_specimen_screen.py
```
