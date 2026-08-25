# BA-OBS-DISC2R 구현 기록: 연결 보정 뒤의 인간 CCEP 실행

Status: COMPLETE

## 실행의 목적

이 기록은 뇌 전체의 계량을 복원한 기록이 아니다. 사전에 고정한 다환자 인간 SPES CCEP 관측량에서, 단순한 유클리드 거리 감쇠 항이 시간·연령 기준식보다 예측을 개선하는지를 한 번의 순차 실행으로 확인한 기록이다. 실행은 “도시의 두 지점이 멀수록 소리가 작아진다”는 작은 비유에 가깝다. 그 비유가 맞더라도 도로망의 실제 전도도나 신경 축삭 경로를 안다는 뜻은 아니다. 전극이 읽은 짧은 자극 후 반응의 크기에, 거리라는 간단한 좌표가 추가 설명력을 갖는지만 묻는다.

## 선행 실행과 재시도의 경계

선행 `BA-OBS-DISC2`는 실패한 과학 결과가 아니라 실행 전 연결 검증 실패였다. D0 opening marker를 쓴 뒤 25.7 ms 안에 `sealed event/sample crosswalk mismatch`로 멈췄고, HTTP range 요청·원시 전압 decode·endpoint 계산·결과 파일은 하나도 만들지 않았다. 선행 marker와 failure record의 SHA-256은 각각 `ff4ac42a44d34c3a4438250392d042133f84dcb8ee341537a05dfcdf8a85661e`, `15e711b64cb0fe2b73aa3b1c1c8235ab80961b63e40f97fdf8969d3f686d0c1a`이다.

원인은 record의 `event_sample_crosswalk`가 event-index lookup이 아니라 sample-start와 onset의 차이를 세는 histogram이라는 점을 잘못 읽은 데 있었다. `BA-OBS-DISC2R`은 그 해석과 selected trial의 manifest 연결만 고쳤다. source/split, 수신구간, endpoint, 후보식, 최적화, permutation·bootstrap, 문턱과 주장 상한은 바꾸지 않았다. 따라서 재시도는 데이터를 보고 식을 다시 고른 실행이 아니다. 이 재시도의 run-lock SHA-256은 `d70f83387143145bb1c40258c1f1a3974c168c30c677d2f67cc5819ffdccd291`이다.

## 관측량과 식

각 trial에서 contact별 baseline median을 빼고 bipolar difference를 만들었다. 열 trial의 baseline을 합쳐 $1.4826\,\mathrm{MAD}$로 scale을 정규화하고, 열 trial 평균 파형의 다섯 시간 구간 $[10,18)$, $[18,30)$, $[30,50)$, $[50,80)$, $[80,120]\,\mathrm{ms}$ RMS를 $E$라 두었다. 분석값은 무차원 $z=\log(E+10^{-6})$이며, 같은 수신기·시간창을 자극 전 $-300\,\mathrm{ms}$로 옮긴 값은 음성 대조에만 사용했다.

시간의 무차원 좌표를 $x$라 하고, 참여자 $i$의 중심화 연령을 $\widetilde A_i$라 하면 공통 기준식은 다음과 같다.

$$
T_i^\star(x)=\beta_1\log x+\beta_2x
+\gamma_1\widetilde A_i\log x+\gamma_2\widetilde A_i x.
\tag{1}
$$

각 자극 source에는 anchor trial만으로 정한 offset을 더했다. 이 offset은 source마다 다른 자극 크기·전극 상태를 흡수하지만 query target의 거리 효과를 맞추지는 않는다. 선택 후보 `SC`는 식 (1)에 $-ar$를 더하며 $a\geq0$, $r$는 등록 좌표의 단순 유클리드 거리다. 즉 최종 적합식은 $T_i^\star(x)-ar+b_s$이고, $b_s$는 source anchor offset이다.

## 실행 순서와 apparatus

실행 전에는 74 참여자, 592 source, 5,920 선택 trial에 대해 event index, zero-based anchor, orientation, 자극 metadata가 sealed manifest와 정확히 일치하는지 확인했다. histogram 또는 anchor 하나를 바꾼 fixture는 raw request 전에 차단했고, 정상 linkage test는 3/3을 통과했다. 독립 사전 감사와 수령증을 봉인한 뒤에만 아래 명령으로 stage를 순차적으로 열고 적합했다.

```text
.codex\hooks\python.cmd python ...\artifacts\disc2r_ccep_run.py open-stage D0
.codex\hooks\python.cmd python ...\artifacts\disc2r_ccep_run.py fit-stage D0
```

각 다음 stage도 같은 `open-stage` 뒤 `fit-stage` 순서를 따랐고, 앞 stage의 사전 gate가 통과할 때만 열렸다. D0/D1/D2/D3은 환자 단위로 서로 겹치지 않는 `24/8/12/30`명, source `192/64/96/240`, target `3,072/1,024/1,536/3,840`, version-locked byte range `1,920/640/960/2,400`개를 사용했다. 합계는 74명, 592 source, 9,472 target, 5,920 range다. range receipt는 HTTP version·content range를 봉인했고, `raw_payload_persisted=false`를 유지했다. 원시 전압 payload는 저장하지 않았다.

D0 result SHA-256은 `d357dce969476f352758790c8a7cb2d212967186de9ede61765376cf94ca5919`, D1은 `9b9ff8cbcec56790975690c7934bf0a5db4e14e9efb6e64c61926796a85098f3`, D2는 `67140450e3c8f6634dda7d8516c53b36f71e976004bc81185d0782ff2d9f1b91`, D3는 `1e85eb3979b338f8927a35ce1e739468980ce1fa56f259d742577eadef6b85fa`다. 이 hash chain은 재실행이 아니라 이미 열린 stage의 정확한 산출물을 가리킨다. 뒤의 hardened v2 검증은 이 산출물을 locked manifest에 다시 묶고 적합을 재계산했지만, 원시 byte payload는 의도적으로 보존하지 않았으므로 payload digest의 내용 재해시는 새 외부 download I/O가 있어야 가능하다.

## 구현 결과의 범위

실행 apparatus는 실제 인간 자료의 관측 endpoint까지 정확히 도달했고, run-lock·marker·range·endpoint·result 연결이 완결됐다. 하지만 이 구현 사실 자체는 거리 항의 과학적 타당성도, 리만 계량도 증명하지 않는다. 그 판단은 다음 검증 기록의 사전 gate와 음성 대조를 모두 통과한 수치 비교에서만 나온다.
