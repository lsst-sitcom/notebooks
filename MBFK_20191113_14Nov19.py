# Stand-alone code for running makeBrighterFatterKernel.py on ComCam data.
# This version (14-Nov-19) is just to test it out with the MBFK.py code in tickets/DM-18683

import os, sys, time, datetime, glob, subprocess
import matplotlib.pyplot as plt
import numpy as np
import astropy.io.fits as pf

import eups
check_eups = subprocess.Popen('eups list -s | grep lsst_distrib',shell=True)
subprocess.Popen.wait(check_eups)
check_local = subprocess.Popen('eups list -s | grep LOCAL',shell=True)
subprocess.Popen.wait(check_local)
sys.stdout.flush()
from lsst.daf.persistence import Butler
from lsst.cp.pipe.makeBrighterFatterKernel import MakeBrighterFatterKernelTask

DETECTOR=4 # Do S11 only
REPO_DIR = '/project/shared/comCam'
starting_visit = 2019111300120
ending_visit = 2019111300210


pairs = []
visit_1 = starting_visit
while visit_1 < ending_visit:
    pairs.append('%s,%s'%(str(visit_1),str(visit_1+2)))
    visit_1 += 4
print(pairs)
print(len(pairs))
sys.stdout.flush()

args = [REPO_DIR, '--output', '/lsst/jhome/cslage/ComCam/20191113A/' ,'--id', 'detector=%d'%DETECTOR,  '--visit-pairs']
for pair in pairs:
    args.append(str(pair))
args = args + ['-c','xcorrCheckRejectLevel=2', 'doCalcGains=True', 'level="AMP"', 'forceZeroSum=True', 'biasCorr=1.0',
                   'correlationModelRadius=3', 'correlationQuadraticFit=True', 'doPlotPtcs=True',
                   'maxMeanSignal=100000',
                   '--clobber-config', '--clobber-versions']

corr_struct = MakeBrighterFatterKernelTask.parseAndRun(args=args)
