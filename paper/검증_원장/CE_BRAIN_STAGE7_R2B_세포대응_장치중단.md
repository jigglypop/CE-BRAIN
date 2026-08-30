# CE-BRAIN Stage 7 R2B 세포대응 장치 중단

Status: `SCORE_BEFORE_APPARATUS_STOP`

`ec016.17/ec016.233`은 공식 MD5, 20kHz spike, 1,250Hz LFP, LFP·position duration, 원시 위치 유효률 94.05%를 통과했다. 그러나 topdir 메타데이터의 CA1 pyramidal unit 84개 중 이 세션 cluster label에 실제 존재하는 unit은 75개였다.

**[판정]** 사전 계약의 84/84 일치 조건에 따라 `STAGE7_R2B_APPARATUS_STOP`이다. ripple·place decoding·replay score는 열지 않았다.

**[교정 허용]** 75개 실제 unit의 `.clu/.res` 길이와 label을 검증하고 최소 30개 조건을 새 계약으로 고정하는 것은 장치 정의 교정으로 허용한다. R2B 판정을 소급 변경하지 않으며 R2C라는 새 개발 실행으로만 진행한다.
