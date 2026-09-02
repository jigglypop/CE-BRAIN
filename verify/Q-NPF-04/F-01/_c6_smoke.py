import sys,os,time
sys.path.insert(0,os.path.abspath('verify/Q-NPF-04/F-01'))
import c6_practical as c6
c6.N_REP=3
t=time.time(); c6.main(); print("smoke elapsed %.1f"%(time.time()-t))
