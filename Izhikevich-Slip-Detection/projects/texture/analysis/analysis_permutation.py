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

def permutation(signal):
    permut = np.random.permutation(len(signal))
    return signal[permut]

colors = ['black','firebrick','darkorange','gold','chartreuse','mediumaquamarine','skyblue','darkblue']
# texturev = ['GreyTile', 'MultiColorTile', 'SmoothTile', 'RT', 'RugSoftBacking', 'WhiteRug', 'PAPER', 'SB']
texturev = ['1','2','3','4','5','NOISE']
res = [np.load('exp_dataset_artificial/results_taxel' + str(k) + '.npz') for k in range(16)]
print(res[0].files)

features = res[0]['features']
targets = res[0]['targets']
# print(targets)
for k in range(15):
    features = np.hstack((features,res[k+1]['features']))
    # targets = np.hstack((targets,res[k+1]['targets']))

features = features / np.max(features)

createFile = False

if createFile:
    tb0 = time.time()
    simul = [[] for k in range(16)]
    isihist = [[] for k in range(16)]
    featObj = [[] for k in range(16)]
    plt.figure()
    for k in range(16):
        plt.subplot(4,4,k+1)
        print('permutation')
        tt0 = time.time()
        pool = Pool() #for multiprocessing, use all available cores
        im = pool.map(permutation,res[k]['inputCurrent']) #load all the data files
        pool.close()
        pool.join()
        ttf = time.time()
        print('finished: ' + str(ttf-tt0) + ' seconds')

        #run the simulation
        n = [spkn.model.izhikevich() for i in range(len(texturev)*20)]
        simul[k] = spkn.simulation(dt=1,t0=0,tf=len(im[0]),I=im,neurons=n)
        #running simulations
        print('Simulation: ' + str(k))
        tt0 = time.time()
        simul[k].optIzhikevich()
        ttf = time.time()
        print('finished: ' + str(ttf-tt0) + ' seconds')

        isihist[k] = spkn.analysis.isi_histogram(simul[k], 20, type='gaussian')
        for w in range(len(texturev)):
            plt.plot(isihist[k].xvals[w],isihist[k].yvals[w],color=colors[w])

        featObj[k] = spkn.classification.feature_extraction(simul[k], 20)

        #saving the results
        np.savez('permut_results_taxel' + str(k),
        features=featObj[k].features,targets=featObj[k].targets,
        isihist_xvals=isihist[k].xvals,isihist_yvals=isihist[k].yvals,inputCurrent=simul[k].I,
        spikes=simul[k].spikes,target_names=texturev)


    tbf = time.time()
    print('total time: ' + str(tbf-tb0) + ' seconds')
    # plt.show()
else:
    ax_inputs = plt.figure()
    ax_rawinputs = plt.figure()
    ax_isi = plt.figure()
    ax_feat = plt.figure()

    globalFeatures = np.zeros((len(texturev)*20,32))
    permutFeatures = np.zeros((len(texturev)*20,32))
    idx = 0

    for k in range(16):
        x = np.load('permut_results_taxel' + str(k) + '.npz')
        y = np.load('exp_dataset_artificial/results_taxel' + str(k) + '.npz')

        x0 = ax_inputs.add_subplot(4,4,k+1)
        xx0 = ax_rawinputs.add_subplot(4,4,k+1)
        x1 = ax_isi.add_subplot(4,4,k+1)
        x2 = ax_feat.add_subplot(4,4,k+1)

        auxv = 0
        for w in range(len(texturev)):
            x0.plot(x['inputCurrent'][auxv],color=colors[w])
            xx0.plot(y['inputCurrent'][auxv],color=colors[w])
            x1.plot(x['isihist_xvals'][w],x['isihist_yvals'][w],color=colors[w])
            x2.scatter(x['features'][auxv:auxv+20,0],x['features'][auxv:auxv+20,1],color=colors[w])

            globalFeatures[auxv:auxv+20,idx] = y['features'][auxv:auxv+20,0]
            globalFeatures[auxv:auxv+20,idx+1] = y['features'][auxv:auxv+20,1]
            permutFeatures[auxv:auxv+20,idx] = x['features'][auxv:auxv+20,0]
            permutFeatures[auxv:auxv+20,idx+1] = x['features'][auxv:auxv+20,1]
            auxv += 20

        idx += 2

    #features original data
    idx = 0
    plt.figure()
    for k in range(16):
        auxv = 0
        plt.subplot(4,4,k+1)
        for w in range(len(texturev)):
            plt.scatter(globalFeatures[auxv:auxv+20,idx],globalFeatures[auxv:auxv+20,idx+1],color=colors[w])
            auxv += 20
        idx += 2
    #features permutation data
    idx = 0
    plt.figure()
    for k in range(16):
        auxv = 0
        plt.subplot(4,4,k+1)
        for w in range(len(texturev)):
            plt.scatter(permutFeatures[auxv:auxv+20,idx],permutFeatures[auxv:auxv+20,idx+1],color=colors[w])
            auxv += 20
        idx += 2

    #TSNE with original data
    rawTSNE = TSNE(n_components=2).fit_transform(globalFeatures)
    plt.figure()
    plt.title('TSNE - Original signal')
    auxv = 0
    for w in range(len(texturev)):
        plt.scatter(rawTSNE[auxv:auxv+20,0],rawTSNE[auxv:auxv+20,1],color=colors[w],label=texturev[w])
        auxv += 20
    plt.legend()

    #TSNE with permuted data
    permutTSNE = TSNE(n_components=2).fit_transform(permutFeatures)
    ax_tsne = plt.figure()
    plt.title('TSNE - Permuted signal')
    auxv = 0
    for w in range(len(texturev)):
        x3 = ax_tsne.add_subplot(1,1,1)
        x3.scatter(permutTSNE[auxv:auxv+20,0],permutTSNE[auxv:auxv+20,1],color=colors[w],label=texturev[w])
        auxv += 20
    plt.legend()
plt.show()
