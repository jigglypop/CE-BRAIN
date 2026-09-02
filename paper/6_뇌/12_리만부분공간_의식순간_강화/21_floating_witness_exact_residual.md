# 21. floating solver witness를 exact residual로 되돌리기

## floating solver witness를 exact residual로 되돌리기

수치 solver가 출력한 역행렬을 decimal 문자열로 저장하면 출력 정밀도와
locale에 따라 원래 bit 값이 사라질 수 있다. 새 receipt는 정확히 16자리
lowercase binary64 hex를 받는다. sign `s`, exponent `e`, fraction `f`에 대해
normal 값은

$$
x=(-1)^s(2^{52}+f)2^{e-1023-52},
$$

subnormal 값은

$$
x=(-1)^sf2^{-1074}
$$

로 host float 연산 없이 exact rational로 복원한다. 예를 들어 저장된
binary64 `0.1`은 `1/10`이 아니라

$$
\frac{3602879701896397}{36028797018963968}
$$

이다. signed zero의 수치값은 0이지만 원 bit hash와 진단 count에는 부호를
보존하며, NaN과 infinity는 거부한다.

복원한 complex witness `B`는 새 정리를 거치지 않고 기존 exact 식

$$
R=I-BA_0,\qquad |R|+|B||\Delta|
$$

에 그대로 들어간다. induced 1/infinity norm이 모두 1보다 작으면 Banach
residual 인증이 성립한다. 따라서 solver가 어떤 방법으로 `B`를 제안했는지
신뢰할 필요는 없고, 나쁜 witness는 동일한 exact gate에서 실패한다.

다만 증명된 것은 `binary64_stored_value_decoding_verified=True`뿐이다.
solver algorithm, 연산별 rounding mode, hardware/BLAS, empirical matrix
provenance는 모두 거짓으로 남는다. 이는 stored value의 reproducibility를
닫은 것이지 전체 solver 실행을 인증한 것이 아니다. 정식 기록은
`_workspace/ce/brain-binary64-residual-witness-receipt-20260826/40-final-report.md`를 따른다.
