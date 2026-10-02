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
