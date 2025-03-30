import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt

NROWS = 4
NCOLS = 4
NPATCH = 5
NTAXELS = NROWS * NCOLS

s = np.loadtxt('s7.txt')
n = len(s)

[b,a] = sig.butter(4,(400/500),'low')
for k in range(80):
	s[:,k] = sig.filtfilt(b,a,s[:,k])

sx = [np.zeros((n,16)) for k in range(5)]

p = 0
j = 0
i = 0

for k in range(n):
	for w in range(0,80):
		col = 4*i + j
		sx[p][k,col] = s[k,w]
		p += 1
		if p >= NPATCH:
			p = 0
			j += 1
			if j >= NCOLS:
				j = 0
				i += 1
				if i >= NROWS:
					i = 0

for z in range(5):
	plt.figure()
	for k in range(16):
		plt.subplot(NROWS,NCOLS,k+1)
		plt.plot(sx[z][:,k])
plt.show()
