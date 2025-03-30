import numpy as np
import matplotlib.pyplot as plt

s = np.loadtxt('sensors_data.txt')

plt.figure()
plt.plot(s)
plt.show()
