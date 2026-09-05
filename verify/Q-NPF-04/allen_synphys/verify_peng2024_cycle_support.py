"""방향 변화가 가능한 실제 기록에서 비트열 완전열거로 정확 기대값 대조."""
import csv
import io
import json
import zipfile
from collections import Counter
from fractions import Fraction
from itertools import combinations,product
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
path=HERE/'peng2024_cycle_conditioning_result.json'
result=json.loads(path.read_text(encoding='utf-8'))
archive=ROOT/'data/external/peng2024_human/data.zip'
assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
audits={}
with zipfile.ZipFile(archive) as z:
    for cohort in ('er','tr'):
        rows=list(csv.DictReader(io.StringIO(z.read('data/tconnection_'+cohort+'.csv').decode('utf-8-sig'))))
        records=[]
        for record in result['results'][cohort+'_published']['records']:
            if record['orientation_support']==1:continue
            rr=[r for r in rows if r['clusterid']==record['cluster']]
            lookup={(r['cellid_pre'],r['cellid_post']):int(r['connected']) for r in rr}
            directed={(a,b) for (a,b),v in lookup.items() if v==1 and lookup[b,a]==0}
            edges=sorted(tuple(sorted(e)) for e in directed)
            assert len(edges)<=16
            nodes=sorted({a for e in edges for a in e})
            quotas=Counter(a for a,b in directed)
            triangles=[t for t in combinations(nodes,3) if all(e in edges for e in combinations(t,2))]
            distribution=Counter()
            for bits in product((0,1),repeat=len(edges)):
                graph={e if bit==0 else e[::-1] for e,bit in zip(edges,bits)}
                if Counter(a for a,b in graph)!=quotas:continue
                cycles=sum(((a,b) in graph and (b,c) in graph and (c,a) in graph)
                           or ((b,a) in graph and (c,b) in graph and (a,c) in graph) for a,b,c in triangles)
                distribution[cycles]+=1
            support=sum(distribution.values());expected=Fraction(sum(k*v for k,v in distribution.items()),support)
            assert support==record['orientation_support'] and expected==Fraction(record['expected_exact'])
            records.append({'cluster':record['cluster'],'distribution':{str(k):v for k,v in sorted(distribution.items())},
                            'variable_cycle_count':len(distribution)>1})
        audits[cohort]={'records':records,'variable_cycle_records':sum(r['variable_cycle_count'] for r in records)}
out={'verification':'PASS: exhaustive orientations of every nonunique published real graph agree with dynamic counts',
     'result_sha256':sha(path),'code_sha256':sha(Path(__file__)),'cohorts':audits}
save('peng2024_cycle_support_verification.json',out)
print(json.dumps(out,indent=2))
