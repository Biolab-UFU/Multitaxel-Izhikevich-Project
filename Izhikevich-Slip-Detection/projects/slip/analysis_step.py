'''
summary results
transparent
fth: 30% ok, RT: [57, 63, 45], TT [396, 663, 579]: RMS: []
PV: [], AREA: []

dath: 70% ok, RT: [54, 60, 48, 51, 42, 45], TT: [272, 276, 265, 456, 258, 264]
RMS: [1.91, 1.81, 1.92, 1.15, 1.97, 2.02] PV: [3.1, 3.05, 3.13, 2.34, 3.04, 3.13], AREA: [161, 144, 146, 141, 156, 168]

dark
fth: 40% ok, RT: [54, 192, 75, 54], TT [432, 516, 588, 300]: RMS: [1.28, 0.89, 1.04, 1.49] PV: [2.66, 2.25, 2.53, 3.05]
AREA: [149, 125, 152, 117]
dath 60% ok, RT: [60, 99, 123, 84, 75], TT: [330, 315, 501, 381, 264], RMS: [1.35, 1.25, 1.62, 1.42, 1.53]
PV: [2.67, 2.4, 3.25, 2.49, 2.65] AREA: [126, 111, 166, 166, 122],

textured
fth  90% ok, RT: [48, 42], TT [453, 285]:
dath 90% ok, RT: [36, 28, 30], TT [252, 297, 273]:
'''

import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt

# filename = 'slip_experiment_pouring_textured_3.txt'
# filename = 'slip_experiment_pouring_dark_16.txt'
# filename = 'slip_experiment_pouring_dark_fixed_2.txt'
# filename = 'slip_experiment_pouring_dark_dath_5_5_6.txt'
# filename = 'slip_experiment_pouring_transparent_11.txt'
# filename = 'slip_experiment_pouring_transparent_dath_5_5_1.txt'
# filename = 'slip_experiment_pouring_dark_dath_5_5_2.txt'
# filename = 'slip_experiment_step_textured_dath_5_5_1.txt'
# filename = 'slip_experiment_step_textured_dath_5_5_1.txt'
filename = 'slip_experiment_step_textured_fth_5_5_20.txt'
# filename = 'slip_experiment_step_textured_fth_5_5_14.txt'
# filename = 'slip_experiment_step_transparent_fth_5_5_4.txt'

s = np.loadtxt(filename)

initPos = 115
resAccel = np.sqrt(np.power(s[:,0],2) + np.power(s[:,1],2) + np.power(s[:,2],2))
controlSignal = s[:,7]
opticSignal = s[:,5]
eventSignal = s[:,6]

#create the time vector
sampfreq = 333
timev = np.arange(0,len(s)) * (1/sampfreq)

# bestAccel = np.abs(s[:,2]) - (np.power(2,16)/4) #y-axis provided best response
#convert to g
bestAccel = 9.8 * (s[:,1] / (np.power(2,16)))
[b,a] = sig.butter(4,15/(333/2),'low')
bestAccel = sig.filtfilt(b,a,np.abs(bestAccel))
#convert to g

#finding the onset of slip
th = np.mean(bestAccel[300:500]) + 100*np.std(bestAccel[300:500])
print(th)
aux_onset_slip = np.where(bestAccel > th)[0]
aux_onset_slip = aux_onset_slip[np.where(aux_onset_slip > (2*333))[0]]
onset_slip = aux_onset_slip[0]
offset_slip = aux_onset_slip[-1]

#offset of slip is the last change in position given by the controller
aux_offset_slip = np.where(controlSignal == controlSignal[-1])[0]
offset_slip = aux_offset_slip[0]
print(onset_slip, offset_slip)
# offset_slip = aux_onset_slip[aux_offset_slip[-1]]

#measure the power of the accelerometer signal
accelsig = bestAccel[onset_slip:offset_slip]
accelsig = accelsig - np.mean(accelsig)
accelsig = accelsig / np.max(np.abs(accelsig))
plt.figure(); plt.plot(accelsig); plt.show()
print('area: ' + str(np.trapz(accelsig)))
print('peak vel: ' + str(np.max(accelsig)))
print('rms: ' + str(np.sqrt(np.mean(np.power(accelsig,2)))))

#measuring response time
#find the index where position started to increase
onset_pos = np.where(controlSignal > controlSignal[0])[0][0]
print(onset_pos)
response_slip_time = timev[onset_pos] - timev[onset_slip]

#measuring total time
total_slip_time = timev[offset_slip] - timev[onset_slip]

print(onset_slip, offset_slip)
print('response time: ' + str(response_slip_time))
print('total time: ' + str(timev[offset_slip] - timev[onset_slip]))

plt.figure()
plt.subplot(4,1,1)
plt.plot(timev,bestAccel)
plt.scatter(timev[onset_slip], bestAccel[onset_slip],marker='o',color='r')
plt.scatter(timev[offset_slip], bestAccel[offset_slip],marker='o',color='r')
# plt.plot(s[:,1])
# plt.plot(s[:,2])
plt.subplot(4,1,2)
plt.plot(timev,opticSignal)
plt.scatter(timev[onset_slip], opticSignal[onset_slip],marker='o',color='r')
plt.scatter(timev[offset_slip], opticSignal[offset_slip],marker='o',color='r')
plt.subplot(4,1,3)
plt.plot(timev,eventSignal)
plt.scatter(timev[onset_slip], eventSignal[onset_slip],marker='o',color='r')
plt.scatter(timev[offset_slip], eventSignal[offset_slip],marker='o',color='r')
plt.subplot(4,1,4)
plt.plot(timev,controlSignal)
plt.scatter(timev[onset_slip], controlSignal[onset_slip],marker='o',color='r')
plt.scatter(timev[offset_slip], controlSignal[offset_slip],marker='o',color='r')
plt.show()

