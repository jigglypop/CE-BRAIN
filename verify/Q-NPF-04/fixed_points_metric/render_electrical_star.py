"""Show fixed points, measured cross-transfer and heldout pilot errors."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    contract = json.loads((HERE/'electrical_star_transfer_contract.json').read_text(encoding='utf8'))
    result = json.loads((HERE/'electrical_star_transfer_result.json').read_text(encoding='utf8'))
    by_device = {cell['device_id']:cell for cell in contract['cells']}
    cells = [by_device[d] for d in contract['star_devices_center_then_leaves']]
    p = np.array([c['position'] for c in cells])*1e6
    p -= p[0]
    fig = plt.figure(figsize=(12,9),layout='constrained')
    a = fig.add_subplot(2,2,1,projection='3d')
    a.scatter(*p.T,c=['#b83131']+['#2878b5']*3,s=50)
    for i in range(1,4):
        a.plot(*p[[0,i]].T,color='#888888')
    for point,cell in zip(p,cells):
        a.text(*point,str(cell['id']),fontsize=9)
    a.set_xlim(p[:,0].min()-20,p[:,0].max()+20)
    a.set_ylim(p[:,1].min()-20,p[:,1].max()+20)
    a.set_zlim(p[:,2].min()-12,p[:,2].max()+12)
    a.set(xlabel='x (um)',ylabel='y (um)',zlabel='z (um)',title='A. Fixed positions + manual electrical labels')
    b = fig.add_subplot(2,2,2)
    z = np.array(result['summary'][0]['measured_star_transfer_MOhm'])
    np.fill_diagonal(z,np.nan)
    limit = float(np.nanmax(np.abs(z)))
    shown = b.imshow(z,cmap='coolwarm',vmin=-limit,vmax=limit)
    b.set_xticks(range(4),[str(c['id']) for c in cells],rotation=25)
    b.set_yticks(range(4),[str(c['id']) for c in cells])
    b.set(title='B. Measured cross-transfer, training sweep 10',xlabel='Injected cell',ylabel='Recorded cell')
    for i in range(4):
        for j in range(4):
            if i!=j:
                b.text(j,i,f'{z[i,j]:.2f}',ha='center',va='center',fontsize=9)
    fig.colorbar(shown,ax=b,label='MOhm (diagonal omitted)')
    c = fig.add_subplot(2,2,3)
    d = fig.add_subplot(2,2,4)
    held = result['summary'][1:]
    x = np.arange(len(held))
    for k,(name,color) in enumerate([('Zero','#999999'),('Free transfer','#2878b5'),('Symmetric','#e07b22')]):
        key = 'unrestricted' if k==1 else 'symmetric'
        errors = [r['zero_star_offdiagonal_rms_mV'] if k==0 else r[key]['star_offdiagonal_rmse_mV'] for r in held]
        c.bar(x+(k-1)*.23,np.array(errors)*1000,.21,label=name,color=color)
    d.bar(x-.13,[r['zero_unused_leaf_rms_mV']*1000 for r in held],.24,label='Zero',color='#999999')
    if result['star_fit'] is not None:
        d.bar(x+.13,[r['star_unused']['rmse_mV']*1000 for r in held],.24,label='Star prediction',color='#358458')
    else:
        d.text(.5,.85,'Star fit ineligible',transform=d.transAxes,ha='center')
    for axis,title in [(c,'C. All 12 cross responses among the four cells'),(d,'D. Four responses unused by the star fit')]:
        axis.set(title=title,ylabel='Heldout RMSE (uV)')
        axis.set_xticks(x,[f"Sweep {r['sweep']}" for r in held])
        axis.spines[['right','top']].set_visible(False)
        axis.legend(fontsize=9)
    fig.suptitle('Electrical-star pilot: response prediction at fixed neuron positions',fontsize=15)
    fig.supxlabel('Same-experiment pilot selected using manual annotations. Transmission constraints are not direct anatomy or metric validation.',fontsize=9)
    for extension in ['png','svg']:
        output = HERE/f'electrical_star_pilot.{extension}'
        if output.exists():
            raise FileExistsError(output)
        fig.savefig(output,dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
