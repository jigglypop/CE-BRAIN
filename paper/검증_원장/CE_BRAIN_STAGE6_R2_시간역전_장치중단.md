# CE-BRAIN Stage 6 R2 후보 시간역전 장치중단

Status: `STAGE6_STRICT_PAST_SCHEMA_STOP`

development subject `719828686`, session `754312389`, asset `5a58bf3d-a1b9-444b-8ab0-ef5478aa42a6`의 1,859,545,192-byte NWB를 공식 SHA-256 `08904e57846251d7967c5cec90b9eb3caa6f66a552c2275672389f60147cc697`과 일치시켰다.

자연영화는 900프레임 완전 반복 20회와 stimulus block 4·12를 갖지만, block 12에서 연속 frame 시작시각이 역전되는 지점이 2곳 있었다.

- frame 244→245: `7839.401899858075 → 7839.368462046439`
- frame 599→600: `7851.245053455182 → 7851.211458611537`

두 차이는 약 한 frame인 33ms 역전이다. strict-past 다음-frame 예측에서 이를 정렬·삭제하면 R1과 다른 후처리가 되므로 neural prediction score 전에 장치 중단했다. 이 개체는 Stage 6의 양성·음성 과학 결과로 세지 않는다.

