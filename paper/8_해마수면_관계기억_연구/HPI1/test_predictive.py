import itertools,unittest
import numpy as np
from predictive_core import *

class PredictiveContracts(unittest.TestCase):
    def prepared(self):
        m,_=template(111);initialize_from_past_episodes(m,toy_sequences());return m
    def test_fixed_pool_and_emission_ids(self):
        m,s=template();before=m.emission.copy();n=len(s);initialize_from_past_episodes(m,toy_sequences())
        self.assertEqual(n,len(m.initial));np.testing.assert_array_equal(m.emission,before)
    def test_observation_only_encoding_not_enough(self):
        m=self.prepared();a=m.posterior([0,1,3]);b=m.posterior([0,2,3])
        np.testing.assert_array_equal(a@m.emission,b@m.emission)
        self.assertGreater(hellinger_chord_squared(a@m.future_likelihoods(3),b@m.future_likelihoods(3)),7.9)
    def test_missing_cue_keeps_ambiguity(self):
        m=self.prepared();p=m.posterior([0,None,3,3,3])@m.future_likelihoods(1)
        np.testing.assert_allclose(p[[4,5]],[.5,.5],atol=1e-13)
    def test_observed_cue_selects_future(self):
        m=self.prepared()
        for seq in toy_sequences():
            self.assertAlmostEqual((m.posterior(seq[:5])@m.future_likelihoods(1))[seq[5]],1,places=13)
    def test_impossible_pattern_fails(self):
        m=self.prepared()
        with self.assertRaises(ValueError):m.posterior([0,1,5])
    def test_boolean_symbol_rejected(self):
        with self.assertRaises(ValueError):self.prepared().posterior([False,1])
    def test_bad_probability_rejected(self):
        with self.assertRaises(ValueError):ContextModel([[1,1],[0,1]],np.eye(2),[1,0])
    def test_empty_episode_rejected(self):
        with self.assertRaises(ValueError):initialize_from_past_episodes(self.prepared(),[[]])
    def test_slot_budget_enforced(self):
        m=ContextModel(np.ones((7,7))/7,np.eye(7),np.eye(7)[0])
        with self.assertRaises(ValueError):initialize_from_past_episodes(m,toy_sequences())
    def test_forward_independent_path_enumeration(self):
        m,_=template(88);seq=toy_sequences()[0]
        supports=[np.flatnonzero(m.emission[:,y]) for y in seq];p=0.
        for path in itertools.product(*supports):
            v=m.initial[path[0]]
            for t in range(len(path)-1):v*=m.transition[path[t],path[t+1]]
            p+=v
        self.assertAlmostEqual(np.exp(np.log(m.forward(seq)[1]).sum()),p,places=14)
    def test_counts_total_is_transitions(self):
        m,_=template(100);c,ll=m.expectation(toy_sequences()[0]);self.assertAlmostEqual(c.sum(),6,places=12)
    def test_em_non_decrease(self):
        m,_=template(11);ll=m.fit(toy_sequences(),30);self.assertGreaterEqual(np.diff(ll).min(),-1e-10)
    def test_future_joint_word_independent_paths(self):
        rng=np.random.default_rng(17);T=rng.uniform(.1,1,(3,3));T/=T.sum(1)[:,None]
        B=rng.uniform(.1,1,(3,2));B/=B.sum(1)[:,None];m=ContextModel(T,B,[.2,.3,.5]);L=m.future_likelihoods(3)
        for j,word in enumerate(itertools.product(range(2),repeat=3)):
            for start in range(3):
                p=0.
                for path in itertools.product(range(3),repeat=3):
                    a=start;v=1.
                    for state,y in zip(path,word):v*=T[a,state]*B[state,y];a=state
                    p+=v
                self.assertAlmostEqual(p,L[start,j],places=14)
    def test_future_mass_conserved(self):
        m,_=template(3)
        for h in range(5):np.testing.assert_allclose(m.future_likelihoods(h).sum(1),1,atol=2e-12)
    def test_fisher_horizon_monotonic(self):
        rng=np.random.default_rng(170)
        for _ in range(16):
            T=rng.random((4,4));T/=T.sum(1)[:,None];B=rng.random((4,3));B/=B.sum(1)[:,None]
            m=ContextModel(T,B,np.ones(4)/4);vals=[mixture_fisher(*m.future_likelihoods(h)[[0,1]]) for h in range(4)]
            self.assertGreaterEqual(np.diff(vals).min(),-1e-12)
    def test_fisher_matches_local_kl(self):
        p=np.array([.1,.3,.6]);q=np.array([.6,.2,.2]);rho=.4;eps=1e-4
        center=rho*p+(1-rho)*q
        kp=sum(center*np.log(center/((rho+eps)*p+(1-rho-eps)*q)))
        km=sum(center*np.log(center/((rho-eps)*p+(1-rho+eps)*q)))
        self.assertAlmostEqual((kp+km)/eps**2,mixture_fisher(p,q,rho),places=6)
    def test_marginal_geometry_can_lose_all_context(self):
        p=np.array([.5,0,0,.5]);q=np.array([0,.5,.5,0])
        for ax in (0,1):np.testing.assert_array_equal(p.reshape(2,2).sum(ax),q.reshape(2,2).sum(ax))
        self.assertAlmostEqual(hellinger_chord_squared(p,q),8,places=13)
    def test_identical_future_laws_are_null_direction(self):
        self.assertEqual(mixture_fisher(np.array([.4,.6]),np.array([.4,.6])),0)
    def test_replayed_copies_not_more_independent_data(self):
        m,_=template(201);receipt=initialize_from_past_episodes(m,toy_sequences()*10)
        self.assertEqual(receipt['distinct_training_episodes'],2)
        self.assertAlmostEqual((m.posterior([0,None,3,3,3])@m.future_likelihoods(1))[4],.5,places=13)

if __name__=='__main__':unittest.main(verbosity=2)
