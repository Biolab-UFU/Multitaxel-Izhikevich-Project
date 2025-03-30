import sys
sys.path.append('../../../framework/libraries/neuromorphic')
import numpy as np
from sklearn import neighbors, datasets
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
import time
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import spiking_neurons as spkn
from copy import copy
from multiprocessing import Pool
#-------------------------------------------------------------------------------
def permutation(signal):
    permut = np.random.permutation(len(signal))
    return signal[permut]

colors = ['black','firebrick','darkorange','gold','chartreuse','mediumaquamarine','skyblue','darkblue','saddlebrown']
texturev = ['GreyTile', 'MultiColorTile', 'SmoothTile', 'RT', 'RugSoftBacking', 'WhiteRug', 'PAPER', 'SB','NOISE']
res = [np.load('exp_dataset_with_noise15/results_taxel' + str(k) + '.npz') for k in range(16)]

#MULTI TAXEL
createFile = False
if createFile:
    rawsig = [[] for k in range(16)]
    simulObj = [[] for k in range(16)]
    isihist = [[] for k in range(16)]
    rasters = [[] for k in range(16)]
    featObj = [[] for k in range(16)]
    for k in range(16):
        rawsig[k] = [(x*150) for x in res[k]['rawCurrent']]
        n = [spkn.model.izhikevich(d=8) for k in range(180)]
        simulObj[k] = spkn.simulation(dt=1,t0=0,tf=len(rawsig[k][0]),I=rawsig[k],neurons=n)
        print('Simulation: ' + str(k))
        simulObj[k].optIzhikevich()
        isihist[k] = spkn.analysis.isi_histogram(simulObj[k], 20, type='gaussian')
        rasters[k] = spkn.analysis.raster(simulObj[k])
        featObj[k] = spkn.classification.feature_extraction(simulObj[k], numSignals=20)
        np.savez('amplitude_results_taxel' + str(k),
        features=featObj[k].features,targets=featObj[k].targets,
        isihist_xvals=isihist[k].xvals,isihist_yvals=isihist[k].yvals,inputCurrent=simulObj[k].I,
        spikes=simulObj[k].spikes)
else:
    res = [np.load('amplitude_results_taxel' + str(k) + '.npz') for k in range(16)]

    plt.figure()
    for k in range(16):
        auxv = 0
        plt.subplot(4,4,k+1)
        for w in range(len(texturev)):
            plt.plot(res[k]['inputCurrent'][auxv])
            auxv += 20

    plt.figure()
    for k in range(16):
        auxv = 0
        plt.subplot(4,4,k+1)
        for w in range(len(texturev)):
            plt.plot(res[k]['isihist_xvals'][w],res[k]['isihist_yvals'][w],color=colors[w])
            auxv += 20

    plt.figure()
    for k in range(16):
        auxv = 0
        plt.subplot(4,4,k+1)
        for w in range(len(texturev)):
            plt.scatter(res[k]['features'][auxv:auxv+20,0],res[k]['features'][auxv:auxv+20,1],color=colors[w])
            auxv += 20

    #classification of individual taxels
    clf = neighbors.KNeighborsClassifier(n_neighbors=12,weights='distance')
    confmat = [[] for k in range(16)]
    plt.figure()
    for i in range(16):
        plt.subplot(4,4,i+1)
        ret = spkn.classification.LOOCV(clf, features=res[i]['features'], targets=res[i]['targets'], target_names=texturev)
        plt.matshow(ret[0],fignum=False,vmin=0,vmax=20)

    globalFeatures = res[0]['features']
    for i in range(1,16):
        globalFeatures = np.hstack((globalFeatures,res[i]['features']))
    print(globalFeatures.shape)
    #TSNE
    featTSNE = TSNE(n_components=2).fit_transform(globalFeatures)
    plt.figure(figsize=(19.2,10.8),dpi=100)
    auxv = 0
    for w in range(len(texturev)):
        plt.scatter(featTSNE[auxv:auxv+20,0],featTSNE[auxv:auxv+20,1],label=texturev[w],color=colors[w])
        auxv += 20
    plt.legend()
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig('tsne.png', bbox_inches='tight')


    #reduce with PCA and then use tsne for visualizing
    pcaObj = PCA(n_components=0.95,svd_solver='full')
    featPCA = pcaObj.fit_transform(globalFeatures)
    # print(pcaObj.inverse_transform(featPCA))
    # featPCA = PCA(n_components=0.8,svd_solver='full').fit_transform(globalFeatures)
    print('PCA: ' + str(featPCA.shape))
    pcaTSNE = TSNE(n_components=2).fit_transform(featPCA)
    plt.figure()
    auxv = 0
    for w in range(len(texturev)):
        plt.scatter(pcaTSNE[auxv:auxv+20,0],pcaTSNE[auxv:auxv+20,1],label=texturev[w],color=colors[w])
        auxv += 20
    plt.legend()

    ret = spkn.classification.LOOCV(clf, features=featPCA, targets=res[i]['targets'], target_names=texturev)
    print(ret[0])
    print(ret[1])

    plt.show()
#analyze without GreyTile
#just amplify the signal
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#SINGLE TAXEL
#-------------------------------------------------------------------------------
# rawsig = [(x/np.max(x))*10 for x in res[14]['rawCurrent']]
# rawsig = [(x*5000)+10 for x in res[14]['rawCurrent']]
# #simulation
# n = [spkn.model.izhikevich(d=8) for k in range(180)]
# simulObj = spkn.simulation(dt=1,t0=0,tf=len(rawsig[0]),I=rawsig,neurons=n)
# tt0 = time.time()
# simulObj.optIzhikevich()
# ttf = time.time()
# print('finished: ' + str(ttf-tt0) + ' seconds')
# rasters = spkn.analysis.raster(simulObj)
# isihist = spkn.analysis.isi_histogram(simulObj, numSignals=20, type='gaussian')
# featObj = spkn.classification.feature_extraction(simulObj, 20)
# auxv = 0
# plt.figure()
# for w in range(len(texturev)):
#     # plt.plot(simulObj.I[auxv],color=colors[w])
#     # plt.scatter(rasters.xvals[auxv],rasters.yvals[auxv],marker='|',color='k')
#     # plt.plot(isihist.xvals[w],isihist.yvals[w],color=colors[w])
#     plt.scatter(featObj.features[auxv:auxv+20,0],featObj.features[auxv:auxv+20,1],color=colors[w],label=texturev[w])
#     auxv += 20
# plt.legend()
# plt.show()
#-------------------------------------------------------------------------------
# #-------------------------------------------------------------------------------
# featuresTSNE = TSNE(n_components=2).fit_transform(features)
# plt.figure()
# auxv = 0
# for w in range(len(texturev)):
#     plt.scatter(featuresTSNE[auxv:auxv+20,0],featuresTSNE[auxv:auxv+20,1],color=colors[w],label=texturev[w])
#     auxv += 20
# plt.legend()
# plt.show()
# #-------------------------------------------------------------------------------
# plt.figure()
# for w in range(16):
#     auxv = 0
#     plt.subplot(4,4,w+1)
#     for k in range(len(texturev)):
#         plt.plot(res[w]['inputCurrent'][auxv],color=colors[k])
#         auxv += 20
# plt.show()
# #-------------------------------------------------------------------------------
