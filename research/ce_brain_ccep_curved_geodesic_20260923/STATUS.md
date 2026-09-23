# STATUS — CCEP 곡률 계량(곡면 geodesic) 대 동결 Euclidean `SC`

이 파일은 마일스톤마다 갱신한다. 최신 항목이 맨 위.

## 2026-09-23 03:55 KST — 단계 1: DISC2R 복원 + ds004457 신원 확인

- **현재 단계**: 데이터 신원·독립성 검사 (결과 endpoint 미개봉).
- **DISC2R 파이프라인**: ce-runs에는 DISC2R 파일이 없음(확인). 이 저장소 git 이력 `4fa83be2~1`의
  `_workspace/ce/brain-human-ccep-multisubject-precision{,-retry}-20260825/`에서 core·runner·split·감사·검증 코드와
  계약 문서를 읽기 전용 복사로 복원 → `recovered_disc2r/`. endpoint 표(d0–d3 JSON)와 range 영수증은 git에 없음
  (`*.json` gitignore) → 봉인 수치의 바이트 재현은 원자료 재수령(~7 GB) 없이는 불가.
- **ds004457 신원**: "Electrical stimulation of temporal and limbic circuitry produces distinct responses in human
  ventral temporal cortex" (Huang et al. 2023 J Neurosci), OpenNeuro v1.0.2 (2023-06-02), CC0, 11.7 GB, Mayo Clinic,
  **환자 5명**, 6 mA biphasic 200 µs 0.2 Hz SPES.
- **예비 판정**: 환자 5명은 환자-disjoint 개발+확인 설계(DISC2R D3 기준 30명)에 **너무 적음** →
  `DATASET_UNSUITABLE` 후보. 사용자 규칙대로 강제하지 않고 대안 탐색 중.
- **대안 탐색(메타데이터만)**: OpenNeuro iEEG 73개 중 CCEP/자극 관련 22개. 유력 후보 `ds006254`
  ("IEEG CCEP Recording", University of Alabama at Birmingham, SEEG, 30명, Talairach mm 좌표, EDF+ 주석에
  "Start Stimulation from A to B" 표기, events.tsv 없음, 1 Hz 5 mA 300 µs). `ds005448`(STReEF)는 UMCU RESPect
  (ds004080와 같은 기관, 환자 중복 배제 불가, 개인 native 좌표만) → 부적합.
- **다음 단계**: ds004457 좌표·전극형 확인 → ds006254 실현 가능성(좌표·주석·펄스 시각·처리량) 감사 →
  최종 판정 기록.
