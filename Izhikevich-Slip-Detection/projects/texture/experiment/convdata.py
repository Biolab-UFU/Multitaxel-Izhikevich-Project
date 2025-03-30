import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig

def convscale(x,xmin,xmax,ymin,ymax):
    return ((x-xmin)*(ymax-ymin) / (xmax-xmin)) + ymin;

[b,a] = sig.butter(4,(10/500),'low')

#determine the files to be loaded
fileprefix = './data/'
filesuffix = 'ntesting_005_3_Ite'
filenames = []
numSignals = 3
#filenames.append(['SmallDots_Ite0.txt','SmallDots_Ite1.txt'])
for k in range(numSignals):
    filenames.append(fileprefix + 'testing_005_3_Ite' + str(k) + '.txt')
# for k in range(numSignals):
#     filenames.append(fileprefix + 'BigDots_6spt_Ite' + str(k) + '.txt')

for k in range(len(filenames)):
    f = open(fileprefix + filesuffix + str(k) + '.txt','w')
    print('loading file: ', filenames[k])
    sigx = np.loadtxt(filenames[k])
    baseline = sigx[0:500,:]
    meanv = [np.mean(sigx[:,z]) for z in range(16)]
    signorm = [[] for z in range(16)]
    for z in range(len(sigx)):
        auxv = 0
        for i in range(16):
            x = convscale(sigx[z,i],meanv[i],meanv[i]*0.6,0,1)
            if x < 0:
                x = 0
            elif x > 1:
                x = 1
            signorm[auxv].append(x)
            f.write(str(signorm[auxv][-1]) + ' ')
            auxv += 1
        f.write('\n')
    f.close()

plt.figure()
for k in range(16):
    plt.plot(sigx[:,k])
plt.figure()
for k in range(16):
    plt.plot(signorm[k])
plt.figure()
for k in range(16):
    plt.plot(sig.filtfilt(b,a,signorm[k]))
plt.show()
