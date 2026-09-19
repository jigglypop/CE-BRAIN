"""Show saved conditional-current scores without fitting or reselection."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np

from vc20hz_source_inputs import HERE,sha


def main():
    source=HERE/'mixed_clamp_ap_prediction_result.json'
    png=HERE/'figures/mixed_clamp_ap_prediction.png'
    receipt=HERE/'mixed_clamp_ap_prediction_figure.json'
    if png.exists() or receipt.exists():raise FileExistsError('Preserve saved figure')
    if sha(source)!='f49e06773fcc01701da16133746c68a7d678155b172786b6de71953753c5a84c':raise ValueError('Frozen prediction result changed')
    data=json.loads(source.read_text(encoding='utf-8'))
    models=('command_fixed','ap_fixed','ap_order','ap_history','ap_order_history','ap_early5ms','ap_late5ms')
    names=('Command','AP fixed','AP + order','AP + history','AP + both','AP -5 ms','AP +5 ms')
    cohorts=('within_sweep_recovery','later_50Hz','transport_20Hz','transport_100Hz')
    labels=('Recovery, same sweeps (n=5)','Later 50 Hz (n=3)','20 Hz transport (n=2)','100 Hz transport (n=6)')
    summaries={(r['pair_id'],r['model'],r['cohort']):r['equal_sweep_rmse_pA'] for r in data['summary'] if r['qc_scope']=='recording_qc_primary'}
    baseline=np.array([summaries[121566,'state',c] for c in cohorts])
    values=np.array([[summaries[121566,m,c] for m in models] for c in cohorts])
    relative=100*(values/baseline[:,None]-1)
    pairs=(121535,121551,121558,121566);aggregate={}
    for pair in pairs:
        for model in ('state',)+models:
            mses=[r['mse_pA2'] for r in data['per_sweep'] if r['pair_id']==pair and r['model']==model and r['qc_scope']=='recording_qc_primary' and r['cohort']!='train_initial']
            assert len(mses)==16
            aggregate[pair,model]=float(np.sqrt(np.mean(mses)))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,bx)=plt.subplots(2,1,figsize=(12,8.7),gridspec_kw={'height_ratios':[1.3,1]})
    heat=ax.imshow(relative,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-15,vcenter=0,vmax=15),aspect='auto')
    ax.set_xticks(range(len(models)),names);ax.set_yticks(range(len(cohorts)),labels)
    for i in range(4):
        for j in range(len(models)):
            ax.text(j,i,f'{values[i,j]:.3f}\n({relative[i,j]:+.1f}%)',ha='center',va='center',fontsize=9,color='white' if abs(relative[i,j])>10 else 'black')
    ax.set_title('Reported connection 121566: RMSE (pA), change relative to state model',loc='left',pad=12)
    fig.colorbar(heat,ax=ax,pad=.02,label='RMSE change vs state (%)')
    colors=('#4477aa','#228833','#cc6677','#aa3377','#66ccee','#bbbbbb','#ee7733')
    for j,(model,label,color) in enumerate(zip(models,names,colors)):
        x=np.arange(4)+(j-3)*.09
        delta=[100*(aggregate[p,model]/aggregate[p,'state']-1) for p in pairs]
        bx.scatter(x,delta,label=label,color=color,s=37,marker=('o','s','D','^','v','<','>')[j])
    bx.axhline(0,color='#555555',lw=.8);bx.set_xticks(range(4),[str(p) for p in pairs])
    bx.set_ylabel('RMSE change vs state (%)');bx.set_xlabel('Recorded pair ID')
    bx.grid(axis='y',alpha=.2);bx.set_title('All four directions: 16 non-training recording/cohort scores per model',loc='left',pad=10)
    bx.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,-.24),frameon=False)
    fig.suptitle('Observed source events improve some current readouts, not transport consistently',fontsize=14,y=.98)
    fig.text(.035,.035,'Lower is better. Fit: five 50 Hz recordings, initial eight pulses; ridge and timing grids use recording-level CV.\n'
        'Primary recording-QC cohort includes response-QC failures. Same-sweep recovery is not an independent recording.\n'
        'Frequency, order and state covary; shifts are sensitivity checks. These are conditional current predictions, not identified PSCs.',fontsize=9)
    fig.tight_layout(rect=(.01,.16,.99,.94));png.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(png,dpi=160);plt.close(fig)
    out=dict(builder_sha256=sha(__file__),input_sha256=sha(source),image_sha256=sha(png),
        matplotlib=matplotlib.__version__,cohorts=cohorts,models=models,
        connected_state_rmse_pA=baseline.tolist(),connected_model_rmse_pA=values.tolist(),relative_percent=relative.tolist(),
        aggregate=[dict(pair_id=p,model=m,rmse_pA=v) for (p,m),v in aggregate.items()])
    with receipt.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2,allow_nan=False)
    print(str(png))


if __name__=='__main__':main()
