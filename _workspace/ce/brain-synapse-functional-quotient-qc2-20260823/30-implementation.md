# BA-SRM3 implementation log

Status: COMPLETE

구현은 support auditor, train-only operator, frozen evaluation의 순서로 진행한다. support가
실패하면 operator code를 실제 데이터에 실행하지 않는다.

기존 support/extractor/operator 코드는 진단 증인으로만 보존한다. clamp mode를 누락한
extractor를 이 run 안에서 수리해 재적합하지 않는다. 결과를 본 뒤 측정모형을 바꾸는 행위는
새 판본이므로 BA-SRM4의 별도 계약으로 이관한다.
