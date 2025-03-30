'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Neuromorphic Engineering and Robotics Group - NER
#-------------------------------------------------------------------------------
# Description: Library for handling spiking neurons
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# LIBRARIES
#-------------------------------------------------------------------------------
import sys
sys.path.append('../../../framework/libraries/neuromorphic')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import scipy.signal as sig
import scipy.stats as stats
import spiking_neurons as spkn #library for handling spiking neurons
from sklearn import neighbors, datasets
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Load all the files related to a texture
#Each taxel will generate one simulation object where the number of neurons is
#equal to the number of textures.
#Therefore, it is possible to generate a rastergram for a specific taxel over
#all different textures
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Starting with only one taxel
#-------------------------------------------------------------------------------
#determine the files to be loaded
fileprefix = './dataset/'
filenames = []
numSignals = 10
#filenames.append(['SmallDots_Ite0.txt','SmallDots_Ite1.txt'])
for k in range(numSignals):
    filenames.append(fileprefix + 'newdata_' + str(k) + '.txt')
for k in range(numSignals):
    filenames.append(fileprefix + 'newdataf_' + str(k) + '.txt')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PARAMETERS RELATED TO THE TACTILE SENSORS
NROWS = 4
NCOLS = 4
NTAXELS = NROWS*NCOLS
#-------------------------------------------------------------------------------
#loading the textures
totalNumInputs = len(filenames)
numTextures = int(totalNumInputs / numSignals)
textures = [[] for k in range(totalNumInputs)]
textureNames = []
textureNamesPlot = []
aux = 0
for k in range(totalNumInputs):
    print('loading file:',filenames[k])
    textures[k] = np.loadtxt(filenames[k])
    textureNames.append(filenames[k].split(fileprefix)[1].split('.')[0].split('_')[0])
    # #only save the name of the texture, avoid repetitions
    if k==0 or k%aux == 0:
        textureNamesPlot.append(filenames[k].split(fileprefix)[1].split('.')[0].split('_')[0])
        aux += numSignals
