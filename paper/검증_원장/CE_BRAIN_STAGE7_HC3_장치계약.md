# CE-BRAIN Stage 7 hc-3 기억궤적 장치 계약

Status: `METADATA_LOCK_PRE_REPLAY_SCORE`

## 목표 정렬

Stage 6에서 history의 예측 유용성은 두 개체에서 반복됐지만 교차축 순환의 고유 이득은 분리되지 않았다. 따라서 Stage 7은 “순환차원이 기억 용량을 만든다”를 전제로 하지 않고, 행동 중 학습된 CA1 공간 순서가 멈춤·ripple 구간에서 시간 압축된 궤적으로 다시 나타나는지만 독립적으로 검사한다.

## 자료 선택

공식 CRCNS AWS 공개 버킷 `s3://crcnsarchive/hc-3`의 metadata를 endpoint-blind로 조회했다. 선형 트랙, 위치자료, 30개 이상의 CA1 피라미드 세포를 동시에 만족하는 최상위 세션 `ec013.40/ec013.719`를 선택했다.

- behavior: `linear`, familiarity 10
- duration: 1,202.176초
- CA1 pyramidal unit: 43개
- 위치 유효률: 96.86%
- spike sampling: 20kHz
- LFP sampling: 1,250Hz, 65채널
- archive size: 373,823,610 bytes
- 공식 MD5: `32517ed8114e1b930df7925da6f2bb68`

파형 `.spk`와 feature `.fet`는 분석에 필요하지 않아 추출하지 않았다. `.clu/.res`, `.whl`, `.eeg`, `.xml/.par`만 사용한다.

## 다음 과학 계약 전 장치 문턱

모든 electrode의 `.clu` label 수와 `.res` timestamp 수가 같아야 한다. LFP·위치·metadata duration은 0.1초 이내로 일치해야 한다. 적격 CA1 피라미드 세포가 30개 미만이거나 위치 유효률이 90% 미만이면 중단한다.

이 장치 계약은 ripple 수, place field, replay 순서 점수를 열지 않는다. 장치 통과 뒤 별도 R1 계약에서 ripple 검출, 행동 encoding template, vector 대 trajectory 대조와 판정 문턱을 고정한다.

