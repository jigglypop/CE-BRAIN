# CE-BRAIN Stage 3A R2 장치 수정 계약

Status: `SEALED_PRE_RESULT`

R2 schema receipt SHA-256은 `be74b966fbe664d00afd84486336fd5b3f0d08cfbc70c322f77f7f71be7e03fd`이며 confirmation 반응값은 열지 않았다. 봉인 직전 R1+R2 집중검사는 12개 모두 통과했다.

## 1. 계승 범위

R2는 SHA-256 `a932297a588e9b90eda9d0321244d67e1598ac16edd69e57d7f4fbb2961dd838`로 봉인된 Stage 3A R1 manifest의 가설, 데이터, 분할, endpoint, 후보 모델, 임계값, bootstrap, 결정 규칙을 전부 그대로 계승한다. R1 실행은 반응 endpoint를 읽기 전 좌표 수집 중 `sub-76`의 canonical node가 0개여서 `np.stack` 장치 오류로 정지했다. 따라서 과학 결과는 생성되지 않았다.

## 2. 허용된 단일 수정

development 동물의 canonical node가 10개 미만이면 좌표 정규화와 template 구성에서 그 동물을 제외한다. R1도 정규화 뒤 10개 미만을 제외하려 했으나, 0개 입력은 정규화 함수가 먼저 실패했다. R2는 같은 기준을 정규화 전에 적용한다.

이 수정은 반응값, 전파 성공 여부, confirmation endpoint, 모델 적합값을 사용하지 않는다. 그 밖의 과학 규칙과 수치 임계값은 바꾸지 않는다.

## 3. 봉인과 중단 규칙

R2 manifest는 R1 코드·테스트·계약과 R2 wrapper·테스트·계약을 모두 해시로 고정한다. 별도 artifact 디렉터리를 사용한다. R2가 다시 사전처리·coverage·실행환경 문제로 실패하면 R2 파일을 덮어쓰지 않고 새 수정 계약 없이는 재실행하지 않는다.
