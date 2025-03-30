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
#-------------------------------------------------------------------------------
# 1) load results
results = [np.load('./exp_dataset_artificial_noise_30/results_taxel' + str(k) + '.npz') for k in range(16)]
# 2) loop over all taxels and from every texture, take one sample
#generate all the plots that are necessary to explore the data and save them
numIte = 20
numTextures = len(results[0]['texturev'])
windowsize = 300
overlap = 0.2
signalId = 0
xgrid = np.linspace(0,500,1000)
#fit kdes
for w in range(numTextures):
    textureName = results[0]['texturev'][w]
    print('processing texture ' + textureName)

    asr = [spkn.analysis.get_asr_over_time(results[k]['spikes'][signalId],windowsize,overlap) for k in range(16)]
    kdeobj = [stats.gaussian_kde(asr[k]) for k in range(16)]
    kdefit = [kdeobj[k].evaluate(xgrid) for k in range(16)]
    ent = [stats.entropy(kdefit[k],base=2) for k in range(16)]

    #plot the inputs
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(16):
        plt.subplot(4,4,k+1)
        plt.plot(results[k]['rawCurrent'][signalId])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(textureName + '_inputs.png', bbox_inches='tight')
    plt.close()

    #plot the spiking rate over time
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(16):
        plt.subplot(4,4,k+1)
        plt.plot(asr[k])
        plt.ylim([0,np.max(asr[k])])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(textureName + '_avgsr.png', bbox_inches='tight')
    plt.close()

    #plot the histogram
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(16):
        plt.subplot(4,4,k+1)
        probs,bins = np.histogram(asr[k])
        plt.bar(bins[0:len(bins)-1],probs)
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(textureName + '_histogram.png', bbox_inches='tight')
    plt.close()

    #plot the kde
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(16):
        plt.subplot(4,4,k+1)
        plt.plot(xgrid,kdefit[k])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(textureName + '_kde.png', bbox_inches='tight')
    plt.close()

    #plot the entropy
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(16):
        plt.bar(np.arange(len(ent)),ent)
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(textureName + '_entropy.png', bbox_inches='tight')
    plt.close()

    signalId += numIte

'''























#-------------------------------------------------------------------------------
# kdefit = [[] for k in range(16)]
# ent = [[] for k in range(16)]
# windowsize = 300
# overlap = 0.2
# signalId = 130
# xgrid = np.linspace(0,500,1000)
# for k in range(15,16):
#     for w in range(60,80):
#         print('taxel ' + str(k) + ', texture it ' + str(w))
#         asr = spkn.analysis.get_asr_over_time(results[k]['spikes'][w],windowsize,overlap)
#         kdeobj = stats.gaussian_kde(asr)
#         kdefit[k].append(kdeobj.evaluate(xgrid))
#         ent[k].append(stats.entropy(kdefit[k][-1],base=2))
#     plt.plot(ent[k])
#     plt.show()
#-------------------------------------------------------------------------------
# 2) compute average spiking rate of each taxel for the same texture, one
#iteration only
windowsize = 300
overlap = 0.2
signalId = 70
xgrid = np.linspace(0,500,1000)
asr = [spkn.analysis.get_asr_over_time(results[k]['spikes'][signalId],windowsize,overlap) for k in range(16)]
#fit kdes
kdeobj = [stats.gaussian_kde(asr[k]) for k in range(16)]
kdefit = [kdeobj[k].evaluate(xgrid) for k in range(16)]
ent = [stats.entropy(kdefit[k],base=2) for k in range(16)]
kldiv = [kld(kdefit[6],kdefit[k]) for k in range(16)]
print(ent)
print(kldiv)
plt.figure()
for k in range(16):
    plt.subplot(4,4,k+1)
    plt.plot(results[k]['rawCurrent'][signalId])
plt.figure()
for k in range(16):
    plt.subplot(4,4,k+1)
    plt.plot(asr[k])
    plt.ylim([0,np.max(asr[k])])
plt.figure()
for k in range(16):
    plt.subplot(4,4,k+1)
    plt.plot(xgrid,kdefit[k])
plt.figure()
for k in range(16):
    plt.subplot(4,4,k+1)
    probs,bins = np.histogram(asr[k],bins='auto')
    plt.bar(bins[0:len(bins)-1],probs)
plt.figure()
plt.bar(np.arange(len(ent)),ent)
plt.figure()
plt.bar(np.arange(len(kldiv)),kldiv)
plt.show()
#-------------------------------------------------------------------------------
'''
