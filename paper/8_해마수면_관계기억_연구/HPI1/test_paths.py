import unittest
import numpy as np
from path_geometry import path_metric,path_jacobians

class PathChecks(unittest.TestCase):
    def test_path_stack_matches_direct_propagation(self):
        A=np.array([[.4,.1],[.2,.3]]);B=np.eye(2);C=np.array([[1.,.2]])
        J,_=path_jacobians(A,B,C,3);x=np.array([.7,-.2]);r=B@x;read=[]
        for _ in range(3):r=A@r;read.append(float((C@r)[0]))
        np.testing.assert_allclose(J@x,read,atol=1e-15)
    def test_temporal_covariance_cannot_be_dropped(self):
        # Two identical sensors, correlated Gaussian noise.
        A=B=np.ones((1,1));C=np.ones((2,1));S=np.array([[1.,.8],[.8,1.]])
        G,_=path_metric(A,B,C,S,1);G0,_=path_metric(A,B,C,np.eye(2),1)
        self.assertAlmostEqual(G[0,0],2/1.8);self.assertAlmostEqual(G0[0,0],2)
    def test_nonpositive_covariance_rejected(self):
        with self.assertRaises(np.linalg.LinAlgError):path_metric(np.eye(2),np.eye(2),np.eye(2),np.zeros((2,2)),1)

if __name__=='__main__':unittest.main()
