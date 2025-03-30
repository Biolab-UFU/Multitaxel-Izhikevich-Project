import numpy as np
import matplotlib.pyplot as plt

s = np.loadtxt('slip_experiment_data.txt')

plt.figure()
plt.subplot(3,2,1)
plt.plot(s[:,4])
plt.subplot(3,2,3)
plt.plot(s[:,5])
plt.subplot(3,2,5)
plt.plot(s[:,6])

plt.subplot(3,2,2)
plt.plot(s[:,0])
plt.plot(s[:,1])
plt.plot(s[:,2])

plt.subplot(3,2,4)
plt.plot(s[:,3])

plt.show()
