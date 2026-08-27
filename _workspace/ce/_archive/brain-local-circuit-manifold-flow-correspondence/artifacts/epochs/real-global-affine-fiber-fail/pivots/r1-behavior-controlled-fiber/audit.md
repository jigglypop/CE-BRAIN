# R1 독립 상태 감사

Gate: PASS — valid empirical STOP/FAIL, no apparatus defect found.

감사는 동결 계약, `analyze_behavior_pivot.py`, `result.json`, `source-receipt.json`을 읽기 전용으로 대조했다. 고정 DANDI 자산의 바이트 수와 SHA-256이 일치하고 원 NWB 삭제가 기록됐다. train-only unit retention, train-only 신경·행동 정규화와 PCA, development 선택 뒤 test materialization, 동일 행의 대조 모형, 쌍체 블록 bootstrap, 평가 입력에서의 정확한 수축성 계산, split 내부 100-bin 이동 행동 재적합을 확인했다.

후보는 `full VAR+input`과 `base+input`보다 나빴고, 두 우위 조건과 수축 조건 $q_{\max}<1$을 실패했다. 이동 행동 대조군보다 실제 행동이 나았다는 사실은 이 음성 판정을 뒤집지 않는다. 따라서 `STOP`은 구현 결함이 아니라 동결한 R1의 유효한 kill condition이다. DANDI `001695` 확인 자산은 열지 않는다.
