# CE-BRAIN Stage 3A R3 결측 관측 계약

Status: `SEALED_PRE_RESULT`

R3 schema receipt SHA-256은 `be74b966fbe664d00afd84486336fd5b3f0d08cfbc70c322f77f7f71be7e03fd`이다. 봉인 직전 R1+R2+R3 집중검사는 14개 모두 통과했다.

## 1. 계승 범위와 R2 중단

R3는 R1과 manifest SHA-256 `a4503c7bcdd75d643a43e5ac289d70ee9b0216410b017c4e9c4387fdc427a528`로 봉인된 R2의 모든 과학 규칙을 계승한다. R2는 모델 적합이나 과학 판정 전에 첫 신호 전처리에서 중단됐다. 110개 파일의 green/red trace는 뉴런별 관측 시작·종료가 달라 정상적인 `NaN` 구간을 포함한다. R2의 열 평균은 이 결측을 전 열로 전파해 모든 동물의 residual scale을 무효화했다.

R2 중단 원인 감사에서 development와 confirmation trace를 불러 각 파일의 finite 비율과 zero-variance 열 수만 확인했다. stimulus별 반응 라벨, 간선별 propagation endpoint, 후보 모델 점수나 승자는 계산하지 않았다. 그러므로 R3 manifest는 `confirmation_values_opened=true`, `confirmation_scientific_endpoints_opened=false`로 정직하게 구분한다. R3 결과의 지위는 완전 미개봉 확인셋보다 한 단계 낮은 투명한 apparatus-repair 결과다.

## 2. 허용된 결측 처리

- red→green OLS, non-stimulus 중심과 MAD는 receiver별 green·red가 모두 finite인 프레임만 사용한다.
- receiver별 OLS 표본이 16프레임 미만이면 그 receiver를 제외한다.
- 결측 z값은 보간하거나 0으로 대체하지 않고 `NaN`으로 유지한다.
- 각 stimulus×receiver 간선은 baseline `[-10,-2]`와 response `[stop+1,stop+10]`에 각각 finite z가 8프레임 이상일 때만 적격이다.
- source self-response도 같은 finite gate를 통과해야 한다.
- 적격 간선에 대한 기존 연속 2-frame threshold, 모델, 분할, bootstrap, 결정 규칙은 바꾸지 않는다.

## 3. 봉인 규칙

R3 manifest는 R1·R2의 봉인 파일과 R3 코드·테스트·계약을 모두 해시로 고정하며 별도 artifact 디렉터리를 사용한다. 추가 실패 시 덮어쓰지 않는다.
