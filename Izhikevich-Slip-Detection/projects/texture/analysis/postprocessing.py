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
from sklearn.svm import SVC
from scipy import stats
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def permutation(signal):
    permut = np.random.permutation(len(signal))
    return signal[permut]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
numSignals = 20
colors = ['black','firebrick','darkorange','gold','chartreuse','mediumaquamarine','skyblue','darkblue','saddlebrown']
# folderpath = './exp_dataset_tiles_10_2'
# texturev = ['GreyTile', 'MultiColorTile',  'SmoothTile']
# folderpath = './exp_dataset_natural_15'
# texturev = ['GreyTile', 'MultiColorTile',  'SmoothTile', 'RT', 'RugSoftBacking', 'WhiteRug', 'PAPER', 'SB']
# folderpath = './exp_dataset_natural_noise_offset_30'
folderpath = './exp_dataset_newnatural_noise_30'
texturev = ['GreyTile', 'MultiColorTile',  'SmoothTile', 'RT', 'RugSoftBacking', 'WhiteRug', 'PAPER', 'SB', 'NOISE']
# texturev = ['RugSoftBacking','WhiteRug','NOISE']
# folderpath = './exp_dataset_rugs30_noise'
# texturev = ['1','2','3','4','5','NOISE']
# folderpath = './exp_dataset_newartificial2_30'
# folderpath = './exp_dataset_artificial_noise_offset_10'
# texturev = ['1','2','3','4','5']
# folderpath = './exp_dataset_artificial_30'
res = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(16)]
#compute the 32-dimensional feature space
globalFeatures = res[0]['features']
for i in range(1,16):
    globalFeatures = np.hstack((globalFeatures,res[i]['features']))
print(globalFeatures.shape)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# INPUTS
#-------------------------------------------------------------------------------
plt.figure(figsize=(19.2,10.8),dpi=100)
for k in range(16):
    auxv = 0
    plt.subplot(4,4,k+1)
    for w in range(len(texturev)):
        plt.plot(res[k]['inputCurrent'][auxv],color=colors[w])
        auxv += 20
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/inputs.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# ISI Histogram
#-------------------------------------------------------------------------------
plt.figure(figsize=(19.2,10.8),dpi=100)
for k in range(16):
    auxv = 0
    plt.subplot(4,4,k+1)
    for w in range(len(texturev)):
        plt.plot(res[k]['isihist_xvals'][w],res[k]['isihist_yvals'][w],color=colors[w])
        auxv += 20
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/isihist.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# RASTERGRAM
#-------------------------------------------------------------------------------
plt.figure(figsize=(19.2,10.8),dpi=100)
for k in range(16):
    auxv = 0
    plt.subplot(4,4,k+1)
    for w in range(len(texturev)):
        plt.scatter(res[k]['raster_xvals'][auxv],res[k]['raster_yvals'][auxv],marker='|',color='k')
        auxv += 20
    plt.xlim([res[0]['timev'][0],res[0]['timev'][-1]])
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/rasters.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
# FEATURES
#-------------------------------------------------------------------------------
plt.figure(figsize=(19.2,10.8),dpi=100)
for k in range(16):
    auxv = 0
    plt.subplot(4,4,k+1)
    for w in range(len(texturev)):
        plt.scatter(res[k]['features'][auxv:auxv+20,0],res[k]['features'][auxv:auxv+20,1],color=colors[w])
        auxv += 20
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/features.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# CLASSIFICATION
#-------------------------------------------------------------------------------
#classification of individual taxels
clf = neighbors.KNeighborsClassifier(n_neighbors=12,weights='distance')
confmat = [[] for k in range(16)]
plt.figure(figsize=(19.2,10.8),dpi=100)
f = open(folderpath + '/accuracy.txt','w')
for i in range(16):
    plt.subplot(4,4,i+1)
    ret = spkn.classification.LOOCV(clf, features=res[i]['features'], targets=res[i]['targets'], target_names=texturev)
    plt.matshow(ret[0],fignum=False,vmin=0,vmax=20)
    plt.colorbar()
    #write the overall accuracy to the file
    f.write('taxel ' + str(i) + ' ' + str(np.trace(ret[0])/(numSignals*len(texturev))) + '\n')
f.close()
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/confmatrix.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PCA 90.0
#-------------------------------------------------------------------------------
#reduce with PCA and then use tsne for visualizing
pcaObj = PCA(n_components=0.90,svd_solver='full')
featScaled = stats.zscore(globalFeatures)
featPCA = pcaObj.fit_transform(featScaled)
# print(pcaObj.inverse_transform(featPCA))
# featPCA = PCA(n_components=0.8,svd_solver='full').fit_transform(globalFeatures)
print('PCA: ' + str(featPCA.shape))
pcaTSNE = TSNE(n_components=2).fit_transform(featPCA)
#plot
plt.figure(figsize=(19.2,10.8),dpi=100)
auxv = 0
for w in range(len(texturev)):
    plt.scatter(pcaTSNE[auxv:auxv+20,0],pcaTSNE[auxv:auxv+20,1],label=texturev[w],color=colors[w])
    auxv += 20
plt.legend()
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/pca900_' + str(featPCA.shape[1]) + '_features.png'
plt.savefig(filename, bbox_inches='tight')
#classification
ret = spkn.classification.LOOCV(clf, features=featPCA, targets=res[i]['targets'], target_names=texturev)
print(ret[0])
print(ret[1])
#plot
plt.figure(figsize=(19.2,10.8),dpi=100)
plt.title('Confusion Matrix')
plt.matshow(ret[0],fignum=False,vmin=0,vmax=20)
plt.colorbar()
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/pca900_' + str(featPCA.shape[1]) + '_confmatrix.png'
plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
# PCA 99.5
#-------------------------------------------------------------------------------
#reduce with PCA and then use tsne for visualizing
pcaObj = PCA(n_components=0.995,svd_solver='full')
featScaled = stats.zscore(globalFeatures)
featPCA = pcaObj.fit_transform(featScaled)
# print(pcaObj.inverse_transform(featPCA))
# featPCA = PCA(n_components=0.8,svd_solver='full').fit_transform(globalFeatures)
print('PCA: ' + str(featPCA.shape))
pcaTSNE = TSNE(n_components=2).fit_transform(featPCA)
#plot
plt.figure(figsize=(19.2,10.8),dpi=100)
auxv = 0
for w in range(len(texturev)):
    plt.scatter(pcaTSNE[auxv:auxv+20,0],pcaTSNE[auxv:auxv+20,1],label=texturev[w],color=colors[w])
    auxv += 20
plt.legend()
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/pca995_' + str(featPCA.shape[1]) + '_features.png'
plt.savefig(filename, bbox_inches='tight')
#classification
ret = spkn.classification.LOOCV(clf, features=featPCA, targets=res[i]['targets'], target_names=texturev)
print(ret[0])
print(ret[1])
#plot
plt.figure(figsize=(19.2,10.8),dpi=100)
plt.title('Confusion Matrix')
plt.matshow(ret[0],fignum=False,vmin=0,vmax=20)
plt.colorbar()
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())
filename = folderpath + '/pca995_' + str(featPCA.shape[1]) + '_confmatrix.png'
plt.savefig(filename, bbox_inches='tight')
