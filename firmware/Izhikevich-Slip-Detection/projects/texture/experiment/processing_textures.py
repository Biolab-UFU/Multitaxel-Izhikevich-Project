# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
#-------------------------------------------------------------------------------
# Description:
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
import sys
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/texture_recognition')
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import spiking_neurons as spkn
import scipy.signal as sig
from dataprocessing import *
from tactileboard import *
import time
#import the library for processing the texture data
import texture
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#number of repetitions
numIterations = 20
#number of textures
texturesId = np.arange(1,6)
#force values
forcev = ['008','018','028']
# forcev = ['008']
#palpation time
palpationt = ['3','6','9','12']
# palpationt = ['3']
#file prefix --> basic file name
fileprefix  = './data/texture_new'

finalTime0 = time.time()
for j in range(len(forcev)):
    for w in range(len(palpationt)):
        files = []
        for i in range(len(texturesId)):
            for k in range(numIterations):
                overallFilePrefix = fileprefix + str(texturesId[i]) + '_' + forcev[j] + '_' + palpationt[w]
                files.append(overallFilePrefix + '_Ite' + str(k) + '.txt')

        #processing textures
        print('')
        print('-------')
        print('starting processing')
        print('')
        print('files: ' + overallFilePrefix)
        print('number of inputs:', len(files))
        print('loading files...')
        tt0 = time.time()
        t0 = time.time()
        x,y = texture.load_and_preprocessing(files,numIterations,parallel=True)
        t1 = time.time()
        print('done: ' + str(t1-t0) + ' seconds')

        print('running simulations...')
        t0 = time.time()
        simul = texture.simulate(x,y,opt=True)
        t1 = time.time()
        print('done: ' + str(t1-t0) + ' seconds')

        print('analyzing')
        t0 = time.time()
        rast,isihist = texture.analysis(simul,numIterations)
        t1 = time.time()
        print('done: ' + str(t1-t0) + ' seconds')

        print('classification')
        t0 = time.time()
        ret = texture.classification(simul,numIterations)
        t1 = time.time()
        print('done: ' + str(t1-t0) + ' seconds')

        fileresults = './results/classification_performance_' + forcev[j] + '_' + palpationt[w] + '_.txt'
        f = open(fileresults,'w')
        for k in range(TBCONSTS.NTAXELS):
            f.write('Classification Results for Taxel: ' + str(k+1) + '\n')
            f.write(str(ret[1][k]) + '\n')
            f.write('Overall accuracy: ' + str(np.trace(ret[1][k])/(numIterations*len(texturesId))) + '\n')
            f.write(str(ret[2][k]) + '\n')
            f.write('\n\n')

        filesuffix = forcev[j] + '_' + palpationt[w]
        texture.plot(simul,rast,isihist,ret[0],ret[1],numIterations,len(texturesId),filesuffix)

        #delete variables
        del(simul)
        del(rast)
        del(isihist)
        del(ret)

        tt1 = time.time()
        print('total time: ' + str(tt1-tt0) + ' seconds')

finalTime1 = time.time()
print('')
print('----------------------------')
print('Total processing time: ' + str(finalTime1-finalTime0) + ' seconds')
