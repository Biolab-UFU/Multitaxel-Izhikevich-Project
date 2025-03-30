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
def kld(a,b):
    a = np.array(a)
    b = np.array(b)
    # print(a[a==0])
    # print(b[b==0])
    a[a==0] = 0.00001
    b[b==0] = 0.00001
    # print(a[a==1])
    # print(b[b==1])
    return stat.entropy(a,b)
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
    # folderpath = './load_artificial'
    folderpath = '../texture/analysis/exp_dataset_natural_noise_offset_10'
    resp = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    numTextures = int(len(resp[0]['texturev']))
    numSignals = int(len(resp[0]['spikes']) / numTextures)

    #fitting the ISIs distribution of each texture for each taxel
    isiv = [[] for k in range(16)]
    kdeobj = [[] for k in range(16)]
    kdefit = [[] for k in range(16)]
    matkld_taxels = [np.zeros((numTextures,numTextures)) for k in range(16)]
    matkld_textures = [np.zeros((16,16)) for k in range(numTextures)]
    xgrid = np.linspace(0,100,1000)

    #first, KL divergence between textures -- generate the matrix
    for k in range(16):
        print('processing taxel ' + str(k))
        isiv[k] = spkn.information.get_global_isi(resp[k]['spikes'], numSignals)
        kdeobj[k] = [stat.gaussian_kde(isiv[k][w]) for w in range(numTextures)]
        kdefit[k] = [kdeobj[k][w].evaluate(xgrid) for w in range(numTextures)]
        for i in range(numTextures):
            for j in range(numTextures):
                matkld_taxels[k][i,j] = kld(kdefit[k][i],kdefit[k][j])
        # print(matkld_taxels[k])

    #
    # #plot the figure with the gaussian fit
    # plt.figure()
    # for k in range(16):
    #     plt.subplot(4,4,k+1)
    #     for w in range(numTextures):
    #         plt.plot(xgrid,kdefit[k][w])

    #KL divergence between taxels, same texture
    plt.figure()
    for w in range(numTextures):
        print('processing texture ' + str(w))
        plt.subplot(3,3,w+1)
        plt.title(resp[0]['texturev'][w])
        for i in range(16):
            for j in range(16):
                matkld_textures[w][i,j] = kld(kdefit[i][w],kdefit[j][w])
        plt.matshow(matkld_textures[w],fignum=False)
        plt.colorbar()

    plt.show()
