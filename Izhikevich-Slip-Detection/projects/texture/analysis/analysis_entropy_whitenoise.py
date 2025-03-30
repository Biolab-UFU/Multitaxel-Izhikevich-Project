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
def compute_entropy_whitenoise_mean(meanv):
    tt0 = time.time()
    # print('computing')
    global stdDist, numSamples, xgrid
    samples = np.random.normal(meanv,stdDist,numSamples)
    kdeobj = stats.gaussian_kde(samples)
    kdefit = kdeobj.evaluate(xgrid)
    entr = stats.entropy(kdefit,base=2)
    ttf = time.time()
    # print('finished! ' + str(ttf-tt0) + ' seconds')
    return entr
#-------------------------------------------------------------------------------
def compute_entropy_whitenoise_std(stdv):
    tt0 = time.time()
    # print('computing')
    global meanDist, numSamples, xgrid
    samples = np.random.normal(meanDist,stdv,numSamples)
    kdeobj = stats.gaussian_kde(samples)
    kdefit = kdeobj.evaluate(xgrid)
    entr = stats.entropy(kdefit,base=2)
    ttf = time.time()
    # print('finished! ' + str(ttf-tt0) + ' seconds')
    return entr
#-------------------------------------------------------------------------------
meanDist = -60
stdDist = 10
numSamples = 1000
xgrid = np.linspace(-2000,2000,10000)
#first, test the influence of the variance in the estimate of entropy
meanDist = 0
stdItv = np.arange(0.1,200,0.5)
respEnt = np.zeros(len(stdItv))

#computing changes in entropy due to the mean of the distribution
meanItv = np.arange(0,200,0.5)
print('entropy while changing the mean value')
tt0 = time.time()
pool = Pool() #for multiprocessing, use all available cores
resp = pool.map(compute_entropy_whitenoise_mean,meanItv) #load all the data files
respEntMean = [resp[k] for k in range(len(resp))]
pool.close()
pool.join()
ttf = time.time()
print('finished! ' + str(ttf-tt0) + ' seconds')

print('entropy while changing the std value')
tt0 = time.time()
pool = Pool() #for multiprocessing, use all available cores
resp = pool.map(compute_entropy_whitenoise_std,stdItv) #load all the data files
respEntStd = [resp[k] for k in range(len(resp))]
pool.close()
pool.join()
ttf = time.time()
print('finished! ' + str(ttf-tt0) + ' seconds')

# tt0 = time.time()
# for k in range(len(stdItv)):
#     print('computing std: ' + str(stdItv[k]))
#     samples = np.random.normal(meanDist,stdItv[k],numSamples)
#     kdeobj = stats.gaussian_kde(samples)
#     kdefit = kdeobj.evaluate(xgrid)
#     respEnt[k] = stats.entropy(kdefit,base=2)
# ttf = time.time()
# print('finished! ' + str(ttf-tt0) + ' seconds')

plt.figure()
plt.plot(meanItv,respEntMean)
plt.title('Entropy while changing the mean')

plt.figure()
plt.plot(stdItv,respEntStd)
plt.title('Entropy while changing the std')
plt.show()

# #generate the samples
# samples = np.random.normal(meanDist,stdDist,size=numSamples)
# #fit to kde
# kdeobj = stats.gaussian_kde(samples)
# kdefit = kdeobj.evaluate(xgrid)
# print(stats.entropy(kdefit,base=2))
# plt.figure()
# plt.plot(xgrid,kdefit)
# plt.show()
#-------------------------------------------------------------------------------
