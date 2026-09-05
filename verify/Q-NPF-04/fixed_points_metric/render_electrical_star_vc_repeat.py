"""Standalone figure for the fixed-holding VC repeatability pilot."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'electrical_star_vc_repeat_result.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
held=[s for block in r['blocks'] for s in block['scores'][2:]]
for ax,key,title in [(axes[0,0],'cross','All 12 cross directions'),(axes[0,1],'direct','Six annotated direct directions')]:
    x=np.arange(6)
    for offset,name,color in [(-.2,'repeat','#156a88'),(0,'symmetric','#d98732'),(.2,'shifted_sham','#92999e')]:
        values=[s['models'][name][key]['ratio_to_zero'] for s in held]
        ax.bar(x+offset,values,width=.19,label=name,color=color)
    ax.axhline(.8,color='#963f50',linestyle='--',label='necessary threshold')
    ax.axhline(1,color='.4',linestyle=':')
    ax.axvline(2.5,color='.7',linewidth=1)
    ax.set(xticks=x,xticklabels=[str(s['sweep']) for s in held],xlabel='Held sweep: 2-4 at -70 mV; 7-9 at -55 mV',
           ylabel='RMSE / zero-response RMSE',title=title)
axes[0,0].legend(fontsize=8,loc='best')
time=np.asarray(r['time_s'])*1000
for ax,block in zip(axes[1],r['blocks']):
    target,source=1,0
    template=np.asarray(block['training_template_pA'])[target,source]
    sham=np.asarray(block['training_sham_template_pA'])[target,source]
    traces=np.array([r['records'][s]['aligned_current_pA'][target][source] for s in block['held']])
    for index,trace in enumerate(traces):ax.plot(time,trace,color='.6',alpha=.5,linewidth=.8,label='individual held sweep' if index==0 else None)
    ax.plot(time,template,color='#156a88',linewidth=2,label='fixed training mean')
    ax.plot(time,sham,color='#92999e',linestyle='--',linewidth=1,label='shifted sham mean')
    ax.axvspan(1.3,1.8,color='#963f50',alpha=.12)
    ax.set(xlim=(-5,20),xlabel='Time from actual / sham onset (ms)',ylabel='Baseline-subtracted current (pA)',
        title=f"Device 4 to 1, holding {block['nominal_holding_mV']} mV")
axes[1,0].legend(fontsize=8,loc='best')
fig.suptitle('Fixed-neuron VC pilot: repeatability of large-command cross currents\n70 mV pulse; command voltage is not calibrated membrane voltage',fontsize=14)
for suffix in ['png','svg']:
    output=HERE/f'electrical_star_vc_repeat.{suffix}'
    if output.exists():raise FileExistsError(output)
    fig.savefig(output,dpi=160)
print('RENDERED')
