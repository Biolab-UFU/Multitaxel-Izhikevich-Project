import sys
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/texture_recognition')
import numpy as np
from copy import copy
import spiking_neurons as spkn
import matplotlib.pyplot as plt
import time
#can only be used for izhikevich
#with the exact same parameters
def runOptimalIzhikevich(numNeurons,current):
    #model parameters
    a = 0.02
    b = 0.2
    c = -65
    d = 8
    v = np.ones(numNeurons) * c
    u = v * b
    firings = []
    spikes = []
    #simulation
    for k in range(tf):
        #check whether there are spikes
        fired = np.where(v >= 30)[0]
        if(len(fired) > 0):
            firings.append(fired)
            spikes.append(k)
            #take the current input
        im = [current[i][k] for i in range(numNeurons)]
        v[fired] = c
        u[fired] += d
        v += 0.5*(0.04*np.power(v,2) + 5*v + 140 - u + im)
        v += 0.5*(0.04*np.power(v,2) + 5*v + 140 - u + im)
        u = u + a*(b*v-u)
        print(v[0])
        t=input()
    return v, firings, spikes

def run(current,neurons,tf):
    numNeurons = len(neurons)
    #model parameters
    A = np.array([x.A for x in neurons],dtype='float64')
    B = np.array([x.B for x in neurons],dtype='float64')
    C = np.array([x.C for x in neurons],dtype='float64')
    a = np.array([x.a for x in neurons],dtype='float64')
    b = np.array([x.b for x in neurons],dtype='float64')
    c = np.array([x.c for x in neurons],dtype='float64')
    d = np.array([x.d for x in neurons],dtype='float64')
    # print('A',A)
    # print('B',B)
    # print('C',C)'
    v = np.ones(numNeurons) * c
    u = v * b
    vm = []
    firings = []
    spikes = []
    #simulation
    for k in range(tf):
        #check whether there are spikes
        fired = np.where(v >= 30)[0]
        if(len(fired) > 0):
            firings.append(fired)
            spikes.append(k)
            spk = np.zeros(numNeurons)
            spk[fired] = 31
            vm.append(copy(spk))
            v[fired] = c[fired]
            u[fired] += d[fired]

        vm.append(copy(v))
        #take the current input
        im = [current[i][k] for i in range(numNeurons)]
        v += 0.5*(A*np.power(v,2) + B*v + C - u + im)
        v += 0.5*(A*np.power(v,2) + B*v + C - u + im)
        u += a*(b*v-u)
        # print(v[0])
        # t=input()
    print(len(vm))
    return v, firings, spikes, vm

nn = 200
ii = 20000
I = np.ones(ii)*30
I[0:500] = 0
Im = [copy(I) for k in range(nn)]
n = [spkn.model.izhikevich() for k in range(nn)]
# resp = runOptimalIzhikevich(10,Im)

print('global simulation')
t0 = time.time()
resp = run(Im,n,ii)
t1 = time.time()
print('done: ', str(t1-t0), ' seconds')

print('global simulation')
simul = spkn.simulation(1,0,ii,Im,n)
t0 = time.time()
resp = simul.optIzhikevich()
t1 = time.time()
print('done: ', str(t1-t0), ' seconds')
print(simul.spikes[0])

a = input()

print('traditional simulation')
simul = spkn.simulation(1,0,ii,Im,n)
t0 = time.time()
simul.run()
t1 = time.time()
print('done: ', str(t1-t0), ' seconds')

# print(resp[1])
# print(resp[2])
r = [resp[3][k][0] for k in range(len(resp[3]))]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
plt.figure()
plt.plot(r)
plt.show()
#-------------------------------------------------------------------------------
