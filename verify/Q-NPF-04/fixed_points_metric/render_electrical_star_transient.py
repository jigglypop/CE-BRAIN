"""Render the already-seen-sweep RC development result without raw-data access."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from electrical_star_transient import project

HERE = Path(__file__).resolve().parent
result = json.loads((HERE/'electrical_star_transient_result.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes = plt.subplots(2,2,figsize=(12,8),layout='constrained')
for ax,label,title in [(axes[0,0],'cross','All 12 cross directions'),(axes[0,1],'direct','Six annotated direct directions')]:
    x = np.arange(3)
    for offset,name,color in [(-.16,'cascade','#156a88'),(.16,'instant','#d98732')]:
        y = [fold['scores'][name][label]['ratio_to_zero'] for fold in result['folds']]
        bars = ax.bar(x+offset,y,width=.3,label=name,color=color)
        ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=9)
    ax.axhline(1,color='.5',linestyle=':',label='zero-response baseline')
    ax.axhline(.8,color='#963f50',linestyle='--',label='development threshold')
    ax.set(xticks=x,xticklabels=['10','11','12'],xlabel='Left-out seen sweep',ylabel='RMSE / zero-response RMSE',ylim=(0,1.23),title=title)
axes[0,0].legend(loc='lower left',fontsize=8)
ax=axes[1,0]
time=np.asarray(result['specification']['time_s'])
held=2;target=1;source=0
observed=project(np.asarray(result['records'][held]['voltage_mV']))[target,source]
predicted=np.asarray(result['folds'][held]['scores']['cascade']['prediction_mV'])[target,source]
ax.plot(time,observed,color='.45',linewidth=1,label='filtered observation')
ax.plot(time,predicted,color='#156a88',linewidth=2,label='prediction from sweeps 10, 11')
ax.axvspan(0,1,color='#d98732',alpha=.08)
ax.set(xlabel='Time from current onset (s)',ylabel='Filtered voltage (mV)',title='Example: device 4 to device 1, seen sweep 12')
ax.legend(fontsize=8,loc='upper right')
ax=axes[1,1]
for device,own in zip(result['specification']['devices_center_then_leaves'],result['folds'][0]['model']['own']):
    candidates=own['candidates']
    minimum=min(row['mse'] for row in candidates)
    ax.plot([1000*row['tau_s'] for row in candidates],[row['mse']/minimum for row in candidates],marker='o',label=f'device {device}')
ax.set(xscale='log',xlabel='Candidate own-response pole (ms)',ylabel='Training MSE / grid minimum',title='Own-pole profile: training sweeps 11, 12')
ax.legend(fontsize=8)
fig.suptitle('Electrical-star transient model: development gate failed\nAll responses already seen; sweeps 13-15 remain unopened',fontsize=14)
for suffix in ['png','svg']:
    output=HERE/f'electrical_star_transient.{suffix}'
    if output.exists(): raise FileExistsError(output)
    fig.savefig(output,dpi=160)
print('RENDERED')
