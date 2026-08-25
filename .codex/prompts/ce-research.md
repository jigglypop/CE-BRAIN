`$ce-research` 스킬로 명시적으로 연구 등급인 요청만 full run으로 수행하라.

주제: $ARGUMENTS

1. 먼저 `_workspace/ce/.active-run`과 해당 run의 `status`를 확인한다. 같은 질문·데이터 판본·endpoint의 후속 계산, recovery, 감사, 그림 또는 논문이면 그 `CE_RUN`을 그대로 이어받는다.
2. 적용 가능한 미완성 run이 없을 때만 `.codex/hooks/run.cmd init _workspace/ce/<주제-슬러그>-<YYYYMMDD>`로 run을 만든다. 다른 미완성 run이 있으면 `REUSE_REQUIRED`가 새 디렉터리 생성을 막는다. 독립 계약일 때만 사유를 먼저 적고 `init --new-contract`를 쓴다.
3. 00-contract.md에 질문·정의역·주장·기호·허용 오차를 고정한다.
4. 뇌·기억·의식 주제라면 먼저 `_workspace/ce/brain-algorithm-route-ledger.md`와 선행 run 12/31, 존재하는 40을 읽는다. 40이 없으면 마지막 numbered audit와 closure 부재를 쓰고, 이전 결과·퇴역 경로·후보 선택을 계약에 고정한다.
5. 독립적인 source/math 레인은 필요할 때 병렬 실행하고, 구현을 멈춘 안정 스냅샷을 한 번 감사한다.
6. 이론 잔차나 반례가 확정되면 부모 주장을 좁히고 끝내지 않는다. 같은 run에서 `counterexample`로 증인을 잠그고 구조적으로 다른 기전 경로 3개를 등록한 뒤, 결과를 열기 전에 선택한 경로를 `pivot`으로 시작한다.
7. 감사 Gate PASS 후 승인된 구현을 검증하고, 안정화된 원장을 근거로 주제에 맞는 `docs/<분야>/<논문>/00_논문목차.md`와 그 목차가 순서대로 연결한 장별 Markdown을 제자리 갱신한다. `_workspace/`에는 논문 사본을 만들지 않는다. `40-final-report.md`에는 `DOCS_PAPER: docs/<분야>/<논문>/00_논문목차.md`와 짧은 run 인계만 남기고, 반례·음성 결과·대안 기전·다음 반증 시험은 해당 장에 쓴다.
8. subagent는 Git을 발행하지 않고 main에 변경 manifest를 인계한다. 마지막 메시지에 `CE_RUN=_workspace/ce/<run-id>` 한 줄을 남긴다.
