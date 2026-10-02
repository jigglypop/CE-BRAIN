# CE-BRAIN Pattern-Jet real-data validation

`PATTERN_JET_EQUATION.md`는 후보식, `REAL_DATA_VALIDATION.md`는 실제 생물자료로 가능한 범위의 판정,
`validate_real_data.py`는 재계산 코드, `results.json`은 이번 실행 결과다.

현재 상태: **필요조건 일부 지지 / K>1 직접 검증 미완료**.

실행 예:

```bash
python validate_real_data.py --bergmann-csv data/all_KC_values.csv --output results.json
```

Bergmann CSV는 저자 공개 원본 Git blob
`965d7e038fa23ba4226cda865d8802157f0d18c8`만 허용한다.
Sun Figure 4j의 11마리 배열은 저자 notebook의 고정 커밋 값을 전사했다.


## 다음 단계: K>1 최소차원 스크린

`rank_test.py`는 Bergmann 2026의 31°C `TRPA-ctrl` 6-region 변화량에 대해
nested leave-one-fly-out으로 rank-1과 rank-2 latent state를 비교한다.

실행:

```bash
python rank_test.py --csv data/all_KC_values.csv --output rank_results.json
```

현재 결과는 rank-1 RMSE 0.275576, rank-2 0.273378로 **0.80% 개선**이며,
개체별 6/9 개선(sign test p=0.5078125)이라 **K>1 채택 근거로 쓰지 않는다**.
정적 region 자료이므로 temporal synapse cascade의 직접 검증은 여전히 남아 있다.
