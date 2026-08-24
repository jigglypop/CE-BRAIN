# BA-OBS-DISC1 구현과 관측 식

Status: COMPLETE

이 실행은 실제 인간 뇌 자료에서 복잡한 기하학 식을 사실로 선언하려는 시도가 아니라, 전기적 전파에서 출발한 작은 후보 식들이 시간만 쓰는 기준식보다 새로운 수신 쌍을 더 잘 예측하는지 시험한 실행이다. 결과는 D0에서 거리 감쇠를 넣은 `CABLE` 식을 골랐지만, D2의 주 분석에서 재현성 문턱을 넘지 못해 이 판본을 종료했다. 따라서 이 문서는 성공한 신경 법칙의 기술서가 아니라, 선택·예측·기각이 같은 규칙으로 연결된 음성 결과의 구현 기록이다.

## 관측 대상과 전기적 출발점

국소 선형화한 막전압 반응은 전도도 네트워크와 이온 전류의 야코비안을 묶어 짧은 시간창에서 Green kernel 또는 cable-like 감쇠 형태를 동기로 제공한다. 그러나 iEEG 전극이 읽는 값은 그 막전류 방정식 자체가 아니다. 자극 artifact, 공통 성분, reference montage, volume conduction, 잡음이 함께 섞인 관측량이다. 이 실행의 후보식은 완전한 막전류 법칙이나 축삭 전도 방정식의 추정치가 아니라, 이 관측 사슬 뒤의 **observed response kernel**을 비교하는 저차원 회귀식이다.

각 자극원 $s$, 수신 bipolar 쌍 $r$, trial half $h$, 시간 bin $k$에서 baseline scale로 정규화한 무차원 RMS 진폭 $E$를 만들고 다음 값을 예측 대상으로 삼았다.

$$
z=\log\left(E+10^{-6}\right),
\qquad x=t/(50\,\mathrm{ms}),
\qquad r=\ell/(50\,\mathrm{mm}).
$$

여기서 $t$는 bin 중심 시간, $\ell$은 두 bipolar 중심의 MNI Euclidean 거리다. $E$, $x$, $r$는 모두 무차원이며, $10^{-6}$은 로그를 위한 무차원 floor다. `mean`과 `bipolar` readout은 같은 endpoint에서 병렬로 계산했지만, bipolar가 primary이고 mean은 reference 민감도 진단이다.

## 후보식과 선택 절차

시간만 쓰는 기준식 B0는 $\widehat z=\beta_0+\beta_1\log x+\beta_2x$이다. D0에서 선택된 CABLE 후보는 다음과 같다.

$$
\widehat z=\beta_0+\beta_1\log x+\beta_2x-a r,
\qquad a\ge0.
$$

이 식의 $-ar$ 항은 점점 멀어진 수신 쌍의 관측 RMS 진폭이 감소할 수 있다는 cable/Green-kernel 동기를 담지만, $a$를 해부학적 축삭 길이·전도도·리만 계량의 계수로 해석하지 않는다. 함께 비교한 15개 후보에는 고정·자유 effective shape exponent를 둔 heat-kernel 절단형, 비정상 거리 지수, 지연, 대각 anisotropy proxy, 방향 보정, bi-exponential 파형형이 포함됐다. 이들은 물리적으로 그럴듯한 상상 목록이 아니라, 사전에 고정한 유한 문법이다.

자료는 OpenNeuro `ds003708`의 단일 epilepsy 환자, 6 mA CCEP, 적격 255 epoch로 제한했다. 선행 BA-OBS-ID3가 endpoint를 계산하지 않은 151개 unordered receiver-pair를 거리 층화·signal-independent hash로 D0/D1/D2/D3=`24/48/39/40`으로 나눴다. 이 실행은 ID3의 observed-magnitude 상호성 proxy를 다시 시험한 것이 아니라, endpoint-blind pair pool에서 시간·거리 후보식의 순차 예측을 새로 시험한 BA-OBS-DISC1이다.

D0에서는 각 후보를 여섯 fold와 두 trial half를 교차해 Huber loss로 평가했다. bipolar의 상대 개선도는 $I=1-\mathcal L_{\rm candidate}/\mathcal L_{\rm B0}$로 정의했다. CABLE은 $I_{\rm bip}=0.05211328272681981$, $I_{\rm mean}=0.08361287750306079$, bipolar 6 fold 중 4회 승리로 선택됐다. 이는 24쌍 발견 부분집합의 모델 선택일 뿐, held-out 확인이나 생물학적 증명이 아니다.

## 동결과 재현 경로

실행 전 synthetic heat-generator 회복, geometry-null false-selection, common-reference control, hash/길이 fail-closed, downstream barrier를 같은 코드 경로로 확인했다. 이후 코드 SHA-256 `af70dc054714fccc496bd50a8e25139bd7e4b28dc7a5ddd3acc7a008a36bd8da`, source VersionId/ETag, split manifest, 후보 문법, window, bounds, loss, threshold를 동결했다. 원천은 OpenNeuro 객체의 version-bound range 255개이며, source-cache·split·fixture·D0·D1·D2 receipt가 앞 단계의 hash와 code identity를 연결한다. 그러므로 D2 실패 뒤 같은 판본에서 식·창·문턱을 고쳐 D3을 여는 일은 허용되지 않는다.

이 구현이 검증하지 않은 범위도 명확하다. 단일 환자의 관측 CCEP 결과는 ambient 또는 무한차원 리만 계량, 해부학적·축삭 geodesic, 의식, 자아, 해마 hash, AGI를 검증하거나 반증하지 않는다.
