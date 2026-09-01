# CE-NPF 대체 생물자료 D7 Ottenheimer 2023 자료획득·무결성 결과

## 목표·계보·현재 판정

- 계보: `ALT_BIO_D7_OTTENHEIMER2023`
- 최종 목표: 성체 동일세포의 장기 기능 앵커와 학습 중 기능 표현 변화가 함께 존재하는지를 실제 종단 칼슘영상으로 판별한다.
- 이번 하위 목표: 공식 자료 바이트와 저자 코드 판본을 확보하고, 생물 endpoint 전에 출처·무결성·내부 형상을 잠근다.
- 필요한 이유: 다운로드 또는 ROI 등록 오류를 생물학적 실패나 성공으로 잘못 세지 않기 위해서다.
- 현재 판정: 획득 단계는 `D7_SOURCE_ACQUIRED_INTEGRITY_PASS / EVENT_SCHEMA_PASS /
  REGISTRATION_PREFLIGHT_PASS`; 후속 일회성 endpoint는
  `D7_COMPONENT_CONJUNCTION_NOT_SUPPORTED`로 완료됐다. 상세 수치는
  [`동일세포 앵커·학습표현 결과 v1`](CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_동일세포앵커_학습표현_결과_v1.md)에 둔다.

이 문서는 자료 획득 영수증이다. 장치 준비와 무결성 통과는 가설 지지 결과가 아니다.

## 공식 원자료 정본

- 논문: Ottenheimer et al., *eLife* 2023, `https://elifesciences.org/articles/84604`
- Figshare article DOI: `10.6084/m9.figshare.21365598.v1`
- Figshare article ID/version: `21365598`, version `1`
- 라이선스: `CC BY 4.0`
- 파일: `Imaging.zip`
- Figshare file ID: `37918065`
- 공식 내려받기 URL: `https://ndownloader.figshare.com/files/37918065`
- 로컬 경로: `data/external/ottenheimer_2023_figshare_21365598/Imaging.zip`
- 공식 크기: `3,723,747,863` bytes
- 실제 크기: `3,723,747,863` bytes
- 공식 MD5: `6085f775f1ea3a85505c55aafaf242bb`
- 실제 MD5: `6085f775f1ea3a85505c55aafaf242bb`
- 독립 로컬 SHA-256: `47ffe1933713f53be720d85023f75c6f487faa8ee39a46ad0af63e3801bc4bd9`

다운로드는 Range GET 구간을 연결해 수행했다. 구간 이름의 시작·끝 바이트가 `0`부터
`3,723,747,862`까지 빈틈과 중복 없이 이어지고 합계가 공식 크기와 같음을 검사한 뒤
조립했다. 조립 중간파일은 MD5가 공식값과 일치한 경우에만 `Imaging.zip`으로 승격했다.

## ZIP 전수 무결성

- entry 수: `225`
- 최상위 경로: `Imaging/` 하나
- compressed member 합: `3,723,717,393` bytes
- uncompressed member 합: `5,853,280,753` bytes
- `Fall.mat`: `40`
- `*ROImasks.npy`: `24`
- Python `zipfile.ZipFile.testzip()` 결과: `None`
- 판정: 모든 member CRC 통과

다운로드 구간 임시 디렉터리에는 정본 ZIP과 중복인 약 3.72 GB가 남아 있다. 안전 정책이
recursive 삭제 명령을 차단했으므로 우회 삭제하지 않았다. 이것은 정본의 일부가 아니며
endpoint 입력에도 포함하지 않는다.

## 저자 코드 정본

- GitHub tag: `v2.0`
- tag commit: `d06d9c8d1674a791327b3357d2dd683d9dd0e5e0`
- 로컬 배포 ZIP:
  `data/external/ottenheimer_2023_figshare_21365598/ottenheimer-et-al-2022-v2.0.zip`
- 크기: `78,852` bytes
- SHA-256: `594ec93c6d1665dc6e00653e4e6afd74188fd5c96d31efda0dd5148711e35221`
- 해제 경로:
  `data/external/ottenheimer_2023_figshare_21365598/code_v2.0/ottenheimer-et-al-2022-2.0`

## 공개 형상과 고정 코호트

공식 ZIP member와 저자 `imagingAcquisition.m`을 활동 endpoint와 무관하게 검사했다.

- mice: `PL01, PL02, PL03, PL08, PL10, PL11, PL15, PL16`
- sessions: 각 mouse의 `o1d1, o1d2, o1d3`
- 동일세포 수: 각각 `55, 55, 33, 20, 40, 64, 39, 65`, 합계 `371`
- 동일세포 키: `(mouse, ROImasks.npy의 열 k)`
- 각 날짜의 mask 배열은 `(2,N_m)`이고, 세 날짜에 걸쳐 같은 열 순서가 같은 수동 추적
  triplet을 뜻한다.
