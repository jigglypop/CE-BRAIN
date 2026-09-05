"""비트 집합 교집합으로 공통 이웃 수와 분해 표를 독립 대조한다."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_common_neighbors as study


def bit_counts(a):
    outgoing=[int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little') for row in a]
    incoming=[int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little') for row in a.T]
    return incoming,outgoing


def check(a,p,c,expected):
    vectors=bit_counts(a)
    n=len(a)
    for axis,bits in zip(('input','output'),vectors):
        counts=np.zeros((6,4),dtype=int);mutual=np.zeros((6,4),dtype=int);means=np.zeros((6,4))
        for i in range(n):
            for j in range(i+1,n):
                common=(bits[i]&bits[j]).bit_count()
                group=0 if common==0 else 1 if common==1 else 2 if common<4 else 3
                b=c[i,j];counts[b,group]+=1
                mutual[b,group]+=bool(a[i,j] and a[j,i])
                means[b,group]+=p[i,j]*p[j,i]
        for row in expected[axis]['rows']:
            b,k=row['distance_bin'],row['common_group']
            assert row['opportunities']==counts[b,k] and row['mutual']==mutual[b,k]
            assert abs(row['expectation']-means[b,k])<1e-9
        for k,row in enumerate(expected[axis]['totals']):
            assert row['opportunities']==counts[:,k].sum()
            assert abs(row['residual']-(mutual[:,k].sum()-means[:,k].sum()))<1e-9


def main():
    a=np.zeros((4,4),dtype=bool);a[2,0]=a[2,1]=a[0,3]=a[1,3]=True
    before=bit_counts(a);a[0,1]=a[1,0]=True;after=bit_counts(a)
    assert all((x[0]&x[1]).bit_count()==1 for x in before+after)
    base=study.base
    result_path=study.HERE/'sgsg_common_neighbors_result.json'
    result=json.loads(result_path.read_text())
    roots,xyz,obs,_=base.source.run.shared.source.data()
    c=np.digitize(cdist(xyz,xyz),[50,100,200,400,800])
    old=json.loads((study.HERE/'joint_expected_polish_result.json').read_text())
    with np.load(base.BASE.ROOT/old['fitted_file'],allow_pickle=False) as f:p=f['p']
    check(obs,p,c,result['observed'])
    for r in result['generated']:
        name=f'{r["index"]:02}.npz'
        with np.load(base.source.STORE/name,allow_pickle=False) as f:a=f['adjacency']
        with np.load(base.STORE/name,allow_pickle=False) as f:p=f['p']
        check(a,p,c,r['summary'])
    output=dict(result_sha256=base.BASE.sha(result_path),verifier_sha256=base.BASE.sha(Path(__file__)),
                graphs_verified=65,axes_verified=2,dyads_per_graph=60031,
                direct_pair_edges_excluded_fixture=True,group_distance_rows_verified=65*2*6*4,
                method='Bitset intersection popcount, independent of matrix multiplication')
    base.source.run.shared.source.write_once(study.HERE/'sgsg_common_neighbors_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
