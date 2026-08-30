# CE-BRAIN Stage 9 DA R4 lick 채널 장치 중단

Status: `SCORE_BEFORE_APPARATUS_STOP`

R4 계약은 event code 1 `Lick1 onset`만 행동으로 사용하도록 고정했다. D-cohort day01 의미표와 배선 빈도 감사에서 lick onset은 code 5 `Lick3 onset`에 기록되고 code 1은 0건이었다.

**[판정]** `STAGE9_DA_LICK_CHANNEL_STOP`. dopamine·학습 효과 점수 전에 발견한 장치 오류다.

R4 계약을 소급 수정하지 않는다. R5는 event meaning에 정의된 모든 lick onset code `{1,3,5}`를 합치는 새 계약으로 진행한다. 이는 결과에 맞춘 threshold 조정이 아니라 포트 번호에 무관한 행동 관측 정의다.
