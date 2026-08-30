<!-- 도메인: ce-brain-bio -->

# BA-STAGE4 연구 계약 — 인간 CCEP 고정 도전자 E 대 독립 해부학 연결의 판별

Status: `STAGE4_ANATOMY_NOT_IDENTIFIED / E_RETAINED` (계약 동결 2026-08-30, 결과 기입 2026-08-30)

계보: BA-OBS-DISC2R (`PASS_FINAL`: 거리 감쇠 SC의 held-out 우위) → BA-STAGE3-CCEP (`STAGE3_SYMMETRIC_METRIC_CANDIDATE / SEALED`: 후보 E 고정 선정) → **BA-STAGE4 (이 계약)**. route ledger의 `BA-STAGE3-CCEP-NEXT` 재개 조건(별도 계약·source/data lock·측정/연결 모형·참가자 독립 split·해부학 기반 matched alternative의 endpoint 접근 전 동결)을 이 문서가 이행한다.

## 1. 질문과 판본 지위

시험 질문(단일): **[산출 후보]** 참가자-held-out CCEP 5-bin log-energy 응답 예측에서, 독립 규범 해부학 연결 강도가 고정 도전자 E(등방 Euclidean 감쇠)를 사전 고정 마진으로 이기는가 — 즉 응답 감쇠 구조에 거리로 환원되지 않는 해부학 성분이 식별되는가.

**판본 지위 (정직성)**: 74 participants의 응답 테이블은 DISC2R에서 전부 개봉되었으므로 이 판본도 **registered reanalysis / OUTCOME_KNOWN**이다. 새 정보는 응답과 독립으로 구축되는 해부학 입력뿐이다. 통과해도 first-use 독립 확증이 아니며, 규범(군수준) 해부학이므로 개인 백질·인과 전도로의 승격은 금지된다. `STAGE2_TRANSFER_TENSION`은 이 판본이 뒤집을 수 없다.

## 2. 데이터와 연결 모형 (endpoint 접근 전 동결)

| 입력 | 출처 (sourcer 검증 2026-08-30) | 역할 |
|---|---|---|
| 응답 endpoint 테이블 d0–d3 | 로컬, DISC2R retry run, SHA `8a999fa6…`/`8a5f8186…`/`40c3b4b3…`/`10415230…` (stage3 data-lock과 동일) | 유일한 응답 출처. Stage 3와 같은 74명·592 source·anchor 4+query 12 구조 |
| 전극 파셀 라벨 | OpenNeuro ds004080 v1.2.4 `*_electrodes.tsv` (CC0), `Destrieux_label`/`_text` 컬럼, GitHub raw 미러 | 전극→파셀 매핑. 좌표 변환 불사용 (fsaverage/MNI152 표기 불일치 위험 회피) |
| 해부학 연결 | Domhof et al. 2021 EBRAINS Destrieux-150 파셀 SC(streamline count)·PL(path length) 행렬, HCP 200명 (DOI `10.25493/NVS8-XS5`) | 독립 해부학 강도. 다운로드 시 라이선스 문구·크기·파셀 순서를 매니페스트에 동결(sourcer 의무 (a),(b)) |
| 대안 확보 실패 시 | Rosen & Halgren 2021 Zenodo `10.5281/zenodo.4060485` 군평균 행렬(CC BY)로 대체하되, HCP-MMP 재라벨 필요성을 새 연결 모형으로 동결 후 진행 | fallback |

**연결 모형 (동결)**:
1. bipolar site의 파셀 집합 = 두 contact의 유효 Destrieux 라벨 집합. 라벨 대조는 정수 인덱스가 아니라 **이름 문자열**로 하고 매핑 표를 매니페스트에 동결한다.
2. site 쌍 $(s,t)$의 해부학 강도 $f_{\rm SC}(s,t)=\log(1+\operatorname{med}_{200}\mathrm{SC}[p,q])$의 파셀쌍 평균 ($p\in\mathcal P(s),q\in\mathcal P(t)$); $f_{\rm PL}$은 군중앙 path length. 군중앙값이 정본이고 IQR은 기술 보고.
3. **[공리: 모델 선택]** 동일 파셀쌍($p=q$, 행렬 대각 미정의)은 $\mathrm{SC}[p,\cdot]$ 행 최댓값으로 대체한다. 대각=0 대체는 감도 분석으로만 병기한다.
4. 무효 라벨(비피질·결측) contact를 포함한 target은 **모든 후보에서 matched로 제외**한다. anchor 4개 미만이 된 source는 전 후보에서 제외한다. 제외 수는 연결 영수증(응답 비접촉)에 먼저 잠근다.
5. 연결 영수증은 라벨·행렬만으로 구축하며 응답 값을 읽지 않는다 (anatomy-blind linkage lock).

