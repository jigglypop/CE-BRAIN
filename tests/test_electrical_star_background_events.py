"""Event exposure and unit-scale controls for the target-current follow-up."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"))
from electrical_star_background_events import RATE,exposure_categories,detect,rate_table
from allen_effective_conductance_units import producer_ratio,conditional_steady_conductance


def test_command_regions_and_context_exclusions_partition_exposure():
    cat=exposure_categories(RATE,[(0,.2,.2015)])
    assert cat[round(.15*RATE)]==0
    assert cat[round(.199*RATE)]==1
    assert cat[round(.2005*RATE)]==2
    assert cat[round(.202*RATE)]==10
    assert cat[round(.232*RATE)]==1
    assert cat[round(.234*RATE)]==0
    rates=rate_table(cat,[])
    assert sum(r['exposure_s'] for r in rates)==pytest.approx(np.sum(cat>=0)/RATE)


def test_inward_event_threshold_and_boundary_do_not_count_positive_peak():
    t=np.arange(RATE)/RATE
    current=-30-1200*np.exp(-((t-.15)/.0001)**2)+1200*np.exp(-((t-.4)/.0001)**2)
    cat=exposure_categories(RATE,[])
    events=detect(current,cat,1000)
    assert len(events)==1
    assert events[0]['time_s']==pytest.approx(.15)
    assert events[0]['inward_amplitude_pA']==pytest.approx(1200)
    assert events[0]['category']==0


def test_voltage_ratio_does_not_identify_absolute_synaptic_conductance():
    leak,synapse=10e-9,2e-9
    v0,reversal=-.055,-.075
    psp=synapse/(leak+synapse)*(reversal-v0)
    eta=producer_ratio(psp,reversal,v0)
    assert eta<0
    assert conditional_steady_conductance(eta,leak)==pytest.approx(synapse)
    assert conditional_steady_conductance(eta,2*leak)==pytest.approx(2*synapse)
    for invalid in [-1,-2,.1]:
        with pytest.raises(ValueError):conditional_steady_conductance(invalid,leak)
