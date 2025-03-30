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
    plt.figure()
    for k in range(16):
        print('processing taxel ' + str(k))
        plt.subplot(4,4,k+1)
        isiv[k] = spkn.information.get_global_isi(resp[k]['spikes'], numSignals)
        kdeobj[k] = [stat.gaussian_kde(isiv[k][w]) for w in range(numTextures)]
        kdefit[k] = [kdeobj[k][w].evaluate(xgrid) for w in range(numTextures)]
        for i in range(numTextures):
            for j in range(numTextures):
                matkld_taxels[k][i,j] = kld(kdefit[k][i],kdefit[k][j])
        # print(matkld_taxels[k])
        plt.matshow(matkld_taxels[k],fignum=False)
        plt.colorbar()

    #plot the figure with the gaussian fit
    plt.figure()
    for k in range(16):
        plt.subplot(4,4,k+1)
        for w in range(numTextures):
            plt.plot(xgrid,kdefit[k][w])

    #KL divergence between taxels, same texture
    plt.figure()
    for w in range(numTextures):
        print('processing texture ' + str(w))
        plt.subplot(3,4,w+1)
        plt.title(resp[0]['texturev'][w])
        for i in range(16):
            for j in range(16):
                matkld_textures[w][i,j] = kld(kdefit[i][w],kdefit[j][w])
        plt.matshow(matkld_textures[w],fignum=False)
        plt.colorbar()

    #KL divergence between taxels, same texture
    colors = ['black','dimgrey','rosybrown','lightcoral','darkred','darkorange',
    'gold','olive','palegreen','lime','aquamarine','darkcyan','steelblue',
    'midnightblue','indigo','crimson']
    colors = np.array(colors)
    sf = np.random.permutation(len(colors))
    colors = colors[sf]
    for w in range(numTextures):
        plt.figure(figsize=(19.2,10.8),dpi=100)
        print('processing texture ' + str(w))
        # plt.subplot(2,4,w+1)
        plt.title(resp[0]['texturev'][w])
        for i in range(16):
            plt.plot(xgrid,kdefit[i][w],label='taxel '+str(i),color=colors[i])
        plt.legend()
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        filename = './gaussiankde_texture_' + str(resp[0]['texturev'][w]) + '.png'
        plt.savefig(filename, bbox_inches='tight')
    plt.show()

    '''
    taxelId = 5
    res = np.load(folderpath + '/results_taxel' + str(taxelId) + '.npz')


    #create a vector containing all the ISI values
    isiv = spkn.information.get_global_isi(res['spikes'], numSignals)

    #fit using KDE from scipy
    kernel = [stat.gaussian_kde(isiv[k],bw_method=20/np.std(isiv[k],ddof=1)) for k in range(numTextures)]
    # kernel = [stat.gaussian_kde(isiv[k]) for k in range(numTextures)]
    xgrid = np.linspace(0,1500,10000) #
    scipy_kde = [kernel[k].evaluate(xgrid) for k in range(numTextures)]
    #print entropy
    print('kde entropy')
    [print(stat.entropy(x)) for x in scipy_kde]

    #fit using KDE from statsmodels
    kde = [KDEUnivariate(np.array(isiv[k],dtype=float))  for k in range(numTextures)]
    [x.fit(kernel='gau',bw=50,fft=False) for x in kde]
    sm = [x.evaluate(xgrid) for x in kde]
    print('statsmodels entropy')
    [print(x.entropy) for x in kde]

    #fit using histogram
    probs = [[] for k in range(numTextures)]
    bins = [[] for k in range(numTextures)]
    muv = [[] for k in range(numTextures)]
    sigmav = [[] for k in range(numTextures)]
    binsize = 30
    for k in range(numTextures):
        probs[k],bins[k] = np.histogram(isiv[k],bins=binsize)
        probs[k] = probs[k] / np.sum(probs[k])
        muv[k],sigmav[k] = stat.norm.fit(probs[k])
        # print(bins[k])
    #fitting to a normal distribution

    # print('histogram entropy')
    # [print(stat.entropy(x)) for x in probs]

    #KL Divergence
    scipy_kld = np.zeros((numTextures,numTextures))
    for i in range(numTextures):
        scipy_kde[i][np.where(scipy_kde[i] == 0)] = 0.0000001
        for j in range(numTextures):
            scipy_kde[j][np.where(scipy_kde[j] == 0)] = 0.0000001
            scipy_kld[i,j] = stat.entropy(scipy_kde[i],scipy_kde[j])
    print(scipy_kld)

    #plot kde from scipy
    plt.figure()
    for k in range(numTextures):
        plt.plot(xgrid,scipy_kde[k],label=res['texturev'][k])
    plt.legend()

    #plot kde from statsmodels
    plt.figure()
    for k in range(numTextures):
        plt.plot(xgrid,sm[k],label=res['texturev'][k])
    plt.legend()

    plt.figure()
    #plot histogram
    for k in range(numTextures):
        plt.plot(bins[k][0:len(bins[k])-1],probs[k],label=res['texturev'][k])
    plt.legend()

    plt.figure()
    #plot gaussian fit from histogram
    for k in range(numTextures):
        plt.plot(probs[k],stat.norm.pdf(probs[k],muv[k],sigmav[k]),label=res['texturev'][k])
    plt.legend()


    plt.show()
    '''

    # isiv = [spkn.analysis.get_isi(res['spikes'][k]) for k in range(numTextures)]
    # #fit using kde
    # kernel = [stat.gaussian_kde(isiv[k],bw_method=0.1) for k in range(numTextures)]
    # xgrid = np.linspace(0,1000,1000)
    # v = [kernel[k].evaluate(xgrid) for k in range(numTextures)]
    # plt.figure()
    # for k in range(numTextures):
    #     plt.plot(xgrid,v[k],label=res['texturev'][k])
    # plt.legend()
    # plt.show()
#-------------------------------------------------------------------------------
# plt.figure()
# plt.plot(tactile)
# plt.show()
#-------------------------------------------------------------------------------