colorsPlot = ['k','r','b','g','y','c','m']
# textureNames = list(set(textureNames))
print(textureNamesPlot) #debugging
# print(set(textureNames)) #debugging
# a = input() #debugging
#-------------------------------------------------------------------------------
#low-pass filter
sampfreq = 1000 #sampling frequency
n = 6 #filter order
fc = 30 #cut-off frequency
wn = fc/(sampfreq/2) #filter parameter
[b,a] = sig.butter(n,wn,'low') #create the filter
#-------------------------------------------------------------------------------
#simulation parameters
#find the minimum length of the signals
maxTime = np.min([len(k) for k in textures])
#cut the signals so that all of them have the same length
textures = [x[0:maxTime] for x in textures]
# dt = 1 #1kHz sampling rate
dt = 1
t0 = 0
tf = maxTime
t = np.arange(0,maxTime+1)
t = t*dt
tf = t[-1]
#-------------------------------------------------------------------------------
#for each taxel, create a separate simulation object where each neuron
#will receive its input from a different texture
#for all the taxels
simul = [[] for k in range(NTAXELS)]
rasters = [[] for k in range(NTAXELS)]
isihist = [[] for k in range(NTAXELS)]
currents = [[] for k in range(NTAXELS)]
isicv = [[] for k in range(NTAXELS)]
isifr = [[] for k in range(NTAXELS)]
featuresKNN = [[] for k in range(NTAXELS)]
vpd = [[] for k in range(NTAXELS)]
vrm = [[] for k in range(NTAXELS)]
isidist = [[] for k in range(NTAXELS)]
GF = 50
taxelsProc = np.arange(0,NTAXELS)
# taxelsProc = [0]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# SIMULATION
#-------------------------------------------------------------------------------
for k in range(len(taxelsProc)):
    taxel = taxelsProc[k]
    #get the corresponding filtered input
    textureCurrent = [sig.filtfilt(b,a,x[:,taxel]) for x in textures]
    #save the current
    currents[k] = textureCurrent
    #creating the neurons
    neurons = [spkn.model.izhikevich(a=0.02,b=0.2,c=-65,d=8,name=str(k+1)+'_'+textureNames[k]) for k in range(totalNumInputs)]
    #normalizing the currents
    #take the maximum value accross all the textures for the same taxel and
    #normalize based on this value
    maxAmp = np.max([np.max(x) for x in currents[k]])
    #normalize with respect to the texture with maximum activation
    currents[k] = [((x/maxAmp))*GF for x in currents[k]]
    # currents[k] = [((x+0.5)*GF) for x in currents[k]]
    # currents[k] = [(x/np.max(x))*GF for x in currents[k]]
    #simulation object
    simul[k] = spkn.simulation(dt=dt,t0=t0,tf=tf,I=currents[k],neurons=neurons)
    #run the simulation
    print('Simulation of Taxel:',str(taxel+1))
    simul[k].run()
    print('Simulation finished')
    #retrieve results for rasterplot
    print('Processing rastergram...')
    rasters[k] = spkn.analysis.raster(simul[k])
    #retrieve results for histogram
    print('Processing PSTH...')
    isihist[k] = spkn.analysis.isi_histogram(simul[k],numSignals,type='gaussian')
    #feature extraction from the spike trains
    #according to Rongala et al., 2015
    print('k-NN classification...')
    featuresKNN[k] = spkn.classification.feature_extraction(simul[k],numSignals)
    #Victor Purpura Distance (VPD)
    # print('Victor-Purpura Distance...')
    # vpd[k] = spkn.distance.victor_purpura(simul[k],5)
    # #Van Rossum Distance
    # print('Van Rossum Distance...')
    # vrm[k] = spkn.distance.van_rossum(simul[k],0.096)
    #ISI Distance
    print('ISI Distance...')
    isidist[k] = spkn.distance.isi(simul[k])
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# CLASSIFICATION OF THE SPIKE TRAINS
#-------------------------------------------------------------------------------
filereport = open('classification_report.txt','w')
n_neighbors = 6
clf = neighbors.KNeighborsClassifier(n_neighbors,weights='distance')
conf = []
rep = []
for k in range(len(taxelsProc)):
    resp = spkn.classification.LOOCV(clf,featuresKNN[k].features,featuresKNN[k].targets,target_names=textureNamesPlot)
    conf.append(resp[0])
    rep.append(resp[1])
    filereport.write('\n')
    filereport.write('CLASSIFICATION PERFORMANCE: TAXEL ' + str(k+1) + '\n')
    filereport.write(resp[1])
    filereport.write('\n')
    filereport.write('CONFUSION MATRIX\n')
    for i in range(numTextures):
        for j in range(numTextures):
            filereport.write(str(conf[k][i,j]) + ' ')
        filereport.write('\n')
    filereport.write('\n')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PLOTS
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#defines the colors for each class
colors = ['r','g','y','b','k','c','m']
#-------------------------------------------------------------------------------
#plot all the inputs
plt.figure()
for k in range(len(taxelsProc)):
    plt.subplot(NROWS,NCOLS,k+1)
    for w in range(len(simul[k].neurons)):
        plt.plot(simul[k].timev,simul[k].I[w])
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot one input of each texture per taxel
plt.figure()
for k in range(len(taxelsProc)):
    ax = plt.subplot(NROWS,NCOLS,k+1)
    auxv = 0
    for w in range(0,len(simul[k].neurons),numSignals):
        plt.plot(simul[k].timev,simul[k].I[w],c=colors[auxv],label=textureNamesPlot[auxv])
        auxv += 1
    if k == NTAXELS-1:
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,box.width, box.height * 0.9])
        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),fancybox=True, shadow=True, ncol=5)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot the rastergrams
plt.figure()
for k in range(len(taxelsProc)):
    plt.subplot(NROWS,NCOLS,k+1)
    for w in range(len(simul[k].neurons)):
        plt.scatter(rasters[k].xvals[w],rasters[k].yvals[w],c='k',marker='|')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot one raster of each texture per taxel
plt.figure()
for k in range(len(taxelsProc)):
    plt.subplot(NROWS,NCOLS,k+1)
    for w in range(0,len(simul[k].neurons),numSignals):
        plt.scatter(rasters[k].xvals[w],rasters[k].yvals[w],c='k',marker='|')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot one membrane voltage for each texture
