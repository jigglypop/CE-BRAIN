import json, numpy as np
d=json.load(open('verify/Q-NPF-04/F-01/result_c1_crb.json',encoding='utf-8'))
R=d['rows']
print("configs=%d  pass_all=%d  pass_CA=%d"%(d['n_configs'],d['n_pass_all'],d['n_pass_CA']))
ge=[r['angle_deg']['gain-eff'] for r in R]
gc=[abs(r['postfit_corr']['gain-eff']) for r in R]
zd=[r['z']['delay'] for r in R]
zg=[r['z']['gain'] for r in R]; ze=[r['z']['efficacy'] for r in R]
print("gain-eff angle deg: min %.2f  median %.2f  max %.2f"%(min(ge),np.median(ge),max(ge)))
print("|postfit corr gain-eff|: min %.4f median %.4f max %.4f"%(min(gc),np.median(gc),max(gc)))
print("z_delay: min %.3f median %.3f max %.3f ; #>=2: %d"%(min(zd),np.median(zd),max(zd),sum(1 for z in zd if z>=2)))
print("z_gain min %.2f max %.2f ; z_eff min %.2f max %.2f"%(min(zg),max(zg),min(ze),max(ze)))
print()
print("=== realistic corner: mode=counts, sig_jit=0.030 (the named data has cue-onset jitter) ===")
print("%-6s %-6s %-6s | %8s %8s %8s | %7s %7s %7s | %8s"%("rho0","tau_m","v","z_gain","z_eff","z_del","ang_ge","ang_gd","ang_ed","corr_ge"))
for r in R:
    if r['mode']=='counts' and r['sig_jit']>0:
        print("%-6.2f %-6.3f %-6.2f | %8.2f %8.2f %8.3f | %7.2f %7.2f %7.2f | %8.4f"%(
            r['rho0'],r['tau_m'],r['v_axon'],r['z']['gain'],r['z']['efficacy'],r['z']['delay'],
            r['angle_deg']['gain-eff'],r['angle_deg']['gain-del'],r['angle_deg']['eff-del'],
            r['postfit_corr']['gain-eff']))
print()
print("=== best case for delay: mode=counts, sig_jit=0 (no onset jitter; oracle knows cue time exactly) ===")
for r in R:
    if r['mode']=='counts' and r['sig_jit']==0 and r['v_axon']==0.10:
        print("rho0=%.2f tau_m=%.3f v=%.2f  z=(%.2f,%.2f,%.3f) ang_ge=%.2f corr_ge=%.4f adm_eff=%s"%(
            r['rho0'],r['tau_m'],r['v_axon'],r['z']['gain'],r['z']['efficacy'],r['z']['delay'],
            r['angle_deg']['gain-eff'],r['postfit_corr']['gain-eff'],r['efficacy_magnitude_admissible']))
print()
# how much more data would the delay channel need in the realistic corner?
print("=== N multiplier needed for z_delay>=2 (info scales with trials*cells) ===")
for r in R:
    if r['mode']=='counts' and r['sig_jit']>0 and r['tau_m']==0.020:
        f=(2.0/r['z']['delay'])**2
        print("rho0=%.2f v=%.2f  z_del=%.3f -> need %.0fx more (cells*trials) = %.0f trials/phase at 354 cells"%(
            r['rho0'],r['v_axon'],r['z']['delay'],f,60*f))
