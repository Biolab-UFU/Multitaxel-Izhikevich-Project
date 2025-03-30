import numpy as np
import matplotlib.pyplot as plt

x = np.loadtxt('slip_experiment_water_transparent_dath_1.txt')

pulsesWater = x[:,-1]
totalPulses = pulsesWater[-1] + 1

#find the amount of water per pulse given known volume
volume = 150 #mL
waterPulse = volume / totalPulses
print('total pulses: ' + str(totalPulses))
print('water per pulse: ' + str(waterPulse))

#generate the volume signal
volumeSignal = pulsesWater * waterPulse

plt.figure()
plt.plot(x[:,8])

plt.figure()
plt.plot(volumeSignal)
plt.show()
