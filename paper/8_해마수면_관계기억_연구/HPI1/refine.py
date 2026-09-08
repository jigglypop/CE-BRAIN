from pathlib import Path
import json,hashlib
import numpy as np
from predictive_core import *
R=Path(__file__).resolve().parent

def experiment(seed):
    m,slots=template(seed);emit=m.emission.copy();receipt=initialize_from_past_episodes(m,toy_sequences())
    ll=m.fit(toy_sequences(),iterations=10)
    answers=[]
    for seq in toy_sequences():
        b=m.posterior(seq[:5]);p=b@m.future_likelihoods(1);answers.append(float(p[seq[5]]))
    erased=m.posterior([0,None,3,3,3]);erasedp=erased@m.future_likelihoods(1)
    bA=m.posterior([0,1,3]);bB=m.posterior([0,2,3]);curve=[]
    for h in range(5):
        L=m.future_likelihoods(h);p=bA@L;q=bB@L
        curve.append({'horizon':h,'squared_hellinger_chord':hellinger_chord_squared(p,q),'mixture_fisher':mixture_fisher(p,q)})
    return {'seed':seed,'construction':receipt,'fixed_emissions_preserved':bool(np.array_equal(emit,m.emission)),
            'correct_reward_probabilities':answers,'masked_cue_reward_probabilities':erasedp[[4,5]].tolist(),
            'future_metric':curve,'final_loglik':float(ll[-1]),'transition':m.transition.tolist()}

out={'stage':'Exploratory refinement AFTER random initialization failed; not independent biological confirmation.',
     'change':'Empirical predictive-suffix classes allocate pre-existing emission-matched slots; no larger state budget or hidden labels.',
     'seeds':[201,202,203,204,205,206,207,208],
     'trials':[experiment(s) for s in range(201,209)],
     'same_two_schematic_training_sequences':True,'new_biological_trials':0}
(R/'refinement_results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in out['trials'][0].items() if k!='transition'},indent=2))
