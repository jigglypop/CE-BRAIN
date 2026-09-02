import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd
for amp in (0.3,0.4,0.5,0.6):
    fwd.DRIVE_AMP = amp
    pk=[];pop=[]
    rng = np.random.default_rng(fwd.SEED)
    for n in fwd.CELLS_PER_MOUSE:
        c = fwd.make_circuit(n, rng)
        x = fwd.solve_x(c,(0,0,0))
        pk.append(np.exp(x.max()))
        pop.append(np.exp(x.mean(1).max()))
    print("amp=%.2f  max single-cell rate ratio p50=%.1f p90=%.1f  pop-mean ratio p50=%.2f"%(
        amp, np.percentile(pk,50), np.percentile(pk,90), np.percentile(pop,50)))
# closed-loop timescale of the population response, for the record
fwd.DRIVE_AMP=0.4
rng=np.random.default_rng(fwd.SEED); c=fwd.make_circuit(40,rng)
x=fwd.solve_x(c,(0,0,0)); p=x[0].mean(0); p=p/p.max()
t=np.arange(fwd.NFFT)*fwd.SIM_DT; i=np.argmax(p)
tail=p[i:]; j=np.argmax(tail<np.exp(-1))
print("pop peak t=%.3fs  decay tau=%.3fs"%(t[i], t[i+j]-t[i]))
