<!-- 도메인: ce-brain-bio -->

# BA-SRM14 연구 계약 — anchor 충분성 규칙의 소비 구조 재유도 (개발 판본)

Status: `LOCKED_PRE_JUDGMENT` (2026-08-30)

계보: BA-SRM13 (`SOURCE_ROOTED_INPUT_STOP_V2`, 21/22) → **BA-SRM14 (이 계약)**.

## 1. 판본 지위 선언 (정직성 조항)

이 판본은 SRM13의 recording별 counts를 본 뒤 충분성 규칙을 재유도하므로 **outcome-informed 개발 판본**이다. 유도 근거는 관측 counts가 아니라 **SRM7 §8·§10의 endpoint 소비 문면**이며, 실데이터가 고정되어 합성 판본과 같은 새 seed 검증이 불가능하므로 이 판본의 통과 지위는 "입력 계약 성립(개발)"을 넘지 않는다. 과학적 판정은 여전히 봉인된 행동 endpoint(2단계)의 몫이고, 행동값은 이 판본에서도 읽지 않는다.

## 2. 규칙 재유도

SRM7 §8이 동결한 endpoint 소비 구조:

- 모델 계수는 **outer-train recording의 first-60%(=train split) anchor**로만 적합한다.
- ridge·fixed-$d$ 선택은 **outer-validation recording의 middle-20%(=validation split)**에서 한다.
- 채점은 **outer-held-out recording의 last-20%(=test split)**를 한 번 연다.
- 모든 recording은 **자기 first-60% prefix**로 무감독 feature 보정(평균·척도·$c_G$·σ)만 수행한다.

따라서 endpoint가 어떤 단계에서도 소비하지 않는 (recording 역할, split) 조합에 $\ge100$을 요구하는 것은 소비 구조에서 유도되지 않는 over-coverage다. 재유도된 충분성 규칙:

| outer 역할 | $\ge100$ anchor를 요구하는 split |
|---|---|
| train | train (계수 적합 + 자기 보정) |
| validation | train (자기 보정) 그리고 validation (선택) |
| held-out | train (자기 보정) 그리고 test (채점) |

무감독 보정이 anchor가 아닌 prefix 시점만 요구할 가능성도 있으나, 보수적으로 train split을 전 역할에 포함한다(약화가 아니라 강화 방향의 보수성).

## 3. 판정 절차와 falsifier

- 입력: SRM13 lock 영수증(SHA-256 `490bed3044bc74ffc475e5455a8372ca319c0cd18f4107bcc239cc551678752b`)의 recording별 counts **그대로** — 연산자·데이터·counts 재계산 없음, 규칙 재적용만.
- 전 recording이 §2 규칙을 통과 → `NEURAL_INPUT_LOCK_PASS_V3_DEV` — 2단계(행동 endpoint) 계약 개설 자격.
- 하나라도 실패 → `SOURCE_ROOTED_INPUT_STOP_V3` — 추가 규칙 변경 금지, 해당 recording의 결측 구조를 재개 조건으로 잠금.
- §2 표를 counts를 본 뒤 다시 고치는 행위는 즉시 STOP (이 계약의 표가 최종 문면이다).

## 4. 판정 (규칙 적용 결과)

SRM13 lock의 counts에 §2 규칙을 적용한 결과: **22/22 통과 — `NEURAL_INPUT_LOCK_PASS_V3_DEV`.**

- outer-train 11개(gcamp 7, gfp 첫 7 중 train 역할): train split 최소값 `403` (`20200130_105254`) $\ge100$.
- outer-validation 4개: `20200309_153839` train 931/validation 267, `20200310_141211` train 281/**validation 109**, `20210503_122703` 1183/340, `20210503_135244` 1398/410 — 전부 통과. SRM13의 유일 실패였던 `20200310_141211`의 test 66은 이 역할에서 소비되지 않는 split이다.
- outer-held-out 4개: `20200309_162140` train 940/test 234, `20200310_142022` 665/193, `20210503_151831` 1173/348, `20210503_154404` 1236/377 — 전부 통과.

행동 봉인 유지: `behavior_loaded=false`, endpoint 미개봉. 다음 의무: **BA-SRM15 — 2단계 행동 endpoint 계약** (SRM7 §10 문면 그대로: CE_SOFT 대 matched control 8종, $\Delta R^2>0$ 게이트, adverse control 3종, GFP nuisance panel; 측정 연산만 SRM13의 확증 robust 연산자). 그 계약이 동결되기 전에는 어떤 behavior 값도 읽지 않는다.
