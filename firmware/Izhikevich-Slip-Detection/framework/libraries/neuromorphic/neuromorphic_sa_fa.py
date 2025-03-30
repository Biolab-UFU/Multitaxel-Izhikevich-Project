# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Neuromorphic Engineering and Robotics Group - NER
# Singapore
#-------------------------------------------------------------------------------
# Description:
#   Example for reading a file containing tactile data and generating spikes
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
# LIBRARIES
#-------------------------------------------------------------------------------
import sys
sys.path.append('../general') #add folder to system path
import numpy as np #numpy
import scipy.signal as sig #signal library: low pass filter
import matplotlib.pyplot as plt #matplotlib
from dataprocessing import * #function for normalizing the signal (convscale)
from tactileboard import * #file that handles the tactile board
import spiking_neurons as spkn #library for spiking neurons
#-------------------------------------------------------------------------------
#step 1
#read a texture file
textureData = np.loadtxt('texture_3_007_10_Ite0.txt')

#step 2
#pre-processing
#1) create a low-pass filter
filtorder = 4
lowfc = 30 #cut-off frequency
wn = lowfc / (TBCONSTS.SAMPFREQ/2.0)
#find the coefficients of the low-pass filter
b,a = sig.butter(filtorder,wn,'low')
#filter the data
filtTextureData = [sig.filtfilt(b,a,textureData[:,k]) for k in range(TBCONSTS.NTAXELS)]
#2) normalize the signal
#take the first second of data as reference
normT0 = int(0) #initial time of baseline
normT1 = int(1.0 * TBCONSTS.SAMPFREQ) #final time of baseline
#get a mean value during the baseline (no activation) for each individual taxel
meanBV = [np.mean(filtTextureData[k][normT0:normT1]) for k in range(TBCONSTS.NTAXELS)]
#generate the normalized filtered tactile data
finalTextureData = [convscale(x=filtTextureData[k], xmin=meanBV[k], xmax=0, ymin=0, ymax=1) for k in range(TBCONSTS.NTAXELS)]

#step 3
#neuromorphic model of SA-I and FA-I receptors
#create 16 (4x4) SA neurons
simSA = [spkn.model.izhikevich(a=0.02, b=0.2, c=-65, d=8) for k in range(TBCONSTS.NTAXELS)]
#create 16 (4x4) FA neurons
simFA = [spkn.model.izhikevich(a=0.1, b=0.2, c=-65, d=2) for k in range(TBCONSTS.NTAXELS)]

#create the simulation parameters
sim_dt = 1 #sampling rate of the board = 1 kHz
sim_t0 = 0 #initial time (in ms)
sim_tf = len(textureData) #final time for the simulation (in ms)
sim_GF = 100 #gain factor: it is necessary to amplify the signals in order to generate spikes

#create the input currents
#input for SA neurons
simSA_I = [finalTextureData[k]*sim_GF for k in range(TBCONSTS.NTAXELS)]
#input for FA neurons
simFA_I = [np.abs(np.insert(np.diff(finalTextureData[k]*sim_GF),0,0))*sim_GF for k in range(TBCONSTS.NTAXELS)]

#simulation for SA neurons
#create the object
simSA_obj = spkn.simulation(dt=sim_dt,t0=sim_t0,tf=sim_tf,I=simSA_I,neurons=simSA)
#run the simulation
simSA_obj.optIzhikevich()
#get the rastergram
simSA_rasters = spkn.analysis.raster(simSA_obj)

#simulation for FA neurons
#create the object
simFA_obj = spkn.simulation(dt=sim_dt,t0=sim_t0,tf=sim_tf,I=simFA_I,neurons=simFA)
simFA_obj.optIzhikevich()
#get the rastergram
simFA_rasters = spkn.analysis.raster(simFA_obj)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PLOTS
#-------------------------------------------------------------------------------
#plot the SA inputs together
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.plot(simSA_obj.timev, simSA_I[k], label='taxel ' + str(k))
plt.xlim([simSA_obj.timev[0], simSA_obj.timev[-1]])
plt.xlabel('Time (ms)')
plt.title('SA-I inputs')
plt.legend()

#plot the FA inputs together
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.plot(simFA_obj.timev, simFA_I[k], label='taxel ' + str(k))
plt.xlim([simFA_obj.timev[0], simFA_obj.timev[-1]])
plt.xlabel('Time (ms)')
plt.title('FA-I inputs')
plt.legend()


# plot the SA inputs individually
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
    plt.plot(simSA_obj.timev, simSA_I[k])
    plt.xlim([simSA_obj.timev[0], simSA_obj.timev[-1]])
    plt.xlabel('Time (ms)')

# plot the FA inputs individually
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
    plt.plot(simFA_obj.timev, simFA_I[k])
    plt.xlim([simFA_obj.timev[0], simFA_obj.timev[-1]])
    plt.xlabel('Time (ms)')

#rastergram for the SA neurons
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.scatter(simSA_rasters.xvals[k], simSA_rasters.yvals[k], color='k', marker='|')
    plt.xlim([simSA_obj.timev[0], simSA_obj.timev[-1]])
plt.xlabel('Time (ms)')
plt.ylabel('Neuron id')
plt.title('SA-I rastergram')

#rastergram for the FA neurons
plt.figure()
for k in range(TBCONSTS.NTAXELS):
    plt.scatter(simFA_rasters.xvals[k], simFA_rasters.yvals[k], color='k', marker='|')
    plt.xlim([simSA_obj.timev[0], simSA_obj.timev[-1]])
plt.xlabel('Time (ms)')
plt.ylabel('Neuron id')
plt.title('FA-I rastergram')

plt.show()
#-------------------------------------------------------------------------------
