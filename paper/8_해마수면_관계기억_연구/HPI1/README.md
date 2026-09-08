# HPI-1 게시본: 이력조건부 주소와 예측 정보기하

2026-09-09. 이 디렉터리는 첨부 `CE_BRAIN_HPI1_history_predictive_geometry_20260909.zip`의 실행 소스와 자료를 보존하는 입구다. 원래 연구는11마리 CA1 학습 진행의 저자 공개 요약 재분석과, 같은 HMM에서 문맥복원·미래분포·정보기하를 계산하는 합성 기준이다. 원신경자료 적합이나 인간 뇌 알고리즘 증명은 아니다.

## 1. 보존한 결과와 한계

처음 무작위 전이를120회 EM으로 학습한8조건 중4조건은 두 문맥을 구별하지 못했다. 완결된 과거 에피소드의 prefix와 미래 suffix분포로 기존 감각대응 슬롯을 초기화하자 두 기록의 조회는 해결됐다. 이것은 평가 미래 유출은 아니지만 생물학적인 온라인 국소 규칙도 아니다. 입력 단서가 사라지면 두 보상 확률은.5/.5다. 같은 현재감각이라도3단계 뒤의 미래분포는 다를 수 있다.

저자 공개 11마리×3구간 수치에서 평균 정규화 분리시점은(.40977341,.58995359,.01128401)이었다. Pre-R1−Pre-R2의 짝지은 t검정 p=.04405이나 부호검정 p=.22656이며3마리의 순서는 반대다. 0값과 정규화 시점을 물리적0초로 읽지 않는다. 저자 모델 시뮬레이션은 동물 표본으로 합산하지 않는다.

## 2. 출처

Sun,Winnubst,Natrajan et al. Learning produces an orthogonalized state machine in the hippocampus. Nature640,165–175(2025). DOI10.1038/s41586-024-08548-w. 저자 코드 `sprustonlab/OSM_Paper_Figures`의 커밋 `c1d1788b54c737efe24402e02762eee10da0d0d7`, `fig_4/fig_4j_decorr_order.ipynb`의 수치 literal이다. 전체 노트북 hash 대조나 원칼슘영상의 재분석은 아니다. 출처 정보는 [자료](data/author_thresholds.json)에 들어 있다.

CSCG는 기존 모형 계열이다. DOI10.1038/s41467-021-22559-5. 이번 code를 새 생물학 기전의 최초 발견으로 부르지 않는다. 첨부 CE 우주식은 같은 함수에서 반응을 함께 도출한다는 동기이며, 그 물리 결과를 이 모형이 검증한 것은 아니다.

## 3. 재현과 게시 범위

이번 게시 전에 원본 manifest37개 전부가 일치했고,22개 테스트 및 주실행·보강을 재실행했다. 주결과와 보강결과는 원첨부와 byte일치했다. 고정 신경슬롯의 선형 경로식도 함께 보존한다.

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest discover -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 python run.py
OPENBLAS_NUM_THREADS=1 python refine.py
OPENBLAS_NUM_THREADS=1 python validate.py
OPENBLAS_NUM_THREADS=1 python verify_paths.py
```

실행 결과파일은 위 명령으로 다시 생성한다. Git에는 원본 실행코드·조건·자료 및 [요약](SUMMARY.json)을 게시하며, 과거 큰 전체 JSON·실패로그·원문 원고는 첨부 ZIP에 남긴다. 소스 동일성은 [게시 출처](PUBLICATION.json)에 기록한다. 원문 요약의 git_write_performed=false는 과거 실행의 상태이며, 이번 게시 상태는 새 배포 기록과 커밋으로 구분한다.

온라인 학습과 미래열 계산량의 후속 보강 HPI-2는 이번에 별도로 실행했지만 소스 쓰기가 연결 도구의 보안 판정 오류로 차단됐다. HPI-2는 대화의 배포 패키지에만 보존하며 이 Git 디렉터리에 포함하지 않는다. 원래 HPI-1의 생물학적 미완료를 HPI-2의 합성 성공으로 대체하지 않는다.