# resAccel = np.sqrt(np.power(s[:,0],2) + np.power(s[:,1],2) + np.power(s[:,2],2))
# controlSignal = s[:,7]
# opticSignal = s[:,5]
# eventSignal = s[:,6]
#
#
# # bestAccel = np.abs(s[:,2]) - (np.power(2,16)/4) #y-axis provided best response
# #convert to g
# bestAccel = s[:,1] / (np.power(2,16))
# [b,a] = sig.butter(4,15/(333/2),'low')
# bestAccel = sig.filtfilt(b,a,np.abs(bestAccel))
# #convert to g
#
# #finding the onset of slip
# th = np.mean(bestAccel[2000:2200]) + 3*np.std(bestAccel[2000:2200])
# print(th)
# aux_onset_slip = np.where(bestAccel > th)[0]
# aux_onset_slip = aux_onset_slip[np.where(aux_onset_slip > 2200)[0]]
# onset_slip = aux_onset_slip[0]
# print(onset_slip)
#
# #create the time vector
# sampfreq = 333
# timev = np.arange(0,len(s)) * (1/sampfreq)
#
# #bring position of finger back to zero-reference
# controlSignal = controlSignal - initPos
#
# #making the first part of the signal equal to zero
# s[0:1000,6] = 0
#
# #finding the offset of slip
# offset_slip = aux_onset_slip[-1]
#
# #measuring reaction time
# #find the time where the position of the finger started increasing
# onset_control = np.where(controlSignal > controlSignal[0])[0][0]
# print(onset_control)
# responseTime = (onset_control - onset_slip) * (1/sampfreq)
# print(responseTime)
#
# #measuring total time
# totalTime = (offset_slip - onset_slip) * (1/sampfreq)
# print(totalTime)
#
# #correct the plot
# tcut_begin = 4.5
# tcut_end = tcut_begin + 8.0
# idxSignalBegin = np.where(timev >= tcut_begin)[0]
# idxSignalEnd = int(tcut_end * sampfreq)
# print('idx begin', idxSignalBegin)
# print('idx end', idxSignalEnd)
#
# timev = timev[idxSignalBegin[0]:idxSignalEnd]
# timev = timev - tcut_begin
# bestAccel = bestAccel[idxSignalBegin[0]:idxSignalEnd]
# opticSignal = opticSignal[idxSignalBegin[0]:idxSignalEnd]
# eventSignal = eventSignal[idxSignalBegin[0]:idxSignalEnd]
# controlSignal = controlSignal[idxSignalBegin[0]:idxSignalEnd]
# onset_slip -= idxSignalBegin[0]
# offset_slip -= idxSignalBegin[0]
#
# # plt.figure()
# # plt.subplot(3,1,1)
# # plt.plot(s[:,0])
# # plt.subplot(3,1,2)
# # plt.plot(s[:,1])
# # plt.subplot(3,1,3)
# # plt.plot(s[:,2])
#
# #plot configuration
# SMALL_SIZE = 14
# MEDIUM_SIZE = 14
# BIGGER_SIZE = 16
#
# plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
# plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
# plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
# plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
# plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
# plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
# plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
#
# plt_markersize = 7**2
#
# plt.figure()
# plt.subplot(4,1,1)
# # plt.plot(np.abs(resAccel))
# # plt.plot(s[:,0])
# plt.plot(timev,bestAccel,color='k')
# # plt.plot([timev[0],timev[-1]],[th,th],'r')
# plt.scatter(timev[onset_slip],bestAccel[onset_slip],color='r',marker='o',s=plt_markersize)
# plt.scatter(timev[offset_slip],bestAccel[offset_slip],color='r',marker='o',s=plt_markersize)
# plt.ylabel('Acceleration (g)')
# # plt.plot(s[:,2])
# plt.subplot(4,1,2)
# plt.plot(timev,opticSignal,color='k')
# plt.scatter(timev[onset_slip],opticSignal[onset_slip],color='r',marker='o',s=plt_markersize)
# plt.scatter(timev[offset_slip],opticSignal[offset_slip],color='r',marker='o',s=plt_markersize)
# plt.ylabel('Sensor output (V)')
# plt.subplot(4,1,3)
# plt.plot(timev,eventSignal,color='k')
# plt.scatter(timev[onset_slip],eventSignal[onset_slip],color='r',marker='o',s=plt_markersize)
# plt.scatter(timev[offset_slip],eventSignal[offset_slip],color='r',marker='o',s=plt_markersize)
# plt.ylabel('Events')
# plt.subplot(4,1,4)
# plt.plot(timev,controlSignal,color='k')
# plt.scatter(timev[onset_slip],controlSignal[onset_slip],color='r',marker='o',s=plt_markersize)
# plt.scatter(timev[offset_slip],controlSignal[offset_slip],color='r',marker='o',s=plt_markersize)
# plt.ylabel('MPI Output')
#
# plt.xlabel('Time (s)')
#
# plt.show()