## 3. 후보·절차·판정 (Stage 3 프로토콜 승계)

절차 승계: 참가자 5-fold(`(participant_number-1) mod 5`), ridge $\lambda=1$, source 내 centering, train-RMS 특징 정규화, 비음수 감쇠 계수 0 하한, 4-anchor Huber($\delta=0.5$) offset 추정 후 12-query 채점, 참가자 평균 Huber loss, 4,999 bootstrap.

| 후보 | 형태 | 단순성 순위 |
|---|---|---|
| T | 시간/연령 기준선 | 1 |
| E | $-a\,\lVert\Delta x\rVert$ (고정 도전자) | 2 |
| A_SC | $+c\,f_{\rm SC}$ (해부학 단독, 비음수 $c$) | 3 |
| A_PL | $-c\,f_{\rm PL}$ | 4 |
| EA | E + $c\,f_{\rm SC}$ (결합) | 5 |

대조군 (동결):
- **PERM**: 참가자 내 파셀쌍 무작위 치환 해부학(EA 형태) — seed `20260830`, 499 치환, EA의 개선이 치환 분포 95% 초과여야 함.
- **RESID**: $f_{\rm SC}$를 거리로 회귀한 잔차만 쓰는 EA 변형 — 거리 공선성 분리. EA가 이기는데 RESID 개선 부호가 음이면 해부학 성분 주장 금지.

판정 규칙 (Stage 3 문면): 개선 인정 = 참가자 평균 개선 $\ge0.005$ **그리고** bootstrap 95% 하한 $>0$. 동률대역 $0.002$는 단순성 순위 우선.

- `STAGE4_ANATOMY_BRIDGE_SUPPORTED`: EA 또는 A_SC/A_PL이 E를 이기고, PERM 통과, RESID 부호 양.
- `STAGE4_ANATOMY_NOT_IDENTIFIED`: 어떤 해부학 후보도 E를 못 이김 — E의 지위는 불변, 규범 해부학의 추가 정보 없음으로 완결.
- `STAGE4_APPARATUS_STOP`: 라벨 매핑·행렬 무결성·제외 폭주(전 source의 50% 초과 탈락 시 STOP으로 닫고 판정하지 않음)·재계산 불일치.
- 마진·seed·후보·연결 모형·제외 규칙의 결과 후 변경은 즉시 STOP.

`CLAIM_CEILING`: registered reanalysis. 통과해도 "규범 해부학 연결이 이 관측 커널 예측에 거리 이상 정보를 갖는다"까지. 개인 해부학·인과 전도·리만 계량·의식·AGI 금지. 다음 승격은 미개봉 독립 CCEP corpus 또는 개인별 dMRI 동반 데이터에서만.

## 4. 실행 계획

1. 취득: electrodes.tsv 74명(GitHub raw, CC0) + Domhof 행렬 → `data/external/stage4/` (gitignored), SHA 매니페스트만 정본화.
2. 연결 영수증 (응답 비접촉): 매핑 표·제외 수·강도 분포 동결.
3. 구현 + focused 검사(합성 라벨-행렬 fixture 1회), endpoint 실행 1회, §5 기입.

## 5. 결과 (2026-08-30 실행, 동결 규칙 그대로)

**판정: `STAGE4_ANATOMY_NOT_IDENTIFIED`.** 어떤 해부학 후보도 고정 도전자 E를 사전 마진($\ge0.005$, bootstrap 95% 하한 $>0$)으로 이기지 못했다. 파셀 수준 규범 해부학 연결은 이 관측 커널 예측에서 **Euclidean 거리로 환원되지 않는 정보를 갖지 않는다.**

### 5.1 취득·연결 잠금 (응답 비접촉 단계)

