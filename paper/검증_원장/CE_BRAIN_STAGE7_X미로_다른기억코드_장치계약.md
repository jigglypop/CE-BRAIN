# CE-BRAIN Stage 7 X-미로 다른 기억코드 장치 계약

Status: `BEHAVIOR_ONLY / SCORE_BLIND`

## 목표

trajectory memory 미확립 뒤의 대체 분기에 필요한 행동 event를 신경 endpoint 없이 고정한다. 이 계약은 기억 가설을 채점하지 않고, DANDI 001701에서 다음 원격 팔 선택 event를 재현 가능하게 추출할 수 있는지만 판정한다.

## 입력 잠금

- DANDI 001701의 이미 열린 두 development NWB만 사용한다.
- 파일명·크기·SHA-256은 `CE_BRAIN_STAGE7_DANDI001701_X미로_장치감사.md`를 따른다.
- unit 수는 schema 확인에만 쓰고 `/units/spike_times`와 `/units/spike_times_index`는 읽지 않는다.

## 위치 규칙

1. 각 축의 유효 위치 1·99 percentile을 각각 0·1로 정규화한다.
2. 네 모서리를 west-south, west-north, east-south, east-north endpoint로 둔다.
3. 정규화 거리 0.18 이내에서 0.20초 이상 머문 구간만 방문으로 인정한다.
4. 같은 endpoint의 방문이 1.0초 이내에 다시 이어지면 하나로 합친다.
5. 서로 반대쪽 endpoint로 이동한 연속 방문만 cross-maze transition으로 둔다.
6. 좌표 reference `(0,0) is bottom left corner`와 논문의 과제 설명에 따라 east→west를 이후 선택예측의 primary 방향으로 고정한다. west→east는 방향 대조다.

## 장치 통과 조건

- 유효 위치 비율 90% 이상
- 네 endpoint 각각 방문 20회 이상
- east→west와 west→east transition 각각 40회 이상
- 두 development session 모두 동일 규칙으로 통과

## 금지 주장

trial table이 없으므로 이 장치만으로 correct/incorrect, sample rule, reward, retrieval, correction을 말하지 않는다. 다음 신경분석이 통과해도 claim ceiling은 `다음 원격 팔 선택 관련 코드 후보`다.
