import unittest
import numpy as np
from resource_core import *

class Contracts(unittest.TestCase):
    def simple(self):return Model(np.array([1.,1.]),np.array([0,1]),np.array([[0.,.3],[.3,0.]]),np.ones(2),np.ones(2)*.1)
    def test_bool_time_rejected(self):
        with self.assertRaises(TypeError):binding_pair(.5,.1,1,1,.1,True)
    def test_negative_free_rejected(self):
        with self.assertRaises(ValueError):binding_pair(-.1,.1,1,1,.1,1)
    def test_occupancy_above_capacity_rejected(self):
        with self.assertRaises(ValueError):binding_pair(.1,1.1,1,1,.1,1)
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):binding_pair(.1,.1,1,float('nan'),.1,1)
    def test_zero_duration_identity(self):self.assertEqual(binding_pair(.8,.2,1,1,.1,0),(.8,.2))
    def test_no_reaction_identity(self):np.testing.assert_allclose(binding_pair(.8,.2,1,0,0,5),(.8,.2),atol=1e-16)
    def test_release_returns_pool(self):
        p,b=binding_pair(.8,.2,1,0,.4,3)
        self.assertAlmostEqual(b,.2*np.exp(-1.2));self.assertAlmostEqual(p+b,1)
    def test_double_root(self):
        p,b=binding_pair(.8,.2,1,1,0,2)
        self.assertAlmostEqual(b,1-.8/(1+1.6));self.assertAlmostEqual(p+b,1)
    def test_empty_pool_no_forward_capture(self):
        self.assertEqual(binding_pair(0,0,1,4,0,3),(0.,0.))
    def test_saturated_sites_do_not_exceed_limit(self):
        p,b=binding_pair(.2,1,1,100,0,2);self.assertEqual(b,1);self.assertAlmostEqual(p,.2)
    def test_failed_call_preserves_inputs(self):
        p=np.array([.2,.3]);b=np.array([.1,1.2]);oldp=p.copy();oldb=b.copy()
        with self.assertRaises(ValueError):split_step(self.simple(),p,b,0,.2,lambda t:np.ones(2))
        self.assertTrue(np.array_equal(p,oldp));self.assertTrue(np.array_equal(b,oldb))
    def test_external_configuration_not_shared(self):
        C=np.array([1.,1.]);m=Model(C,np.array([0,1]),np.zeros((2,2)),np.ones(2),np.ones(2));C[:]=4
        np.testing.assert_array_equal(m.capacities,[1,1])
    def test_asymmetric_conductance_rejected(self):
        with self.assertRaises(ValueError):Model(np.ones(2),np.array([0,1]),np.array([[0.,1.],[0.,0.]]),np.ones(2),np.ones(2))
    def test_bool_sites_rejected(self):
        with self.assertRaises(ValueError):Model(np.ones(2),np.array([False,True]),np.zeros((2,2)),np.ones(2),np.ones(2))
    def test_untagged_site_no_new_binding(self):
        m=self.simple();p,b=split_step(m,[1,1],[0,0],0,1,lambda t:np.ones(2),lambda t:np.array([1.,0.]))
        self.assertGreater(b[0],0);self.assertEqual(b[1],0.)
    def test_disconnected_pool_totals(self):
        m=Model(np.ones(2),np.array([0,1]),np.zeros((2,2)),np.ones(2),np.ones(2)*.2)
        p,b=split_step(m,[.8,.2],[.1,.1],0,1,lambda t:np.array([1.,2.]))
        np.testing.assert_allclose(p+b,[.9,.3],atol=1e-14)
    def test_area_change_alone_dilutes_not_creates(self):
        m=Model(np.ones(2),np.array([0,1]),np.zeros((2,2)),np.zeros(2),np.zeros(2))
        p,b=split_step(m,[1,1],[0,0],0,2,lambda t:np.ones(2)*(1+t))
        np.testing.assert_allclose(p,[1,1]);np.testing.assert_allclose(p/3,[1/3,1/3])
    def test_equilibrium_mass(self):
        p,b,c=equilibrium(.8,[1],[1,1],[.15,.15]);self.assertAlmostEqual(p.sum()+b.sum(),.8,places=12)
    def test_capacity_competition(self):
        _,b0,_=equilibrium(.8,[1],[1],[.15]);_,b1,_=equilibrium(.8,[1],[1,1],[.15,.15]);self.assertLess(b1[0],b0[0])
    def test_supply_rescue(self):
        _,b0,_=equilibrium(.8,[1],[1,1],[.15,.15]);_,b1,_=equilibrium(1.6,[1],[1,1],[.15,.15]);self.assertTrue(np.all(b1>b0))
    def test_symmetric_equilibrium_not_wta(self):
        _,b,_=equilibrium(1,[1],[1,1],[.2,.2]);self.assertEqual(b[0],b[1])
    def test_microscopic_mass_and_probabilities(self):
        s,p,m,c=microscopic_stationary([5,6],7,[.5,.4]);self.assertTrue(np.all(s.sum(axis=1)<=7));self.assertAlmostEqual(p.sum(),1)
    def test_deterministic_and_stochastic_equilibria_not_assumed_equal(self):
        _,_,mean,_=microscopic_stationary([2,2],2,[.5,.5]);_,b,_=equilibrium(2,[1],[2,2],[2,2]);self.assertGreater(np.max(np.abs(mean-b)),1e-4)

if __name__=='__main__':unittest.main(verbosity=2)
