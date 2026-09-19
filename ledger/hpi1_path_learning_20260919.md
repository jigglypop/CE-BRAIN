# HPI1 이력 경로 학습 반영 — 2026-09-19

사용자 제공 2026-09-18 학습 개선본의 채택 코드와 짝지은 16개 초기화 결과를 `verify/HPI1_path_learning`에 보존했다. 실제 함수 본문은 바꾸지 않고 독립 실행 형태로 정리했다.

[실행과 한계](../verify/HPI1_path_learning/README_KO.md) · [결과](../verify/HPI1_path_learning/RESULTS.json) · [원본 출처](../verify/HPI1_path_learning/PROVENANCE.json) · [반영 전 검사](../verify/HPI1_path_learning/PACKAGING_CHECK.json)

800상태·추가 EM 160회에서 문맥 분리 완료 13/16→16/16. 기존 13개의 분리 시점은 그대로이며 시간차 개선으로 해석하지 않는다. 이는 후향적 계산 현상 재현이며 실제 칼슘 신호나 MaleCNS 검증이 아니다.

확인: 구조 검사 8조건 및 seed 262 대조/후보 재실행 배열 일치. 전체 저장소 하네스는 이 환경에서 미실행. 기존 main과 봉인 자료는 변경하지 않는 연구 브랜치 반영이다.
