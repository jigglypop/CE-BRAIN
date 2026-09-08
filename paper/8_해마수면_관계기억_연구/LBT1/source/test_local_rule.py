import math
import unittest
import numpy as np
from scipy.special import logsumexp
from scipy.stats import poisson
from local_rule import Parameters,LocalPlasticity,tag_flow,execute,count_moments,rates
from verify import partition_logpdf

class TestLocalRule(unittest.TestCase):
    def test_zero_tag(self):
        w=np.array([.1,.5,.9]);self.assertTrue(np.array_equal(w,execute(w,np.zeros(3),100.,Parameters())))
    def test_zero_dose(self):
        w=np.array([0.,.5,1.]);self.assertTrue(np.array_equal(w,execute(w,np.ones(3),0.,Parameters())))
    def test_tiny_time_bridge(self):
        e,i,t=tag_flow(1.,1.,0.,1e-16,Parameters())
        self.assertAlmostEqual(float(t)/1e-16,1.,places=14)
    def test_equal_rate_bridge(self):
        p=Parameters(tau_e_s=2,tau_i_s=2,tau_tag_s=1)
        self.assertAlmostEqual(float(tag_flow(1,1,0,2,p)[2]),2*math.exp(-2),places=14)
    def test_no_pre_trace(self):
        self.assertEqual(float(tag_flow(0,1,0,30,Parameters())[2]),0.)
    def test_no_instruction(self):
        self.assertEqual(float(tag_flow(1,0,0,30,Parameters())[2]),0.)
    def test_bounds_and_direction(self):
        p=Parameters();w=np.array([0.,.1,.95,1]);y=execute(w,np.ones(4),2,p)
        self.assertTrue(np.all((y>=0)&(y<=1)));self.assertGreater(y[1],w[1]);self.assertLess(y[2],w[2])
    def test_parameter_no_boolean(self):
        with self.assertRaises(TypeError):Parameters(tau_e_s=True)
    def test_branch_integer(self):
        with self.assertRaises(TypeError):LocalPlasticity(['a'],[.5],[.2],[1])
    def test_backward_time_rejected(self):
        o=LocalPlasticity(['a'],[0],[.2],[1]);o.advance_to(2)
        with self.assertRaises(ValueError):o.advance_to(1)
        self.assertEqual(o.time,2)
    def test_owned_initial_state(self):
        w=np.array([.2]);o=LocalPlasticity(['a'],[0],w,[1]);w[0]=.8
        self.assertEqual(o.weights[0],.2)
    def test_same_group_means_independent_of_partition(self):
        p=Parameters();w=np.array([.2,.7]);tag=np.array([.3,.8])
        m,c,_=count_moments(w,tag,[0,0],1.,2.,p)
        m2,c2,_=count_moments(w,tag,[0,1],1.,2.,p)
        self.assertTrue(np.array_equal(m,m2));self.assertEqual(c2[0,1],0.)
    def test_branch_locality(self):
        o=LocalPlasticity(['a','b'],[0,1],[.2,.2],[1,-1]);o.presynaptic(0);o.instruct(0);o.advance_to(20);o.burst(0,2)
        self.assertEqual(o.weights[1],.2);self.assertTrue(np.array_equal(o.signs,[1,-1]))
    def test_likelihood_against_cartesian_enumeration(self):
        from verify import P
        w=np.array([.2,.8]);tag=np.array([.3,.7]);nu=.8;dose=1.5;sig=.03
        y=np.array([[.3,.7],[.4,.65]])
        calculated,_=partition_logpdf(y,w,tag,np.arange(2),nu,dose,sig)
        limit=int(poisson.ppf(1-1e-13,nu));n=np.arange(limit+1);p=poisson.pmf(n,nu);p/=p.sum()
        a,b=rates(tag,P);m=a/(a+b);v=m+(w-m)*np.exp(-n[:,None]*dose*(a+b))
        values=[]
        for obs in y:
            terms=[]
            for i in n:
                for j in n:
                    ll=-.5*sum(((obs-np.array([v[i,0],v[j,1]]))/sig)**2)-math.log(2*math.pi*sig*sig)
                    terms.append(math.log(p[i])+math.log(p[j])+ll)
            values.append(logsumexp(terms))
        np.testing.assert_allclose(calculated,values,atol=1e-12,rtol=0.)

if __name__=='__main__':unittest.main(verbosity=2)