- 5 mice `PL08, PL10, PL11, PL15, PL16`에는 추가 odor-set 자료와 `d3c/Fall.mat`가
  있으나 D7의 주 endpoint에는 쓰지 않는다.

## event와 MAT header 사전검사

분석계약 v1을 쓴 뒤, 신경활동값을 열지 않고 24개 `Fall.mat`의 header와 event-only
값을 검사했다.

- `F,Fneu,spks`는 각 session에서 같은 `(n_roi,T)` 형상이다.
- 공개 저장형상에서 `T-len(frameTimes)`는 24 session 모두 1 또는 2였다.
- trial 수 범위: 145–225.
- `cue1,cue2,cue3`는 중복 없이 `cue`의 정확한 시간순 partition이다.
- first/last 60 안 cue별 최소 trial 수는 13이고, 홀짝 fold 최소수는 6이다.
- median frame interval 범위: 약 0.066948–0.067205 s.
- cue와 lick timestamp는 기록 범위 안이다.

따라서 v1의 exact frame equality와 fold 최소 8은 공개 형상과 불일치했다. endpoint를 보기
전에 `분석계약_v1_사전스키마보정_A1.md`로 말단 neural frame 1–2개를 뒤에서 자르는
규칙과 fold 최소 6을 명시했다. endpoint 정의나 판정방향은 바꾸지 않았다.

등록-only 독립 감사에서는 원래 5 px/2 px/80% 규칙이 5 mice를 탈락시키고, 유일한
`PL08 column 10` panel-order 오류와 `PL01/o1d2`의 320.54 s frame-time 단절을 찾았다.
endpoint를 열지 않고 `분석계약_v1_등록보정_A2.md`를 추가해 해당 triplet 제외,
활동-독립 최근접·ROI-diameter·모호성·충돌 primary, 5 px/no-distance/저자-greedy
sensitivity, segment별 causal smoothing을 고정했다. 예상 primary 보존수는 mouse별
`54,52,33,17,35,62,38,63`, 총 354이다.

## 저자 코드에서 확인한 사전 위험

1. `imagingAcquisition.m:943-1019`는 수동 좌표를 `processROIs` 뒤 `stat.med=(y,x)`에
   최근접 배정한다. 활동 유사도로 세포를 다시 맞추면 안 된다.
2. `processROIs`의 edge 검사 `imagingAcquisition.m:1736`에는 `xpix==511` 대신
   `ypix==511`이 중복된 명백한 오타가 있다. D7 primary는 실제 네 경계 조건인
   `xpix in {0,511}`과 `ypix in {0,511}`을 모두 검사하는 수정판을
   쓰고, 저자 원문 판본을 고정 sensitivity로 둔다.
3. 저자 배정 코드는 충돌한 수동 좌표를 다음 후보에 강제로 넘기며 최대거리 문턱이 없다.
   D7은 거리와 모호성 문턱을 먼저 고정하고 실패 triplet을 제외한다.
4. `imagingAcquisition.m:1542`의 이른바 shuffle은 `sort(activity2(:,2))`로 만든
   결정론적 순서이고, `:1553`의 percentile 분모도 non-self 수가 아니다. D7은 전수
   within-mouse non-self midrank와 mouse-level exact sign-flip을 사용한다.

## 이번 결과가 답한 것과 답하지 못한 것

- 답함: 공식 원자료가 실제로 내려받아졌고 크기·MD5·CRC가 일치한다.
- 반증됨: 앞선 Lee/Garcia 자료처럼 자동 접근 차단 때문에 실제 분석 바이트를 얻을 수
  없다는 상태는 이 자료에는 해당하지 않는다.
- 아직 살아 있음: 성체 동일세포 앵커와 학습 관련 기능 변화의 공존 가능성.
- 아직 미확립: 출생 시 의미, 청소년기 고정 시점, `Delta W`, 전도속도 `Delta v`,
  지연 `Delta tau`, 리만계량 `Delta g`, 그리고 이 변수들의 행동 매개사슬.
- preflight 실행 당시 상태: `REGISTRATION_PREFLIGHT_PASS / ENDPOINT_NOT_RUN`. 최종 보정 runner의
  preflight는 8 mice, 원래 371열 중 primary 동일세포 triplet 354개와 유일한
  `PL01/o1d2` 320.54020125초 gap을 확인했다. 기존 preflight 영수증 SHA-256은
  `4090424d811fe29445e42c4bc2101b197c8408b98f8f8f0945703ad2669b0abb`이며, 후속
  source-lock 보강 전 준비 영수증이므로 endpoint 권한은 아니다.
- 다음 허용 행동: base+A1+A2·runner·tests·공식 archive·저자 code·고정 runtime과 최종
  preflight를 canonical path와 SHA-256으로 각각 잠그고 독립 감사를 통과할 때만
  mouse-level endpoint를 정확히 한 번 실행한다.
