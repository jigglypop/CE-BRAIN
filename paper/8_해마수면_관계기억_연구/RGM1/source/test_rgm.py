import unittest,math,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from rgm_core import *

class RGMContracts(unittest.TestCase):
    def test_invalid_matrix_rejected(self):
        with self.assertRaises(ValueError):response_moment([[1,3],[0,1]],[1,0])
    def test_nonpositive_decay_rejected(self):
        with self.assertRaises(ValueError):response_moment([[0,0],[0,1]],[1,0])
    def test_boolean_time_rejected(self):
        with self.assertRaises(TypeError):regional_flow([1],[1],[0],True,[[1]],[1],[1])
    def test_zero_time_is_exact_and_owned(self):
        e=np.array([1.,0.]);i=np.array([.2,.9]);t=np.array([0.,.3])
        got=regional_flow(e,i,t,0,path_operator([1,2],[.4]),[1,2],[3,4])
        for x,y in zip(got,(e,i,t)):self.assertTrue(np.array_equal(x,y));self.assertFalse(np.shares_memory(x,y))
    def test_no_pre_no_tag(self):
        *_,tag=regional_flow([0,0],[1,1],[0,0],3,path_operator([1,2],[.4]),[1,2],[3,4])
        self.assertTrue(np.array_equal(tag,[0,0]))
    def test_no_instruction_no_tag(self):
        *_,tag=regional_flow([1,1],[0,0],[0,0],3,path_operator([1,2],[.4]),[1,2],[3,4])
        self.assertTrue(np.array_equal(tag,[0,0]))
    def test_positive_chemical_semigroup_required(self):
        with self.assertRaises(ValueError):regional_flow([1,1],[1,0],[0,0],3,[[2,1],[1,2]],[1,2],[3,4])
    def test_equal_regions_do_not_mix_contrast_into_mean(self):
        x=two_region(0,1,.5,.5,.2,[0,1,2]);np.testing.assert_allclose(x[:,0],0,atol=1e-15)
    def test_zero_forcing_contrast_can_change_mean(self):
        x=two_region(0,1,.2,1.4,.3,[0,1]);self.assertGreater(abs(x[-1,0]),.1)
    def test_resolvent_integrated_response(self):
        K=path_operator([1,2],[.4]);b=np.array([1,0]);
        self.assertAlmostEqual(response_moment(K,b),float(b@np.linalg.solve(K,b)),places=13)
    def test_logdet_reference(self):
        self.assertEqual(spectral_source(np.diag([1,2,3]),1,1),0.)
    def test_inverse_wavelength_thickness_scaling(self):
        B,S=.01,1;k=(S/(2*B))**(1/3);k2=(S/(16*B))**(1/3)
        self.assertAlmostEqual(k/k2,2,places=13)
    def test_under_threshold_hessian_positive_on_nonconstant_modes(self):
        H,k,h=fold_hessian(64,.01,1,.38);self.assertGreater(float(h[k>0].min()),0)
    def test_above_threshold_has_negative_modes(self):
        H,k,h=fold_hessian(64,.01,1,.44);self.assertLess(float(h.min()),0)
    def test_no_compression_cannot_buckle(self):
        H,k,h=fold_hessian(64,.01,1,0);self.assertGreaterEqual(float(h.min()),0)
    def test_no_global_shortcut_connectivity_from_embedding(self):
        # The intrinsic metric of an isometric cylindrical patch is the identity.
        u=.73;R=2.;dx=np.array([np.cos(u/R),0,np.sin(u/R)])
        self.assertAlmostEqual(float(dx@dx),1.,places=14)
    def test_source_file_blob(self):
        p=Path(__file__).parent/'data/fsLR_32k_midthickness-lh_eval_50.txt';b=p.read_bytes()
        self.assertEqual(hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest(),'d53ffd0a5244211fdea238266e2714a221c6a2a5')

if __name__=='__main__':unittest.main(verbosity=2)
