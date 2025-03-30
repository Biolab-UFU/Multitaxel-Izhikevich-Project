
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
import sys
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/texture_recognition')
sys.path.append('../../../framework/libraries/general')
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
import texture as textrecog
from tactileboard import *
#-------------------------------------------------------------------------------
# FUNCTIONS
#-------------------------------------------------------------------------------
def plot_texture_example(op='natural',textureId=2,it=10):
    if op == 'artificial':
        resp = [np.load('./exp_dataset_artificial_30/results_taxel' + str(k) + '.npz') for k in range(16)]
    elif op == 'natural':
        resp = [np.load('./exp_dataset_natural_30/results_taxel' + str(k) + '.npz') for k in range(16)]

    id = textureId*20 + it
    plt.figure()
    for k in range(16):
        plt.plot(resp[k]['timev'],resp[k]['rawCurrent'][id],label = 'Taxel ' + str(k))
    plt.xlabel('Time (ms)')
    plt.ylabel('Normalized Amplitude')
    plt.legend()
    plt.show()

#-------------------------------------------------------------------------------
def plot_experiment_setup():
    filename = ['/home/ner/natural/texture_GreyTile_007_30_Ite0.txt',
                '/home/ner/natural/texture_GreyTile_007_30_Ite1.txt']
    filtdata, eventdata = textrecog.load_and_preprocessing(filename,2,parallel=False)

    #correct the event data
    #fix according to the last '2' in eventdata
    lastIdx = np.where(eventdata[0]==2)[0][-1]
    # print(lastIdx) #debugging
    eventdata[0] = eventdata[0][0:lastIdx]
    filtdata[0][0] = filtdata[0][0][0:lastIdx]
    #replace '1s' with '0s', except for the last one
    idx1 = np.where(eventdata[0] == 1)[0]
    lastIdx1 = idx1[len(idx1)-1] + int(0 * TBCONSTS.SAMPFREQ)
    idx2 = int(lastIdx1 + 4.2 * TBCONSTS.SAMPFREQ)
    eventdata[0][idx1] = 0
    eventdata[0][lastIdx1] = 1
    eventdata[0][lastIdx1:idx2] = 1
    timev = np.arange(len(eventdata[0]))
    timev = timev * (1.0/TBCONSTS.SAMPFREQ)
    #bar marking the start of hold
    idxhold = np.where(eventdata[0]==1)[0][0]
    xhold = timev[idxhold]
    #bar marking the start of palpation
    idxpalpation = np.where(eventdata[0]==2)[0][0]
    xpalpation = timev[idxpalpation]
    #spikes
    #run simulation
    im = (filtdata[0][0] / np.max(filtdata[0][0])) * 12
    s = spkn.simulation(dt=1,t0=0,tf=len(im),I=[im],neurons=[spkn.model.izhikevich(d=8)])
    s.run()
    spkv = s.spikes[0]
    # spkv = [spkv[k]/1000.0 for k in range(len(spkv))]
    spkk = np.zeros(len(filtdata[0][0]))
    spkk[np.array(spkv)] = 1
    print(spkk)

    #plotting the figure
    fig = plt.figure()
    ax1 = fig.add_subplot(3,1,1)
    #plot the event data -> demonstrates the experimental setup
    ax1.plot(timev,eventdata[0])
    ax1.set_ylabel('Event Id')
    ax1.get_yaxis().set_ticks([])
    #plot the filtered tactile data
    ax2 = fig.add_subplot(3,1,2)
    ax2.plot(timev,filtdata[0][0])
    ax2.get_yaxis().set_ticks([])
    ax2.set_ylabel('Sensor output')
    #spikes
    ax3 = fig.add_subplot(3,1,3,)
    ax3.plot(timev,spkk,color='k',marker='|')
    ax3.set_ylim([0.09,0.11])
    # ax3.set_xlim([timev[0],timev[-1]])
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Neuromorphic output')
    ax3.get_yaxis().set_ticks([])
    # ax3.yaxis.set_visible(False)
    #plot the lines marking the beginning of events
    ax1.axvline(x=xhold,ymin=-10,ymax=2,color='k',linestyle='--',clip_on=False)
    ax1.axvline(x=xpalpation,ymin=-10,ymax=2,color='k',linestyle='--',clip_on=False)
    ax2.axvline(x=xhold,ymin=-0,ymax=2,color='k',linestyle='--',clip_on=False)
    ax2.axvline(x=xpalpation,ymin=-0,ymax=2,color='k',linestyle='--',clip_on=False)
    # ax3.axvline(x=xhold,ymin=-10,ymax=10,color='k',linestyle='--',clip_on=False)
    # ax3.axvline(x=xpalpation,ymin=-10,ymax=10,color='k',linestyle='--',clip_on=False)
    # ax3.axvline(x=spkv,color='r')
    plt.show()
