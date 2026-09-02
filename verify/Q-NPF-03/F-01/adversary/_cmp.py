import json
L=lambda p: json.load(open(p,encoding='utf-8'))
a=L('adversary/orig_power.json'); b=L('result_power.json')
for x,y in zip(a['rows'],b['rows']):
    d={k:(x[k],y[k]) for k in x if k in y and x[k]!=y[k]}
    print(x['world'],x['contrast'],'DIFF' if d else 'IDENTICAL', d)
for f in ('symbolic','identity'):
    A=L('adversary/orig_%s.json'%f); B=L('result_%s.json'%f)
    print(f, 'IDENTICAL' if A==B else 'DIFF')
