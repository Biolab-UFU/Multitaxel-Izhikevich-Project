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
import sys
sys.path.append('../../../framework/libraries/neuromorphic')
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
import spiking_neurons as spkn
#-------------------------------------------------------------------------------
def convscale(x,xmin,xmax,ymin,ymax):
    vals = ((x-xmin)*(ymax-ymin) / (xmax-xmin)) + ymin;
    vals = np.array(vals)
    vals[np.where(vals < ymin)] = ymin
    vals[np.where(vals > ymax)] = ymax
    return vals
#-------------------------------------------------------------------------------
def funcsat(x,xmin,xmax):
    x[np.where(x < xmin)] = xmin
    x[np.where(x > xmax)] = xmax
    return x
#-------------------------------------------------------------------------------
NROWS = 4
NCOLS = 4
NTAXELS = NROWS*NCOLS
#-------------------------------------------------------------------------------
fileprefix = './data/testing_'
fileforce = ['005_','01_','015_']
filetimep = ['3_','6_','9_']
filesuffix = 'Ite'
numFiles = 3
#-------------------------------------------------------------------------------
#array for storing the texture data
textures = [[] for k in range(numFiles)]
#-------------------------------------------------------------------------------
#normalization parameters
normMin = 0
normMax = 1
#-------------------------------------------------------------------------------
#low pass filter
nfilt = 4
fc = 10
sampfreq = 1000
b,a = sig.butter(nfilt,(fc/(sampfreq/2)),'low')
#-------------------------------------------------------------------------------
#length of the signals
signalLength = np.zeros(numFiles)
#-------------------------------------------------------------------------------
#pre-processing
for k in range(numFiles):
    filename = fileprefix + fileforce[1] + filetimep[1] + filesuffix + str(k) + '.txt'
    print('loading ' + filename + '...')
    textureSignal = np.loadtxt(filename)
    signalLength[k] = len(textureSignal)
    normsignal = [convscale(textureSignal[:,i],np.mean(textureSignal[0:500,i]),0,normMin,normMax) for i in range(NTAXELS)]
    # textures[k] = [normsignal[i] for i in range(NTAXELS)]
    textures[k] = [funcsat(sig.filtfilt(b,a,normsignal[i]),normMin,normMax)*100 for i in range(NTAXELS)]
#-------------------------------------------------------------------------------
#convert to spiking neurons
dt = 1
t0 = 0
#find the signal with least samples
tf = np.min(signalLength)
# print(signalLength)
# print(tf)
simul = [[] for k in range(NTAXELS)]
rasters = [[] for k in range(NTAXELS)]
features = [[] for k in range(NTAXELS)]
#convert each taxel individually
for k in range(NTAXELS):
    neuronmodel = [spkn.model.izhikevich() for i in range(numFiles)]
    Im = [textures[i][k] for i in range(numFiles)]
    simul[k] = spkn.simulation(dt,t0,tf,Im,neuronmodel)
    print('running simulation for taxel: ' + str(k) + '...')
    simul[k].run()
    rasters[k] = spkn.analysis.raster(simul[k])
    features[k] = spkn.classification.feature_extraction(simul[k],3)
    # print(rasters)
    print('simulation finished!')
#-------------------------------------------------------------------------------
print(features[0].features)
#-------------------------------------------------------------------------------
plt.figure()
for k in range(numFiles):
    plt.subplot(numFiles,1,k+1)
    [plt.plot(textures[k][i]) for i in range(16)]
#-------------------------------------------------------------------------------
plt.figure()
for k in range(NTAXELS):
    plt.subplot(NROWS,NCOLS,k+1)
    if rasters[k] is not False:
        for w in range(numFiles):
            plt.scatter(rasters[k].xvals[w],rasters[k].yvals[w],marker='|',color='k')
        plt.xlim([t0,tf])
#-------------------------------------------------------------------------------
plt.show()
#-------------------------------------------------------------------------------