#-------------------------------------------------------------------------------
def plot_entropy(op='natural'):
    global entropyv
    print('processing, please wait...')
    tt0 = time.time()
    if entropyv is None:
        if op == 'artificial':
            resp = [np.load('./exp_dataset_artificial_30/results_taxel' + str(k) + '.npz') for k in range(16)]
        elif op == 'natural':
            resp = [np.load('./exp_dataset_natural_30/results_taxel' + str(k) + '.npz') for k in range(16)]

        numClasses = len(resp[0]['texturev'])
        kdefit = [[] for k in range(numClasses)]
        entropyv = [[] for k in range(numClasses)]
        xgrid = np.linspace(0,1000,1000)
        numsig = 20
        i0 = 0
        i1 = i0 + numsig

        for w in range(numClasses):
            t0 = time.time()
            print('processing class: ' + str(w))
            kdefit = textrecog.analysis_kde_taxel(results_path='',results=resp,spkvItv=[i0,i1],xgrid=xgrid)
            entropyv[w] = [stats.entropy(x,base=2) for x in kdefit]
            i0 += numsig
            i1 += numsig
            tf = time.time()
            print('finished. ' + str(tf-t0) + ' seconds')

    ttf = time.time()
    print('finished! ' + str(ttf-tt0) + ' seconds')

    #find the maximum entropy value over all taxels and textures
    maxv = np.max([np.max(x) for x in entropyv])
    numClasses = len(resp[0]['texturev'])
    xgrid = np.linspace(0,1000,1000)
    plt.figure()
    for w in range(numClasses):
        plt.subplot(int(np.ceil(numClasses/2)),2,w+1)
        plt.bar(np.arange(1,len(entropyv[w])+1),entropyv[w]/maxv)
    plt.show()
