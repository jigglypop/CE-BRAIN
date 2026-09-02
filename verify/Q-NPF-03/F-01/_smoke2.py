import numpy as np, time
import calib_power as C
t0=time.time(); wp=C.prepare_world("true", C.SEED); print("prep",round(time.time()-t0,1))
print("TRUTH learn", {k:round(v,4) for k,v in C.truth(wp).items()})
rng=np.random.default_rng(C.SEED)
t0=time.time(); pools=C.one_rep(wp,"true",rng,"learn"); print("rep",round(time.time()-t0,2),"mice",len(pools))
r=C.boot(pools,rng); print("boot", {k:(round(v,4) if isinstance(v,float) else v) for k,v in r.items()})
