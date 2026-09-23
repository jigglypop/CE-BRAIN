# BA-OBS-DISC2R math lane

Status: COMPLETE

수학 판본은 predecessor `11-math.md` SHA
`9e3021e9fab2b267faf731415565caf82413010bfc80ee27068f502942df8c54`를 그대로 상속한다.

변경은 식이 아니라 유한 자료 index의 사상이다. split trial $e$를 source-manifest clean trial로
보내는 map

$$
L:(i,r,s,e)\mapsto
(\texttt{event\_index},\texttt{anchor\_sample\_zero\_based},\texttt{site})
$$

이 유일하고 세 성분이 모두 같아야 한다. record histogram `{"0":N}`은 $L$이 아니므로
lookup에 쓸 수 없다. 이 수정은 $x,\Delta,r,d_G,E,z$, 후보식, loss, inference를 바꾸지 않는다.
