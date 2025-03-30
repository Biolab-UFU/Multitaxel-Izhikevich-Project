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
sys.path.append('../../framework/libraries/general')
sys.path.append('../../framework/libraries/neuromorphic')
sys.path.append('../../framework/libraries/texture_recognition')
#-------------------------------------------------------------------------------
import numpy as np
import scipy.stats as stat
import scipy.signal as sig
import matplotlib.pyplot as plt
import spiking_neurons as spkn
import texture as textrecog
from statsmodels.nonparametric.kde import KDEUnivariate
#-------------------------------------------------------------------------------
createFile = False
#-------------------------------------------------------------------------------
if createFile:
    #header file that determines data processing
    fileHeader = 'load_artificial.txt'
    #create a TextureRecognition object
    textureRecog = textrecog.TextureRecognition()
    #loads the header file
    ret = textureRecog.loadHeader(fileHeader)
    if ret:
        #generates the name of the files that should be loaded
        textureRecog.createDatasetFiles()
        #runs the processing of data
        textureRecog.runProcessing(parallel=True)
else:
    folderpath = './load_artificial'
    resp = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    numTextures = int(len(resp[0]['texturev']))
    numSignals = int(len(resp[0]['inputCurrent']) / numTextures)

    auxv = 5
    taxelId = 12
    plt.figure()
    for w in range(numTextures):
        plt.subplot(numTextures,1,w+1)
        plt.plot(resp[taxelId]['inputCurrent'][auxv],label=resp[taxelId]['texturev'][w])
        plt.scatter(resp[taxelId]['spikes'][auxv],np.ones(len(resp[taxelId]['spikes'][auxv])),color='k',marker='|')
        auxv += numSignals
    # plt.legend()
    plt.show()
