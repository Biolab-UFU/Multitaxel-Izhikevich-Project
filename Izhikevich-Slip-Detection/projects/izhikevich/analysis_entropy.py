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
sys.path.append('../../framework/libraries/general')
sys.path.append('../../framework/libraries/neuromorphic')
#-------------------------------------------------------------------------------
import numpy as np
import scipy.stats as stat
import matplotlib.pyplot as plt
import spiking_neurons as spkn
#-------------------------------------------------------------------------------
# verify entropy
#-------------------------------------------------------------------------------
#entropy of a constant vector
# z = stat.norm(20,40)
# x = np.linspace(-100,100,1000)
# z = np.random.normal(20,10,size=10000)
# # z = np.ones(1000)
# # z[0:500] = 200
# # z[500:600] = 10
# binsize = 500
# probs,bin_edges = np.histogram(z, bins=binsize)
# probs = probs / np.sum(probs)
# print(stat.entropy(probs))
# # print(probs)
# # print(bin_edges)
# print(len(bin_edges),len(probs))
# bin_edges = bin_edges[0:len(bin_edges)-1]
# plt.figure(); plt.plot(bin_edges,probs); plt.show()
# # print(len(x))
# # print(stat.entropy(z.pdf(x)))
# # plt.figure()
# # plt.plot(x,z.pdf(x))
# # plt.show()
z = np.random.normal(0,50,size=10000)
xgrid = np.linspace(-200,200,5000)
kernel = stat.gaussian_kde(z,bw_method=0.1)
resp = kernel.evaluate(xgrid)
#histogram based
probs,bin_edges = np.histogram(z,bins=5000)
probs = probs / np.sum(probs)
print(kernel(xgrid))
print('kde ' + str(stat.entropy(resp)))
print('histogram ' + str(stat.entropy(probs)))
#kde
plt.figure(); plt.plot(z,stat.norm.pdf(z,0,50))
plt.figure(); plt.title('kde'); plt.plot(xgrid,resp);
plt.figure(); plt.title('histogram'); plt.bar(bin_edges[0:len(bin_edges)-1],probs);
plt.show()
# print(kernel.d, kernel.n)
# # l = input()
#-------------------------------------------------------------------------------
'''
#generate a ramp input
dt = 1
t = np.arange(0,50,0.01)
Is = 20 * np.sin(2.0*np.pi*8*t)
Is += 20
Im = np.ones(5000) * 20
n = [spkn.model.izhikevich(d=8) for k in range(2)]
t0 = 0
tf = len(Im)
simul = spkn.simulation(dt=dt, t0=t0, tf=tf, I=[Im,Is], neurons=n)
simul.run()
isi = spkn.analysis.get_isi(simul.spikes[0])
r = spkn.analysis.raster(simul)
isi0 = stat.entropy(spkn.analysis.get_isi(simul.spikes[0]))
isi1 = stat.entropy(spkn.analysis.get_isi(simul.spikes[0]))
print(isi0)
print(isi1)
kl = stat.entropy(isi0,isi1)
print(kl)
# print(spkn.analysis.get_isi(simul.spikes[0]))
# print(spkn.analysis.get_isi(simul.spikes[1]))
plt.figure()
plt.scatter(r.xvals[0],r.yvals[0],color='k',marker='|')
plt.scatter(r.xvals[1],r.yvals[1],color='k',marker='|')
plt.show()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
'''
