# R2 무차원 감사

Status: COMPLETE

| 코어 인자 | 원 차원 $(M,L,T,\Theta)$ | 무차원화 | 상태 |
|---|---:|---|---|
| spike count $n$과 Anscombe state | $(0,0,0,0)$ | count와 train mean/scale | PASS |
| position $p$ | $(0,1,0,0)$ | $(p-\bar p_{\rm train})/s_{p,\rm train}$ | PASS |
| velocity $v$ | $(0,1,-1,0)$ | $(v-\bar v_{\rm train})/s_{v,\rm train}$ | PASS |
| head direction의 $\sin\theta,\cos\theta$ | angle은 무차원 | degree metadata는 radian 변환; 미지원 unit은 fail-closed | PASS |
| $z,y,\phi$, chart 거리 | $(0,0,0,0)$ | 위 train-only ratios의 선형 조합 | PASS |
| ridge $\lambda$, $a_{ij}$, $q_i$ | $(0,0,0,0)$ | 입력·출력이 모두 standardized | PASS |
| NMSE와 projector distance | $(0,0,0,0)$ | 같은 차원의 제곱합 비와 orthogonal projector norm | PASS |

식의 core에 차원 있는 raw 위치나 속도가 직접 들어가지 않는다. 삼각함수 인자는
radian이고, $q_i<1$과 NMSE 1% 문턱도 무차원이다. 이는 차원 정합만 뜻하며 chart
모형의 물리적 정당성을 뜻하지 않는다.

`verify_dimensionless.py`를 Python 3.13.2로 실행해
`PASS R2 normalized state, chart distance, ridge, contraction, and NMSE are dimensionless`
를 얻었다. 저장소 전체 `tests/test_dimensionless.py`는 기본 Python 3.9.6이
프로젝트 최소 버전 3.10보다 낮아 PEP 604 annotation을 collection하지 못했다.
이 실행기 불일치는 R2 식의 차원 실패가 아니며 full checker PASS로 바꾸어 쓰지
않는다. 스킬이 지목한 `docs/참조/무차원_감사_수학.md`는 현재 tree에 없어 P2
문서 경로 불일치로 남긴다.
