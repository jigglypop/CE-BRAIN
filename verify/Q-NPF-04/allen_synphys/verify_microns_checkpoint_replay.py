"""block90 checkpoint의 edge 순서와 RNG로 block91을 정확히 재현한다."""
import json
import numpy as np
import microns_constrained_swaps as base
from microns_swap_extension import STORE,validate

counts,categories=base.load_graph();initial=counts>=1
prefix=STORE/'t1_seed2026090501_block90'
checkpoint=json.loads(prefix.with_suffix('.json').read_text())
assert base.sha(prefix.with_suffix('.npz'))==checkpoint['graph_sha256']
with np.load(prefix.with_suffix('.npz'),allow_pickle=False) as saved:
    a=saved['adjacency'].copy();edges=saved['edges'].copy()
rng=np.random.default_rng();rng.bit_generator.state=checkpoint['rng_state']
accepted=checkpoint['accepted'];m=len(edges)
for i,j in rng.integers(0,m,size=(m,2)):accepted+=base.propose(a,edges,i,j,categories)
validate(a,edges,initial,categories)
actual=dict(block=91,reciprocal=int(np.sum(a&a.T)//2),original_overlap=float(np.sum(a&initial)/m),accepted=accepted)
final=json.loads((STORE/'t1_seed2026090501_block120.json').read_text())
expected=next(r for r in final['trajectory'] if r['block']==91)
assert actual==expected
print('CHECKPOINT_EDGE_ORDER_AND_RNG_REPLAY_EXACT',actual)
