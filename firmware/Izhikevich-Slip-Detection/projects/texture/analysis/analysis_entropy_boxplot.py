# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering and Robotics Group
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#Paths
import os, sys, glob
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/texture_recognition')
#-------------------------------------------------------------------------------
import spiking_neurons as spkn
import numpy as np
from scipy import stats, signal
import matplotlib.pyplot as plt
from multiprocessing import Pool
import time
from copy import copy
#-------------------------------------------------------------------------------
#checking how average spiking rate changes over time
#-------------------------------------------------------------------------------
def kld(a,b):
    a = np.array(a)
    b = np.array(b)
    # print(a[a==0])
    # print(b[b==0])
    # a[a==0] = 0.00001
    # b[b==0] = 0.00001
    idxa = np.where(np.logical_or(np.equal(a,0),np.less_equal(a,1e-300)))
    idxb = np.where(np.logical_or(np.equal(b,0),np.less_equal(b,1e-300)))
    a[idxa] = 1e-100
    b[idxb] = 1e-100
    # print(a[a==1])
    # print(b[b==1])
    return stats.entropy(a,b,base=2)
#-------------------------------------------------------------------------------
def parallel_entropy(spikes):
    global results,windowsize,overlap,numTextures,numIte
    tt0 = time.time()
    # print('processing')
    asr = spkn.analysis.get_asr_over_time(spikes,windowsize,overlap)
    kdeobj = stats.gaussian_kde(asr)
    kdefit = kdeobj.evaluate(xgrid)
    ent = stats.entropy(kdefit,base=2)
    ttf = time.time()
    # print('finished! ' + str(ttf-tt0) + ' seconds')
    return asr,kdefit,ent
#-------------------------------------------------------------------------------
'''
ATTENTION: BAD CODE BELOW! HAHAHAHA
'''
def overall_entropy(taxelId):
    global results,windowsize,overlap,numTextures,numIte
    tt0 = time.time()
    print('processing taxel ' + str(taxelId))
    asr = [spkn.analysis.get_asr_over_time(results[taxelId]['spikes'][z],windowsize,overlap) for z in range(len(results[taxelId]['spikes']))]
    kdeobj = [stats.gaussian_kde(asr[z]) for z in range(numIte)]
    kdefit = [kdeobj[z].evaluate(xgrid) for z in range(numIte)]
    ent = np.array([stats.entropy(kdefit[z],base=2) for z in range(numIte)])
    ttf = time.time()
    print('finished! ' + str(ttf-tt0) + ' seconds')
    return kdefit,ent
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------
createFile = True
numTaxels = 16
numIte = 20
results = [np.load('./exp_dataset_artificial_noise_30/results_taxel' + str(k) + '.npz') for k in range(numTaxels)]
numTextures = len(results[0]['texturev'])
windowsize = 300
overlap = 0.2
signalId = 0
xgrid = np.linspace(0,500,1000)
auxv = 0
#vector for storing entropy values of each taxel for each texture
kdefitresp = [[] for k in range(numTaxels)]
entresults = [np.zeros((numIte,numTextures)) for k in range(numTaxels)]
if createFile is True:
    tt0 = time.time()
    #processing each taxel separately
    for k in range(numTaxels):
        t0 = time.time()
        pool = Pool() #for multiprocessing, use all available cores
        resp = pool.map(parallel_entropy,results[k]['spikes']) #load all the data files
        pool.close()
        pool.join()
        auxv = 0
        kdefitresp[k] = [resp[z][1] for z in range(numIte*numTextures)]
        for w in range(numTextures):
            for z in range(numIte):
                entresults[k][z,w] = copy(resp[auxv][2])
                auxv += 1
        tf = time.time()
        print('finished taxel ' + str(k) + ': ' + str(tf-t0) + ' seconds')
    ttf = time.time()
    print('finished processing! ' + str(ttf-tt0) + ' seconds')
else:
    print('not done yet')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# KL Divergence of NOISE against other textures for each taxel individually
#-------------------------------------------------------------------------------
kldiv = [[] for k in range(numTaxels)]
for k in range(numTaxels):
    t0 = time.time()
    for z in range(numTextures):
        kldiv[k].append(spkn.information.kldivergence(kdefitresp[k][z*numIte],kdefitresp[k][-1]))
    tf = time.time()
    print('finished taxel ' + str(k) + ': ' + str(tf-t0) + ' seconds')
#-------------------------------------------------------------------------------
# plot the KL Divergence of each taxel
plt.figure(figsize=(19.2,10.8),dpi=100)
for k in range(numTaxels):
    plt.subplot(4,4,k+1)
    plt.bar(np.arange(len(kldiv[k])),kldiv[k])
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
plt.savefig('kldiv_texture_vs_noise.png', bbox_inches='tight')
plt.close()

#-------------------------------------------------------------------------------
#plot the boxplot of entropies
for k in range(numTaxels):
    plt.figure(figsize=(19.2,10.8),dpi=100)
    plt.boxplot(entresults[k])
    plt.ylim([0,np.max(entresults[k])+2])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig('taxel' + str(k) + '_entropy_boxplot.png', bbox_inches='tight')
    plt.close()
# plt.show()
#-------------------------------------------------------------------------------
