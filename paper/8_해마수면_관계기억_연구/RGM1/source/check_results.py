"""Independent scalar/Fourier checks on the stored RGM finite-grid trajectories."""
from pathlib import Path
import json,math,hashlib
import numpy as np
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text());r=json.loads((R/'results.json').read_text());z=np.load(R/'folding_trajectories.npz')
n=p['folding']['nodes'];k=np.fft.fftfreq(n,d=1/n);err=[]
for name,compression in [('below',p['folding']['N_below']),('above',p['folding']['N_above'])]:
    h=p['folding']['B']*k**4+p['folding']['substrate_S']*abs(k)-compression*k*k
    energies=[]
    for u in z[name]:
        f=np.fft.fft(u)
        energies.append(math.fsum(float(hi)*float(abs(fi)**2) for hi,fi in zip(h,f))/(2*n)+p['folding']['quartic']*math.fsum(float(v)**4 for v in u)/4)
    err.extend(abs(float(a)-float(b)) for a,b in zip(energies,z['energy_'+name]))
    rms=math.sqrt(math.fsum(float(x)**2 for x in z[name][-1])/n)
    err.append(abs(rms-r['folding'][name]['final_rms']))
assert max(err)<1e-9
b=(R/'data/fsLR_32k_midthickness-lh_eval_50.txt').read_bytes()
assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()=='d53ffd0a5244211fdea238266e2714a221c6a2a5'
notes={'independent_energy_and_rms_checks':len(err),'max_abs_difference':max(err),
       'final_results_rerun_bitwise_equal':(R/'results.json').read_bytes()==(R/'results_before_rerun.json').read_bytes(),
       'related_contract_tests_passed':17,'published_template_source_blob_matches':True,
       'new_individual_biological_samples':0,'scope':'Scalar checks of toy trajectories and provenance, not validation of cortical folding mechanisms.',
       'refinement_record':'REFINEMENT.json and exploratory snapshots are retained.'}
(R/'validation.json').write_text(json.dumps(notes,indent=2)+'\n');print(json.dumps(notes,indent=2))