#-------------------------------------------------------------------------------
def plot_kld(op = 'natural'):
    return 0
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    SMALL_SIZE = 14
    MEDIUM_SIZE = 18
    BIGGER_SIZE = 20

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    #entropy variables
    entropyv = None

    #MENU
    op = -1
    while op != 0:
        print('')
        print('---------------------------------------------------------------')
        print('Welcome to the neuromorphic texture recognition helper')
        print('Options')
        print('1 - Plot: Example of input and spikes')
        print('2 - Plot: Example of the experiment protocol with signals')
        print('3 - Plot: Entropy')
        print('4 - Plot: KL Divergence')
        print('0 - Exit')
        print('---------------------------------------------------------------')
        op = input('Please, enter the option of your choice: ')
        op = int(op)
        print('')
        if op == 1:
            plot_texture_example('natural',0,10)
        elif op == 2:
            plot_experiment_setup()
        elif op == 3:
            plot_entropy(op = 'artificial')
        elif op == 4:
            plot_kld(op = 'artificial')

    '''

    #artificial textures
    #plot taxels for a given texture
    folderpath_artificial = './exp_dataset_natural_30'
    resp = [np.load(folderpath_artificial + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    # plt.figure()
    # for k in range(16):
    #     plt.plot(resp[k]['timev'],resp[k]['rawCurrent'][70],label='Taxel ' + str(k))
    # plt.legend()
    # plt.xlabel('Time (ms)')
    # plt.ylabel('Normalized amplitude')

    #create a new vector, selecting only the signals related to the same texture
    textureId = 3
    idx0 = textureId * 20
    idx1 = idx0 + 20
    xgrid = np.linspace(0,500,1000)
    kdefit = textrecog.analysis_kde_taxel(results_path=folderpath_artificial, results=resp, spkvItv=[idx0,idx1], xgrid=xgrid)
    kdefitclass = textrecog.analysis_kde_class(results_path=folderpath_artificial, results=resp, xgrid=xgrid)

    entropy_taxels = [[] for k in range(16)]
    #compute entropy for same taxel, different textures
    for k in range(16):
        for w in range(len(kdefitclass[k])):
            entropy_taxels[k].append(stats.entropy(kdefitclass[k][w]))
        print(entropy_taxels[k])

    entropy_textures = [[] for k in range(16)]
    numTextures = len(resp[0]['texturev'])
    plt.figure()
    for w in range(numTextures):
        plt.subplot(4,2,w+1)
        print('texture ' + str(w))
        idx0 = w*20
        idx1 = idx0 + 20
        kdefit = textrecog.analysis_kde_taxel(results_path=folderpath_artificial, results=resp, spkvItv=[idx0,idx1], xgrid=xgrid)
        ent = []
        [ent.append(stats.entropy(kdefit[z])) for z in range(16)]
        plt.bar(ent)
        print(ent)
    plt.show()
    l=input()
    # print(len(kdefit[0]))
    # plt.figure()
    # for k in range(16):
    #     plt.plot(xgrid,kdefit[k],label='Taxel ' + str(k))
    # plt.legend()
    # plt.xlabel('Time (ms)')
    # plt.ylabel('Probability Density')
    # plt.show()

    #artificial textures
    #plot taxels for a given texture
    folderpath_natural = './exp_dataset_natural_30'
    resp = [np.load(folderpath_natural + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    # plt.figure()
    # for k in range(16):
    #     plt.plot(resp[k]['timev'],resp[k]['rawCurrent'][10],label='Taxel ' + str(k))
    # plt.legend()
    # plt.xlabel('Time (ms)')
    # plt.ylabel('Normalized amplitude')

    #create a new vector, selecting only the signals related to the same texture
    textureId = 0
    idx0 = textureId * 20
    idx1 = idx0 + 20
    xgrid = np.linspace(0,500,1000)
    kdefit = textrecog.analysis_kde_taxel(results_path=folderpath_natural, results=resp, spkvItv=[idx0,idx1], xgrid=xgrid)
    print(len(kdefit[0]))
    # plt.figure()
    # for k in range(16):
    #     plt.plot(xgrid,kdefit[k],label='Taxel ' + str(k))
    # plt.legend()
    # plt.xlabel('Time (ms)')
    # plt.ylabel('Probability Density')
    # plt.show()


    #natural textures
    folderpath = './exp_dataset_newnatural_30'
    xgrid = np.linspace(0,300,1000)
    kdev = textrecog.analysis_kde_class(folderpath,xgrid)

    #generate a figure with all the
    plt.figure()
    for k in range(16):
        plt.subplot(4,4,k+1)
        for w in range(len(kdev[k])):
            plt.plot(xgrid,kdev[k][w])
    plt.show()
    '''

    # numSignals = 20
    # # folderpath = './exp_dataset_artificial_30'
    # # folderpath = './exp_dataset_newnatural_30'
    # res = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    # #compute the 32-dimensional feature space
    # globalFeatures = res[0]['features']
    # for i in range(1,16):
    #     globalFeatures = np.hstack((globalFeatures,res[i]['features']))
    # print(globalFeatures.shape)