- electrodes.tsv 74/74 (CC0, 총 988KB); Domhof `150-Destrieux.zip` 132,605,861 bytes, SHA-256 `fcd4f122ad26e897f65b4537012b851b00f832c8ea0c778e19f7d574b022e812`, 라이선스 CC BY 4.0 + HCP Open Access 약관 (기술서 확인, sourcer 의무 (a) 해소). 원본은 gitignored `data/external/stage4/`.
- 파셀 순서 동결: 0-based $=75\cdot[\text{hemi}=R]+(\text{a2009s 인덱스}-1)$. 경험 검증 4종 — 반구 블록 밀도비 $10.0$, 동위쌍비 $17.9$, 최대 파셀(G_front_sup) landmark idx $15/90$, precentral 최상위 파트너 $=$ S_central (sourcer 의무 (b) 해소; 라벨명은 `G&S_`↔`G_and_S_` 정규화 후 전 파일 무모순).
- 탈락(matched): target 53/9,472 (0.56%), source 8/592 — STOP 문턱(50%) 무관. 연결 영수증 SHA-256 `fe20b06b1b3cad01a790787ceb712b1335465975897fd81a8b4b0006b4966527`, `responses_read=false`.
- PERM 대조는 source 내 16-site 치환(참가자 내 최세밀 matched 단위)으로 구현했음을 명기.

### 5.2 채점 결과 (참가자 74, source 584, 참가자 평균 Huber loss)

| 후보 | 평균 loss | 대 E 개선 (mean / lo95 / 양수 참가자) |
|---|---|---|
| T | 0.29976 | — |
| **E (도전자)** | **0.28213** | E>T: $+0.01762$ / $+0.01328$ / 60/74 — **matched 부분집합에서 E 우위 재현** |
| A_SC | 0.29592 | $-0.01378$ / $-0.01774$ / 15/74 — 해부학 단독은 E보다 명확히 열세 |
| A_PL | 0.29224 | $-0.01011$ / $-0.01377$ / 19/74 |
| EA | 0.28195 | $+0.00019$ / $-0.00037$ / 44/74 — 마진 미달, CI가 0 포함 |
| RESID | 0.28195 | $+0.00019$ / $-0.00038$ — 부호 양이나 무시 가능 |

기술 관찰 (판정에 불사용): PERM 499회에서 EA 실측 평균이 전 치환보다 낮았다(`ea_below_perm_fraction=1.0`; 치환 중앙 0.28214, EA 0.28195). 즉 EA의 극미한 우위($1.9\times10^{-4}$)는 잡음 정렬이 아니라 해부학 정렬 방향이지만, 동결 마진($0.005$)의 4%에 불과해 어떤 주장도 지지하지 않는다. A_SC>T($+0.0038$, lo95 $+0.0007$)도 마진 미달의 기술 관찰로만 남긴다.

### 5.3 증거·재현

결과 SHA-256 `fbce6737e43f608acc0cb443e888f28058c62e4fd8042c43f8a83d7a4b30c14a` (runtime 174s). 러너 `examples/brain/ba_stage4_linkage.py`·`ba_stage4_screen.py` (결정론; zip은 §5.1의 URL·SHA로 재취득). Stage 3 채점기와의 T/E 특징 비트 동일성 검사 통과.

### 5.4 지위와 재개 조건

- **보존**: E의 지위 불변 (matched 부분집합에서 우위 재현). "군수준 파셀 해부학은 이 endpoint에 추가 정보 없음"은 후속 경로의 음성대조군이다.
- **경계**: 이 판정은 (i) 군평균(개인 아님) 해부학, (ii) Destrieux 150 파셀 해상도, (iii) 이 관측 커널 endpoint에 한정된다. 개인 백질·세밀 해상도에서의 해부학 정보를 반증하지 않는다.
- **재개 조건**: (i) 개인별 dMRI 동반 iEEG corpus에서 개인 해부학으로 같은 판별을 새 계약으로, 또는 (ii) 파셀보다 세밀한(정점·트랙 수준) 규범 해부학과 새 연결 모형으로. 이 corpus·이 행렬 위에서의 연결 모형 재조정(대각 규칙·파셀 집계·변환 재선택)은 outcome-informed이므로 금지.
- route ledger의 `BA-STAGE3-CCEP-NEXT`(`STAGE4_UNAUTHORIZED`) 행은 이 계약의 실행으로 소진되었고, 이 문서가 그 정규화의 정본이다 (_workspace 원장은 읽기 전용 정책).
