# CE-BRAIN Stage 7 R2 독립세션 선택 계약

Status: `ENDPOINT_BLIND_SELECTION_LOCK`

## 목적

R1의 위치 해독 및 replay 점수를 본 뒤 같은 세션의 test endpoint에 맞춰 분석기를 고치는 경로를 금지한다. R1과 다른 `topdir`의 해마 선형 트랙 세션을 메타데이터만으로 고정하고, 아직 열지 않은 신경·위치 endpoint에서 장치 적격성을 새로 검사한다.

## 선택 규칙

1. R1 `ec013.40` topdir 전체를 제외한다.
2. behavior가 `linear`, duration이 600초 이상, position video가 있고 CA1 pyramidal unit이 30개 이상인 세션만 남긴다.
3. CA1 pyramidal unit 수가 가장 많은 topdir을 고른다. 동률이면 topdir 문자열 순서를 쓴다.
4. 선택 topdir 안에서 archive byte가 가장 작은 세션을 고른다. 동률이면 session 문자열 순서를 쓴다.

고정 결과는 `ec016.17/ec016.234`다. 메타데이터상 duration 1,045.4초, CA1 pyramidal unit 84개, archive 457,750,800 bytes이며 공식 MD5는 `3b350f3b76d7f0c903ee4afab89db9ec`다.

## 다음 게이트

다운로드 뒤 공식 MD5, LFP·spike·position 시간축, 유효 위치율, 방향별 traversal 수를 검사한다. 이 단계에서는 ripple/replay 점수를 열지 않는다. 장치가 통과한 경우에만 R1 실패를 반영한 R2 decoder 교정 후보를 **validation 구간에 한정해** 선택하고, 별도 test 및 ripple endpoint를 여는 새 계약을 작성한다.

R2 결과는 독립 동물의 개발 복제이며 최종 보편 확증이 아니다. R1의 기준을 완화해 통과시키는 용도로 사용하지 않는다.
