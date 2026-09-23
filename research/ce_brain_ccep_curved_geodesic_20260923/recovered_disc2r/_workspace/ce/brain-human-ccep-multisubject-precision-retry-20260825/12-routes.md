# BA-OBS-DISC2R alternative-routes lane

Status: COMPLETE

## 채택

source manifest `clean_trials`와 exact tuple linkage. 이미 hash-locked split을 생성한 정본 행을
다시 대조하므로 가장 강한 fail-closed route다.

## 기각

- histogram을 event lookup으로 사용: predecessor 구현 실패의 직접 원인.
- split anchor를 아무 대조 없이 신뢰: 생성 단계는 검증됐지만 실행 단계 linkage 오류를 잡지
  못하므로 부족하다.
- events TSV를 다시 다운로드해 새 manifest 생성: endpoint-blind이지만 불필요한 source 판본
  증가다. 기존 source manifest가 clean trial 정본을 이미 포함한다.

과학 후보·threshold의 대안 route는 열지 않는다.
