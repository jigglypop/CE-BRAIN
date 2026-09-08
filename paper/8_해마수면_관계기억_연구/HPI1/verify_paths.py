from pathlib import Path
import json
import numpy as np
from path_geometry import path_metric
rng=np.random.default_rng(202609091);errors=[]
for _ in range(32):
    n=5;d=2;c=3;H=4
    A=rng.normal(size=(n,n));A*=.7/max(abs(np.linalg.eigvals(A)))
    B=rng.normal(size=(n,d));C=rng.normal(size=(c,n));E=rng.normal(size=A.shape)*.1
    Q=rng.normal(size=(c*H,c*H));S=Q@Q.T+np.eye(c*H)
    G,dG=path_metric(A,B,C,S,H,E);eps=1e-5
    plus=path_metric(A+eps*E,B,C,S,H)[0];minus=path_metric(A-eps*E,B,C,S,H)[0]
    errors.append(float(np.max(abs(dG-(plus-minus)/(2*eps)))))
assert max(errors)<1e-7
out={'supplied_linear_systems':32,'horizon':4,'fixed_neuron_slot_count':5,'maximum_path_metric_derivative_error':max(errors),'new_biological_samples':0,
     'scope':'Ordered propagation and full Gaussian covariance; no fitted synapses, chemistry, human curvature or nonlinear stability claim.'}
(Path(__file__).parent/'path_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
