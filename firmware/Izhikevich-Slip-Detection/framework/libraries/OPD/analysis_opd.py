import numpy as np
import matplotlib.pyplot as plt

sampfreq = 2000
dt = 1./sampfreq
s = np.loadtxt('opd_data_IR_slide.txt')
t = np.arange(0,len(s))
t = t*dt

# ambient_light = np.mean(s[sampfreq*12:sampfreq*14,:],axis=0)
# no_light = np.mean(s[sampfreq*2:sampfreq*4,:],axis=0)

# print('ambient light')
# print(ambient_light)
# print('no light')
# print(no_light)

plt.figure()
plt.plot(t,s)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (V)')
plt.title('OPD: No light and ambient light')
plt.show()