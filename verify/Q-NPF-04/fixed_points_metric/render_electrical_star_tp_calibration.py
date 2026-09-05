"""Measured TP comparisons and an explicitly synthetic identifiability example."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from electrical_star_tp_calibration import step_current

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'electrical_star_tp_calibration_result.json').read_text(encoding='utf8'))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
colors=['#156a88','#d98732','#65945b','#963f50']
for ax,notebook_key,defined_key,title in [(axes[0,0],'peak_resistance_MOhm','defined_peak_resistance_MOhm','Peak index: target four neurons'),
        (axes[0,1],'steady_resistance_MOhm','defined_late_resistance_MOhm','Late index: target four neurons')]:
    for device,color in zip([4,1,2,5],colors):
        cells=[next(c for c in s['cells'] if c['device']==device) for s in r['matched_sweeps']]
        ax.plot(range(10),[c['inserted'][defined_key] for c in cells],color=color,marker='o',label=f'device {device}: inserted')
        ax.plot(range(10),[c[notebook_key] for c in cells],color=color,linestyle='--',alpha=.75)
    ax.axvline(4.5,color='.6',linestyle=':')
    ax.set(xlabel='Sweep: 0-4 holding command -70 mV; 5-9 -55 mV',ylabel='Effective resistance index (MOhm)',title=title)
axes[0,0].legend(fontsize=8,ncol=2)
axes[0,1].text(.03,.94,'solid: inserted TP\ndashed: nearby notebook TP',transform=axes[0,1].transAxes,va='top',fontsize=9)
ax=axes[1,0]
for is_star,color,label in [(True,'#156a88','target four'),(False,'.65','other three')]:
    cells=[c for s in r['matched_sweeps'] for c in s['cells'] if (c['device'] in [4,1,2,5])==is_star]
    ax.scatter([c['steady_resistance_MOhm'] for c in cells],[c['inserted']['defined_late_resistance_MOhm'] for c in cells],color=color,s=20,label=label)
ax.plot([60,60000],[60,60000],color='.4',linestyle=':')
ax.set(xscale='log',yscale='log',xlabel='Notebook late index (MOhm)',ylabel='Inserted late index (MOhm)',title='One late-current denominator is nearly zero')
ax.annotate('device 7, sweep 6',xy=(126.0234,52174.58),xytext=(310,18000),arrowprops=dict(arrowstyle='->'),fontsize=9)
ax.legend(fontsize=8,loc='lower right')
ax=axes[1,1]
n=7;time=np.linspace(0,10,501);g=.01*np.eye(n);cap=np.full(n,.1);u=np.full(n,-10.)
edge=np.eye(n)[0]-np.eye(n)[1]
cases=[(g,14,0,'14 MOhm series; zero reference','-'),(g,7,1,'7 MOhm series; 1 MOhm reference','--'),
       (g+.1*np.outer(edge,edge),14,0,'14 MOhm series; added gap',':')]
for network,rs,ref,label,style in cases:
    current=step_current(time,network,cap,np.full(n,rs),ref,u)
    ax.plot(time,current[:,0]*1000,label=label,linestyle=style,linewidth=2)
ax.set(xlabel='Time from common step (ms)',ylabel='Current in one port (pA)',title='Synthetic: different circuits, identical common TP')
ax.legend(fontsize=8,loc='lower right')
fig.suptitle('Fixed-neuron test-pulse calibration audit\nRecorded resistance indices exist; intrinsic resistance and metric remain unidentified',fontsize=14)
for suffix in ['png','svg']:
    path=HERE/f'electrical_star_tp_calibration.{suffix}'
    if path.exists():raise FileExistsError(path)
    fig.savefig(path,dpi=160)
print('RENDERED')
