#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
import sys
sys.path.append('../../framework/libraries/general')
sys.path.append('../../framework/libraries/neuromorphic')
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
from multiprocessing import Pool
import time
from dataprocessing import *
import spiking_neurons as spkn
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def load_tactile(filename):
    global NTAXELS
    s = np.loadtxt(filename)
    return [s[:,k] for k in range(NTAXELS)]
#-------------------------------------------------------------------------------
def processing(signals):
    global time_cut_begin, time_cut_end, filtb, filta, NTAXELS
    braille_letters = [signals[0][time_cut_begin[w]:time_cut_end[w]] for w in range(numBraille)]
    baseline = np.mean(signals[0][0:500])
    for w in range(numBraille):
        braille_letters[w] = convscale(braille_letters[w],baseline,0.6*baseline,0,1)
        braille_letters[w] = sig.filtfilt(filtb,filta,braille_letters[w])
    return braille_letters
#-------------------------------------------------------------------------------
def processing_taxels(signals):
    global time_cut_begin, time_cut_end, filtb, filta, NTAXELS
    braille_taxels = [[] for w in range(NTAXELS)]
    for i in range(NTAXELS):
        braille_letters = [signals[i][time_cut_begin[w]:time_cut_end[w]] for w in range(numBraille)]
        baseline = np.mean(signals[i][0:500])
        for w in range(numBraille):
            braille_letters[w] = convscale(braille_letters[w],baseline,0.6*baseline,0,1)
            braille_letters[w] = sig.filtfilt(filtb,filta,braille_letters[w])
        braille_taxels[i] = braille_letters
    return braille_taxels
#-------------------------------------------------------------------------------
def spikes_braille_letter(signals):
    global numRep, GF
    # print('size',len(signals))
    dt = 1
    t0 = 0
    tf = len(signals[0])
    nrn = [spkn.model.izhikevich() for k in range(numRep)]
    im = [GF*x for x in signals]
    simulobj = spkn.simulation(dt=dt,t0=t0,tf=tf,I=im,neurons=nrn)
    simulobj.optIzhikevich()
    asrv = []
    cvisiv = []
    for k in range(numRep):
        if len(simulobj.spikes[k]) > 0:
            asr = len(simulobj.spikes[k])/(tf/1000)
            if len(simulobj.spikes[k]) > 1:
                print(simulobj.spikes[k])
                isiv = np.diff(np.array(simulobj.spikes[k]))
                cvisi = np.std(isiv) / np.mean(isiv)
            else:
                cvisi = 0
        else:
            asr = 0
            cvisi = 0
        asrv.append(asr)
        cvisiv.append(cvisi)
    return simulobj,asrv,cvisiv
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#experiment parameters
NTAXELS = 16
numBraille = 6
numRep = 40
time_cut_begin = [6000,8700,11860,14670,32066,35083,37500]
time_cut_end = [8700,11860,14670,32066,35083,37500]
ford = 4
sampfreq = 1000
wn = 10/(sampfreq/2)
filtb,filta = sig.butter(ford,wn,'low')
GF = 40
#-------------------------------------------------------------------------------
#file parameters
fileprefix = './data/braille_Ite'
#-------------------------------------------------------------------------------
filenames = [fileprefix + str(i) + '.txt' for i in range(40)]
# print(filenames)
print('loading the files....')
t0 = time.time()
pool = Pool()
x = pool.map(load_tactile,filenames)
pool.close()
pool.join()
tf = time.time()
print('done!', tf-t0)

# print(len(x))
# print(x[0][0][0:10])
print('processing...')
t0 = time.time()
pool = Pool()
y = pool.map(processing_taxels,x)
tf = time.time()
print('done!', tf-t0)
#
# print(len(y))
# print(len(y[0]))
# print(len(y[0][0][0]))
# print(len(y[0][0][0][0]))

#now, analyze individual taxels
for i in range(NTAXELS):
    print('analyzing taxel: ' + str(i))
    t0 = time.time()
    asrv = []
    cvisiv = []
    for j in range(numBraille):
        braille_data = [[] for w in range(numBraille)]
        for w in range(numRep):
            braille_data[j].append(y[w][i][j])
        # print(len(braille_data[j]))
        resp_simul,asr,cvisi = spikes_braille_letter(braille_data[j])
        asrv.extend(asr)
        cvisiv.extend(cvisi)
        rast = spkn.analysis.raster(resp_simul)
    plt.figure()
    for k in range(numBraille):
        plt.scatter(asrv[k*numRep:k*numRep+numRep],cvisiv[k*numRep:k*numRep+numRep],label=str(k))
    plt.legend()
    plt.show()
    tf = time.time()
    print('done!', tf-t0)

    #     plt.figure()
    #     plt.plot(braille_data[0][0])
    # plt.show()
    #     # plt.figure()
        # for w in range(numRep):
        #     plt.scatter(rast.xvals[w],rast.yvals[w],color='black',marker='|')
        # plt.show()

# t0 = time.time()
# braille_data = [[] for w in range(numBraille)]
# for i in range(numBraille):
#     for j in range(numRep):
#         braille_data[i].append(y[j][i])
# tf = time.time()
# print(tf-t0)
#
# t0 = time.time()
# resp_simul = spikes_braille_letter(braille_data[1])
# rast = spkn.analysis.raster(resp_simul)
# tf = time.time()
# print(tf-t0)
# print('raster',len(rast.xvals))
# plt.figure()
# for w in range(numRep):
#     plt.scatter(rast.xvals[w],rast.yvals[w],color='black',marker='|')
# plt.show()
#
# print(len(y))
# print(len(y[0]))
# plt.figure()
# plt.plot(y[0][0])
# plt.show()

# t0 = time.time()
# for i in range(40):
#     filename = fileprefix + str(i) + '.txt'
#     print('loading file: ' + filename)
#     tactile_signal = np.loadtxt(filename)
#     tactile_signal = [tactile_signal[:,x] for x in range(16)]
# tf = time.time()
# print(tf-t0)
#     # plt.figure(); plt.plot(tactile_signal); plt.show()
#     plt.figure()
#     for w in range(numBraille):
#         plt.subplot(6,1,w+1)
#         t0 = time_cut_begin[w]
#         tf = time_cut_end[w]
#         plt.plot(tactile_signal[t0:tf,0])
#     plt.show()
# #-------------------------------------------------------------------------------
