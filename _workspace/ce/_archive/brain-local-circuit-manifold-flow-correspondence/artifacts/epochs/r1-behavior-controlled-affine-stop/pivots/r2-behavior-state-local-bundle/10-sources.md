# R2 출처 잠금

Status: COMPLETE

Access date: 2026-08-27 Asia/Seoul

이 레인은 R0/R1에서 이미 잠근 DANDI 자산을 재선택하지 않고 R2에서 달라진
행동 chart와 시간축 해독에 필요한 출처만 대조했다. DANDI `001695`의 asset이나
outcome은 열지 않았다.

| Evidence ID | 양 | 저장소 값 | 원 출처 값 | 기준선 상태 | 영향 |
|---|---|---|---|---|---|
| E-R2-001 | 개발 자료 identity | DANDI `001701@0.260120.0303`, DOI `10.48324/dandi.001701/0.260120.0303`, asset UUID `3f3d0b16-9b3e-42ac-a5e6-327829df1116`, 12,967,760 bytes, SHA-256 `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3` | DANDI immutable version과 공식 asset metadata에 결박된 predecessor receipt | `VERIFIED_INHERITED` | R2 실행 직전 whole-byte 크기와 SHA-256이 다시 일치해야 scoring 가능 |
| E-R2-002 | implicit TimeSeries 시간축 | `starting_time+k/rate`; seconds와 Hz | NWB schema의 `starting_time`은 첫 표본 시각, `rate`는 sampling rate | `VERIFIED` | Position과 CompassDirection clock이 다르거나 metadata가 없으면 fail-closed |
| E-R2-003 | 행동 객체 의미 | `Position/position` 2D와 `CompassDirection/head direction` | NWB behavior schema에서 Position은 SpatialSeries 위치, CompassDirection은 방향 theta SpatialSeries | `VERIFIED_INHERITED` | unit metadata를 읽어 degree는 radian으로 변환하고 radian만 직접 삼각함수에 사용 |
| E-R2-004 | 생물 기준선 지위 | extracellular point event와 first-order population predictor | DANDI/NWB는 spike event 관측을 지지하지만 full VAR은 세포 기전식이 아닌 통계 기준선 | `BOUNDARY_VERIFIED` | R2 결과를 생물학적 회로 법칙이나 인과 기전으로 승격 금지 |
| E-R2-005 | asset 접근 | per-asset HTTPS download 후 local hash | DANDI 공식 access 문서가 per-asset download를 지원 | `VERIFIED` | 임시 NWB는 계산 뒤 삭제하고 aggregate만 보존 |

## 공식 출처

- DANDI 001701 immutable release: `https://doi.org/10.48324/dandi.001701/0.260120.0303`
- DANDI asset API: `https://api.dandiarchive.org/api/dandisets/001701/versions/0.260120.0303/assets/3f3d0b16-9b3e-42ac-a5e6-327829df1116/`
- DANDI data access: `https://docs.dandiarchive.org/user-guide-using/accessing-data/downloading/`
- NWB schema 2.11.0 TimeSeries/behavior definitions: `https://nwb-schema.readthedocs.io/en/latest/format.html`

## 판정

P0와 P1은 없다. source lane 환경에서는 DANDI API의 live DNS 재조회가 막혀
있었으므로 그 재조회만 P2로 남긴다. 이는 2026-08-27 predecessor metadata/hash
receipt와 모순이 아니다. 실제 scoring script가 download 직후 exact byte 수와
SHA-256을 다시 검증하므로 그 gate가 통과할 때만 계산을 진행한다.

생물 기준식은 관측 해상도의 통계 baseline이다. CE 추가항은 행동-only chart와
chart별 국소 연산자이며 `[경험식]`이다. 측정모형과 핵심 분모는 검증 가능한
상태이므로 사전구현 감사로 넘길 수 있다.
