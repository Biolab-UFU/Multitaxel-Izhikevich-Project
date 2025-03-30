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
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/texture_recognition')
#-------------------------------------------------------------------------------
import spiking_neurons as spkn
import numpy as np
from scipy import stats, signal
import matplotlib.pyplot as plt
#-------------------------------------------------------------------------------
#checking how average spiking rate changes over time
#-------------------------------------------------------------------------------
# toy example
#-------------------------------------------------------------------------------
sampfreq = 1000
dt = 1.0/sampfreq
timeRest = 2.0
timeStim = 10.0
ampStim = 1.0
t0 = 0
tf = int((timeRest + timeStim))
timev = np.arange(t0,tf,dt)
#no signal part
rest = np.zeros(int(timeRest*sampfreq)) #2 seconds of no signal
#dc signal
dcsig = np.ones(int(timeStim*sampfreq))*(ampStim*4)
#square wave signal
freq = 0.5
timesquare = np.arange(0,timeStim,dt)
squaresig = ampStim*(signal.square(2.0*np.pi*freq*timesquare)+1)

#generate the signals
simGain = 10
stim_dc = np.hstack((rest,dcsig))
stim_dc = stim_dc * simGain
stim_square = np.hstack((rest,squaresig))
stim_square = stim_square * simGain

#simulation
st0 = 0
stf = len(timev)
sdt = 1
Im = [stim_dc,stim_square]
n = [spkn.model.izhikevich(d=8) for k in range(2)]

#create the simulation object
simul = spkn.simulation(sdt,st0,stf,Im,n)
simul.run() #run the simulation

#convert the list of spikes to numpy arrays
for k in range(len(n)):
    simul.spikes[k] = np.array(simul.spikes[k])

#now, analyze the average spiking rate over windows
asr = [[] for k in range(2)] #vector for storing the average spiking rate
windowsize = int(0.4*sampfreq) #100 ms window
advance = 0.9 #50% advance, window moves half its size forward
#initial window
twindow0 = 0
twindow1 = windowsize

#loop through the signal
while True:
    #for each neuron, compute average spiking rate
    for k in range(len(n)):
        #find the spikes contained inside the window
        idx = np.where(np.logical_and(np.greater_equal(simul.spikes[k],twindow0),np.less(simul.spikes[k],twindow1)))
        #measure the average spiking rate -> number of spikes in the time interval
        idx = idx[0]
        avgspk = np.floor(len(idx) / (windowsize/1000.0))
        asr[k].append(avgspk)

    twindow0 += int(windowsize*(1-advance))
    twindow1 += int(windowsize*(1-advance))

    if twindow1 >= len(timev):
        break #break the loop

#remove a single point from asr
idx = np.where(np.logical_and(np.greater_equal(asr[0],40),np.less_equal(asr[0],60)))[0]
asr[0] = np.array(asr[0])
asr[0][idx] = 0

#fit kde to the distribution of asrs
xgrid = np.linspace(0,200,1000)
kdeobj = [stats.gaussian_kde(asr[k]) for k in range(len(n))]
kdefit = [kdeobj[k].evaluate(xgrid) for k in range(len(n))]

#now, compute entropy
print('entropy dc ' + str(stats.entropy(kdefit[0],base=2)))
print('entropy square ' + str(stats.entropy(kdefit[1],base=2)))

#plot the inputs
plt.figure()
plt.subplot(2,1,1)
plt.plot(timev,stim_dc)
plt.subplot(2,1,2)
plt.plot(timev,stim_square)

#plot the membrane voltage
ratiodc = len(simul.timen[0]) / len(asr[0])
ratiosquare = len(simul.timen[0]) / len(asr[0])
tdc = np.arange(0,len(simul.timen[0]),ratiodc)
print(len(simul.timen[0]),len(tdc))
plt.figure()
plt.subplot(2,1,1)
plt.plot(simul.timen[0],simul.vneurons[0])
# plt.plot(tdc,asr[0],color='r')
plt.subplot(2,1,2)
plt.plot(simul.timen[1],simul.vneurons[1])

#plot the average spiking rate over time
plt.figure()
plt.subplot(2,1,1)
plt.plot(asr[0],marker='*')
plt.subplot(2,1,2)
plt.plot(asr[1],marker='*')

#plot the KDE fit
plt.figure()
plt.subplot(2,1,1)
plt.plot(xgrid,kdefit[0])
plt.subplot(2,1,2)
plt.plot(xgrid,kdefit[1])


p0,b0 = np.histogram(asr[0],bins='auto')
p1,b1 = np.histogram(asr[1],bins='auto')
plt.figure()
plt.subplot(2,1,1)
plt.bar(b0[0:len(b0)-1],p0)
plt.subplot(2,1,2)
plt.bar(b1[0:len(b1)-1],p1)
plt.show()
#-------------------------------------------------------------------------------
# 1) load the results from processing
# results = [np.load('./exp_dataset_natural_noise_30/results_taxel' + str(k) + '.npz') for k in range(16)]
# 2) from the results,
# 3)
# 4)
# 5)
# 6)
# 7)
#-------------------------------------------------------------------------------
