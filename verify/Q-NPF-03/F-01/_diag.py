import numpy as np, importlib
import calib_power as C
def truth(sig_d, dw, vfac, gain, nu=None):
    C.SIG_D=sig_d; C.LEARN_DW=dw; C.LEARN_VFAC=vfac; C.LEARN_GAIN=gain
    if nu is not None: C.NU_G=nu
    wp=C.prepare_world("true", C.SEED)
    t=C.truth_lambda(wp); return {k:round(v,4) for k,v in t.items()}
base=dict(sig_d=0.08,dw=0.18,vfac=1.25,gain=1.30)
print("base       ", truth(**base))
print("no jitter  ", truth(0.0,0.18,1.25,1.30))
print("gain only  ", truth(0.08,0.0,1.0,1.30))
print("both clean ", truth(0.0,0.0,1.0,1.30))
print("clean nu.02", truth(0.0,0.0,1.0,1.30,nu=0.02))
print("clean nu.15", truth(0.0,0.0,1.0,1.30,nu=0.15))