# plt.figure()
# auxv1 = 1
# auxv2 = 0
# for k in range(numTextures):
#     # print(len(simul[4].timev),len(simul[4].I[idx]))
#     if k%2 == 0:
#         plt.subplot(numTextures,2,auxv1)
#         plt.plot(simul[4].timev,simul[4].I[auxv2])
#         auxv2 += numSignals
#         plt.subplot(numTextures,2,auxv1+1)
#         plt.plot(simul[4].timev,simul[4].I[auxv2])
#         auxv1 += 2
#     else:
#         auxv2 -= numSignals
#         plt.subplot(numTextures,2,auxv1)
#         plt.plot(simul[4].timen[auxv2],simul[4].vneurons[auxv2])
#         auxv2 += numSignals
#         plt.subplot(numTextures,2,auxv1+1)
#         plt.plot(simul[4].timen[auxv2],simul[4].vneurons[auxv2])
#         auxv1 += 2
#         auxv2 += numSignals
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot the gaussians
plt.figure()
for k in range(len(taxelsProc)):
    ax = plt.subplot(NROWS,NCOLS,k+1)
    for w in range(numTextures):
        if k < NTAXELS-1:
            plt.plot(isihist[k].xvals[w],isihist[k].yvals[w],c=colors[w])
        else:
            plt.plot(isihist[k].xvals[w],isihist[k].yvals[w],label=textureNamesPlot[w],c=colors[w])
        plt.xlim([0,170])
    if k == NTAXELS-1:
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,box.width, box.height * 0.9])
        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),fancybox=True, shadow=True, ncol=5)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot the features
plt.figure()
for k in range(len(taxelsProc)):
    aux=0
    auxname = 0
    ax = plt.subplot(NROWS,NCOLS,k+1)
    for w in range(numTextures):
        if k<NTAXELS-1:
            plt.scatter(featuresKNN[k].features[aux:aux+numSignals,0],featuresKNN[k].features[aux:aux+numSignals,1],color=colors[w])
        else:
            # print(textureNamesPlot[w]) #debugging
            plt.scatter(featuresKNN[k].features[aux:aux+numSignals,0],featuresKNN[k].features[aux:aux+numSignals,1],color=colors[w],label=textureNamesPlot[w])
        aux += numSignals
    if k == NTAXELS-1:
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,box.width, box.height * 0.9])
        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),fancybox=True, shadow=True, ncol=5)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#plot the confusion matrices
#-------------------------------------------------------------------------------
plt.figure()
for k in range(len(taxelsProc)):
    plt.subplot(NROWS,NCOLS,k+1)
    cax = plt.matshow(conf[k],fignum=False,vmin=0,vmax=numSignals)
    plt.colorbar()
    tick_marks = np.arange(numTextures)
    # plt.xticks(tick_marks,textureNamesPlot)
    plt.yticks(tick_marks,textureNamesPlot)
#-------------------------------------------------------------------------------
# plot the overall accuracy
filereport.write('\n')
filereport.write('Overall accuracy')
filereport.write('\n')
idx = np.arange(0,numTextures)
r=0; c=0
matacc = np.zeros((NROWS,NCOLS))
for k in range(len(taxelsProc)):
    matacc[c,r] = 100 * (np.sum(conf[k][idx,idx]) / (numSignals * numTextures))
    filereport.write(str(matacc[c,r])+ ' ')
    r += 1
    if r >= NROWS:
        r = 0
        c += 1
        filereport.write('\n')
filereport.close()
plt.figure()
plt.matshow(matacc,fignum=False,vmin=0,vmax=100)
plt.colorbar()
#-------------------------------------------------------------------------------
# plot the spike-train distances
#VPD
# plt.figure()
# for k in range(len(taxelsProc)):
#     plt.subplot(NROWS,NCOLS,k+1)
#     plt.matshow(vpd[k],fignum=False)
#     plt.colorbar()
# #VRM
# plt.figure()
# for k in range(len(taxelsProc)):
#     plt.subplot(NROWS,NCOLS,k+1)
#     plt.matshow(vrm[k],fignum=False)
#     plt.colorbar()
#ISI
plt.figure()
for k in range(len(taxelsProc)):
    plt.subplot(NROWS,NCOLS,k+1)
    plt.matshow(isidist[k],fignum=False,vmin=0,vmax=1)
    plt.colorbar()
#-------------------------------------------------------------------------------
#show the figures
plt.show()
