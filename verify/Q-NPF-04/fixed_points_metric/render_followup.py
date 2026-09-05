"""Standalone figures from frozen results, without rereading neural responses."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    targets=[HERE/name for name in ('clamp_predictions.png','clamp_predictions.svg','differential_transfer.png','differential_transfer.svg')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Preserve previous figures')
    vc=json.loads((HERE/'allen_testpulse_model_result.json').read_text(encoding='utf-8'))
    ic=json.loads((HERE/'allen_crossclamp_result.json').read_text(encoding='utf-8'))
    diff=json.loads((HERE/'allen_differential_transfer_result.json').read_text(encoding='utf-8'))
    cells=sorted(vc['cells'],key=lambda c:c['device'])
    fig,axes=plt.subplots(5,2,figsize=(11,12),sharex=True,constrained_layout=True)
    for row,cell in enumerate(cells):
        trace=cell['traces']['same_holding'];ax=axes[row,0]
        ax.plot(trace['time_ms'],trace['mean_current_pA'],color='#202020',label='Observed mean')
        ax.plot(trace['time_ms'],trace['mean_rc_pA'],color='#1478b8',label='Fixed RC prediction')
        ax.plot(trace['time_ms'],trace['mean_resistor_pA'],color='#d58226',linestyle='--',label='Static resistance')
        ax.set_ylabel(f"Cell {cell['cell_id']}\nCurrent (pA)")
        ax=axes[row,1];rr=[r['trace'] for r in ic['records'] if r['cell_id']==cell['cell_id']]
        for key,color,style,label in [('voltage_mV','#202020','-','Observed mean'),('rc_mV','#1478b8','-','Fixed VC-derived prediction'),('static_mV','#d58226','--','Static resistance')]:
            ax.plot(rr[0]['time_ms'],np.mean([r[key] for r in rr],axis=0),color=color,linestyle=style,label=label)
        ax.set_ylabel('Voltage change (mV)')
        for ax in axes[row]:
            ax.axvspan(15.84,25.84,color='#777777',alpha=.08)
            ax.axhline(0,color='#aaaaaa',linewidth=.5)
            ax.grid(alpha=.15);ax.set_xlim(8,41)
    axes[0,0].set_title('VC: same-holding holdout sweeps 3-4')
    axes[0,1].set_title('IC: unrefitted predictions, sweeps 10-15')
    axes[0,0].legend(fontsize=8,loc='lower right');axes[0,1].legend(fontsize=8,loc='lower right')
    for ax in axes[-1]:ax.set_xlabel('Time from sweep start (ms)')
    fig.suptitle('Fixed neuronal identities: measurement-model prediction\nMouse VisP, experiment 4863; waveform evidence only, no spatial metric established',fontsize=13)
    fig.savefig(targets[0],dpi=170);fig.savefig(targets[1]);plt.close(fig)

    matrices=[];titles=['Training: -20 pA (sweep 10)','Positive holdout (sweep 11)','Negative holdout (sweep 12)']
    for sweep in (10,11,12):
        r=next(x for x in diff['sweeps'] if x['sweep']==sweep)
        u=np.array(r['input_matrix']);v=np.array(r['voltage_matrix'])
        # Display each response divided by its own source current, not refitting the prediction.
        z=v/np.diag(u)[None,:]*1000
        matrices.append(np.ma.array(z,mask=np.eye(5,dtype=bool)))
    limit=max(float(np.max(np.abs(z.compressed()))) for z in matrices)
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for ax,z,title in zip(axes,matrices,titles):
        heat=ax.imshow(z,cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set_xticks(range(5),[str(c['cell_id']) for c in cells],rotation=45,ha='right')
        ax.set_yticks(range(5),[str(c['cell_id']) for c in cells])
        ax.set_xlabel('Stimulated cell');ax.set_ylabel('Measured cell');ax.set_title(title,fontsize=10)
    fig.colorbar(heat,ax=axes,label='Window voltage / current (MOhm)',shrink=.8)
    fig.suptitle('Cross-cell responses at fixed positions\nDiagonal omitted; colors are effective responses, not anatomical connections',fontsize=12)
    fig.savefig(targets[2],dpi=180);fig.savefig(targets[3]);plt.close(fig)
    print('FIGURES',*[p.name for p in targets])


if __name__=='__main__':main()
