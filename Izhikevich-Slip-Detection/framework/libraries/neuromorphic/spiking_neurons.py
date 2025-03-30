# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Neuromorphic Engineering and Robotics Group - NER
#-------------------------------------------------------------------------------
# Description: Library for handling spiking neurons
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
# LIBRARIES
#-------------------------------------------------------------------------------
import numpy as np #numpy
import matplotlib.pyplot as plt #plotting
import scipy.io as sio #input-output for handling files
import scipy.signal as sig #signal processing
import scipy.stats as stat #statistics
from collections import Counter #counting occurrences
#machine learning
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
#spike-distance metrics
#pyspike library
import pyspike as spk
#neo library
import quantities as pq
import neo
#elephant library
import elephant.statistics as el
import elephant.spike_train_dissimilarity as spktd
#multiprocessing
from multiprocessing import Pool
from copy import copy
#-------------------------------------------------------------------------------
# DEFINES THE SINGLE NEURON MODELS
#-------------------------------------------------------------------------------
class model():
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    #defines an izhikevich neuron model
    #izhikevich
    #v' = 0.04v^2 + 5v + 140 - u + I
    #u' = a(bv - u)
    #if v >= 30mV, v=c,u=u0+d where u0 is the initial condition of u
    #v represents the membrane potential
    #u represents a membrane recovery variable
    #the parameter a describes the time scale of the recovery variable u.
    #Smaller values result in slow recovery. A typical value is a=0.02
    #the parameter b describes the sensitivity of the recovery variable u to
    #the subthreshold fluctuations of the membrane potential v. A typical value
    #is b=0.2
    #the parameter c describes the after-spike reset value of the membrane
    #potential v caused by the fast high-threshold K+ conductances. A typical
    #value is c=-65mV.
    #the parameter d describes after-spike reset of the recovery variable u
    #caused by slow high-threshold Na+ and K+ conductances. A typical value is
    #d=2.
#-------------------------------------------------------------------------------
    class izhikevich():
        def __init__(self,A=0.04,B=5,C=140,Cm=1,a=0.02,b=0.2,c=-65,d=2,name='default'):
            #parameters that define the neuron model
            self.A = A
            self.B = B
            self.C = C
            self.Cm = Cm
            self.a = a
            self.b = b
            self.c = c
            self.d = d
            self.type = 'izhikevich' #identify the neuron model
            self.name = name #name to help into identifying the neuron itself
            self.uv = []

            #Initial conditions
            self.vm = c #resting potential
            self.u0 = 0.0#(self.b * self.vm) #global initial condition of recovery variable
            self.u = self.u0 #recovery variable

        #integrate the model over one step
        def integrate(self,input_current,dt):
            v_old = self.vm
            u_old = self.u
            #find the next value of the membrane voltage
            self.vm = v_old + dt*((self.A*v_old*v_old + self.B*v_old - u_old + self.C + (input_current/self.Cm)));
            #find the next value of the recovery variable
            self.u = u_old + dt*self.a*((self.b * v_old) - u_old);
            #spike event
            #if a spike is generated
            self.uv.append(self.u)
            if self.vm > 30:
                self.vm = self.c #reset membrane voltage
                self.u = self.u + self.d #reset recovery variable
                self.uv.append(self.u)
                # print(self.u, self.d)
                return [True,self.vm,31] #returns true
            else: #no spikes
                return [False,self.vm] #returns false
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# defines a neuron following the idea of event-based systems
# is this really neuromorphic style? I begin to think that it is not
#-------------------------------------------------------------------------------
    class eventbased():
        def __init__(self,th=0.0005,name='default',maxSamples=50):
            self.type = 'eventbased'
            self.spiketh = th
            self.name = name
            self.prevsamp = 0
            self.sumv = 0
            self.sampleCounter = 0 #keeps track of the integration process
            self.maxSamples = maxSamples

        #integrate the model over one time step
        def integrate(self,input_sample,dt):
            self.sumv += (input_sample - self.prevsamp)
            arg0 = False
            arg1 = 0

            #check if a spike should be triggered
            if self.sumv > self.spiketh:
                arg0 = True
                arg1 = 1
                self.sumv = 0
            elif self.sumv < -self.spiketh:
                arg0 = True
                arg1 = 1
                self.sumv = 0

            #updates the previous sample
            self.prevsamp = input_sample

            #check if the sum should be reset
            self.sampleCounter += 1
            if self.sampleCounter >= self.maxSamples:
                self.sumv = 0

            #return output
            return [arg0,arg1]

        # #integrate the model over one step
        # def integrate(self,input_sample,dt):
        #     # print(input_sample,self.prevsamp,input_sample-self.prevsamp)
        #     if input_sample - self.prevsamp > self.spiketh:
        #         self.prevsamp = input_sample
        #         return [True,1]
        #     elif input_sample - self.prevsamp < -self.spiketh:
        #         self.prevsamp = input_sample
        #         return [True,1]
        #     else:
        #         self.prevsamp = input_sample
        #         return [False,0]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# DEFINES THE SIMULATION CONTROL OBJECT
#-------------------------------------------------------------------------------
class simulation():
    def __init__(self,dt=1,t0=0,tf=1000,I=[np.ones(1000)],neurons=None):
        self.dt = dt #time-step of the simulation (ms)
        self.t0 = t0 #initial time (ms)
        self.tf = tf #final time (ms)
        #input current
        #should be a matrix of NxM
        #where
        # N: number of neurons -> points which neuron should receive the current
        # M: number of samples given dt, t0 and tf
        self.I = I
        #time vector generated from t0, tf, and dt
        self.timev = np.arange(self.t0,self.tf,self.dt)
        #vector containing the neurons to be simulated
        self.neurons = neurons
        #matrix containing time vectors for each neuron
        self.timen = [[] for i in range(len(neurons))]
        #matrix containing the spike times for each neuron
        self.spikes = [[] for i in range(len(neurons))]
        #matrix containing the membrane voltage over time for each neuron
        self.vneurons = [[] for i in range(len(neurons))]

    #allocate individual neurons separately for simulation
    def runParallel(self):
        pool = Pool()
        # pool.map(self.single,[i for i in range(len(self.neurons))])
        # print(self.spikes[0])
        r = pool.map(self.single,[i for i in range(len(self.neurons))])
        for i in range(len(self.neurons)):
            self.spikes[i] = r[i][0]
            self.timen[i] = r[i][1]
            self.vneurons[i] = r[i][2]

        # return [self.single(i) for i in range(len(self.neurons))]

    #simulate a single neuron over all the inputs --> useful for parallel loops
    def single(self,id):
        spikes = []
        timen = []
        vneurons = []
        for k in range(len(self.timev)):
            ret = self.neurons[id].integrate(self.I[id][k],self.dt)
            #if the neuron is izhikevich type
            if self.neurons[id].type == 'izhikevich':
                #if the neuron spikes, it returns True
                if ret[0] is True:
                    #append the current time
                    timen.append(self.timev[k])
                    #append the spike time
                    spikes.append(self.timev[k])
                    self.spikes[id].append(self.timev[k])
                    #append the maximum membrane voltage (30 mV)
                    vneurons.append(ret[2])
            #if the neuron is event-based type
            elif self.neurons[id].type == 'eventbased':
                if ret[0] is True:
                    #append the spike time
                    spikes.append(self.timev[k])

            #add the current time to vector
            timen.append(self.timev[k])
            #add the current membrane voltage to vector
            vneurons.append(ret[1])

        # print(self.spikes[id])

        return spikes,timen,vneurons


    def optParallel(self):
        '''
        optimal integration of izhikevich model based on his matlab code.
        Warning: all the neurons should be of izhikevich type
        '''
        numNeurons = len(self.neurons)
        spikes = [[] for k in range(numNeurons)]
        vneurons = [[] for k in range(numNeurons)]
        timen = [[] for k in range(numNeurons)]
        #model parameters
        #create numpy arrays according to the parameters of each neuron
        A = np.array([x.A for x in self.neurons],dtype='float64')
        B = np.array([x.B for x in self.neurons],dtype='float64')
        C = np.array([x.C for x in self.neurons],dtype='float64')
        a = np.array([x.a for x in self.neurons],dtype='float64')
        b = np.array([x.b for x in self.neurons],dtype='float64')
        c = np.array([x.c for x in self.neurons],dtype='float64')
        d = np.array([x.d for x in self.neurons],dtype='float64')
        #array containing the membrane voltage of each neuron
        v = np.ones(numNeurons) * c
        #array containing the membrane recovery for each neuron
        u = v * b
        #run the simulation
        #optimal integration
        for k in range(self.tf):
            #check whether there are spikes
            fired = np.where(v >= 30)[0]
            #if a spike has been triggered, reset the model
            #and save the spikes
            if(len(fired) > 0):
                #reset the membrane potential
                v[fired] = c[fired]
                #reset membrane recovery
                u[fired] += d[fired]
                #save the time of spike for the neurons that fired
                [spikes[idx].append(self.timev[k]) for idx in fired]
                #save the value of spike for the neurons that fired
                [vneurons[idx].append(31) for idx in fired]
                #save the time where the spike occurred for proper plotting
                [timen[idx].append(self.timev[k]) for idx in fired]

            #save the membrane voltage
            [vneurons[i].append(v[i]) for i in range(len(self.vneurons))]
            #save the time step
            [x.append(self.timev[k]) for x in self.timen]

            #take the current input
            im = [self.I[i][k] for i in range(numNeurons)]
            #integrate two times with dt/2 for numerical stability
            v += (self.dt/2) * (A*np.power(v,2) + B*v + C - u + im) #membrane
            v += (self.dt/2) * (A*np.power(v,2) + B*v + C - u + im) #voltage
            u += self.dt * (a*(b*v-u)) #membrane recovery

        return spikes, vneurons, timen

    def optIzhikevich(self):
        '''
        optimal integration of izhikevich model based on his matlab code.
        Warning: all the neurons should be of izhikevich type
        '''
        numNeurons = len(self.neurons)
        #model parameters
        #create numpy arrays according to the parameters of each neuron
        A = np.array([x.A for x in self.neurons],dtype='float64')
        B = np.array([x.B for x in self.neurons],dtype='float64')
        C = np.array([x.C for x in self.neurons],dtype='float64')
        a = np.array([x.a for x in self.neurons],dtype='float64')
        b = np.array([x.b for x in self.neurons],dtype='float64')
        c = np.array([x.c for x in self.neurons],dtype='float64')
        d = np.array([x.d for x in self.neurons],dtype='float64')
        #array containing the membrane voltage of each neuron
        v = np.ones(numNeurons) * c
        #array containing the membrane recovery for each neuron
        u = v * b
        #run the simulation
        #optimal integration
        for k in range(self.tf):
            #check whether there are spikes
            fired = np.where(v >= 30)[0]
            #if a spike has been triggered, reset the model
            #and save the spikes
            if(len(fired) > 0):
                #reset the membrane potential
                v[fired] = c[fired]
                #reset membrane recovery
                u[fired] += d[fired]
                #save the time of spike for the neurons that fired
                [self.spikes[idx].append(self.timev[k]) for idx in fired]
                #save the value of spike for the neurons that fired
                [self.vneurons[idx].append(31) for idx in fired]
                #save the time where the spike occurred for proper plotting
                [self.timen[idx].append(self.timev[k]) for idx in fired]

            #save the membrane voltage
            [self.vneurons[i].append(v[i]) for i in range(len(self.vneurons))]
            #save the time step
            [x.append(self.timev[k]) for x in self.timen]

            #take the current input
            im = [self.I[i][k] for i in range(numNeurons)]
            #integrate two times with dt/2 for numerical stability
            v += (self.dt/2) * (A*np.power(v,2) + B*v + C - u + im) #membrane
            v += (self.dt/2) * (A*np.power(v,2) + B*v + C - u + im) #voltage
            u += self.dt * (a*(b*v-u)) #membrane recovery

    #run the simulation
    def run(self):
        #for every time step of the simulation
        for k in range(len(self.timev)):
            #for each neuron
            for i in range(len(self.neurons)):
                #run an interation for the neuron
                ret = self.neurons[i].integrate(self.I[i][k],self.dt)

                #if the neuron is izhikevich type
                if self.neurons[i].type == 'izhikevich':
                    #if the neuron spikes, it returns True
                    if ret[0] is True:
                        #append the current time
                        self.timen[i].append(self.timev[k])
                        #append the spike time
                        self.spikes[i].append(self.timev[k])
                        #append the maximum membrane voltage (30 mV)
                        self.vneurons[i].append(ret[2])
                #if the neuron is event-based type
                elif self.neurons[i].type == 'eventbased':
                    if ret[0] is True:
                        #append the spike time
                        self.spikes[i].append(self.timev[k])

                #add the current time to vector
                self.timen[i].append(self.timev[k])
                #add the current membrane voltage to vector
                self.vneurons[i].append(ret[1])

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# DEFINES METHODS FOR ANALYZING SPIKE TRAINS
#-------------------------------------------------------------------------------
class analysis():
    #method to compute average spiking rates
    def get_asr_over_time(spikes,windowsize,overlap):
        '''
        computes average spiking rate over windows of time. the timing of spikes
        should be in ms; windowsize should be given in ms and overlap in
        percentage.
        '''
        twindow0 = 0
        twindow1 = windowsize
        asr = []
        #go through the spike vector until the window crosses its
        #limits
        while True:
            #find the spikes contained inside the window
            idx = np.where(np.logical_and(np.greater_equal(spikes,twindow0),np.less(spikes,twindow1)))
            #measure the average spiking rate -> number of spikes in the time interval
            idx = idx[0]
            avgspk = np.floor(len(idx) / (windowsize/1000.0))
            asr.append(avgspk)

            #increment the windows
            twindow0 += int(windowsize*(1-overlap))
            twindow1 += int(windowsize*(1-overlap))

            #all intervals have been scanned
            if twindow0 > spikes[-1] or twindow1 > spikes[-1]:
                break #break the while loop

        return asr

    #measures the inter-spike interval for all consecutive spikes in a
    #spike train
    def get_isi(spike_train):
        isi = [] #aux vector
        for k in range(len(spike_train)-1):
            isi.append(spike_train[k+1] - spike_train[k])
        return isi
    def get_sr(spike_train):
        return sr

    def isi_histogram(simulObj,numSignals,type='gaussian'):
        class isi():
            def __init__(self,xvals,yvals,fit,pdf=None,type=None):
                self.xvals = xvals
                self.yvals = yvals
                self.fit = fit
                self.pdf = pdf
                self.type = type

        #get the number of repeated inputs
        numInputs = int(len(simulObj.neurons) / numSignals)
        #get the number of neurons
        numNeurons = len(simulObj.neurons)
        #result for ISIs
        resultISI = [[] for k in range(numInputs)]
        #result for the histogram
        resultHist = [[] for k in range(numInputs)]
        #store the spike times
        xvalues = [[] for k in range(numInputs)]
        #store the number of occurrences
        yvalues = [[] for k in range(numInputs)]
        #curve fitting parameters
        fit = [[] for k in range(numInputs)]
        #curve fitting parameters
        pdf = [[] for k in range(numInputs)]

        aux = 0
        #compute the ISIs for all the neurons
        #combine ISIs from repeated inputs
        for k in range(numInputs):
            for v in range(numSignals):
                for w in range(len(simulObj.spikes[aux])-1):
                    resultISI[k].append(simulObj.spikes[aux][w+1]-simulObj.spikes[aux][w])
                aux += 1

        if type == 'basic':
            #return basic histogram first
            for k in range(numInputs):
                #count the occurrences of values
                resultHist[k] = Counter(resultISI[k])
                xvalues[k] = list(resultHist[k].keys())
                xvalues[k].sort()
                yvalues[k] = [resultHist[k][v] for v in xvalues[k]]
                #curve fitting
                if len(xvalues[k]) > 0 and len(yvalues[k]) > 0:
                    fit[k] = np.polyfit(xvalues[k],yvalues[k],10)
                else:
                    fit[k] = False
                # fit[k] = 0
                pdf = None
        elif type == 'gaussian':
            for k in range(numInputs):
                #count the occurrences of values
                resultHist[k] = Counter(resultISI[k])
                xvalues[k] = list(resultHist[k].keys())
                xvalues[k].sort()
                mux,sigmax = stat.norm.fit(resultISI[k])
                yvalues[k] = stat.norm.pdf(xvalues[k],mux,sigmax)
                # n,bins,patches = plt.hist(resultISI[k],bins='auto',normed=1)
                # y = mlab.normpdf(bins,mux,sigmax)
                # plt.plot(bins,y,color=np.random.rand(3,1))
                # xvalues[k] = bins
                # yvalues[k] = y
                # fit[k] = False
                plt.close()
                pdf[k] = stat.norm.fit(resultISI[k])

        # elif type == 'nonparametric':
        #     for k in range(numInputs):

        return isi(xvalues,yvalues,fit,pdf,type)

    def raster(simulObj):
        class rasters():
            def __init__(self,xvals,yvals,yvalslbl,ylabels,spike,numNeurons):
                self.numNeurons = numNeurons
                self.xvals = xvals
                self.yvals = yvals
                self.yvalslbl = yvalslbl
                self.ylabels = ylabels
                self.spike = spike

        #get the number of neurons
        numNeurons = len(simulObj.neurons)
        #get the names of the neurons
        neuronNames = [v.name for v in simulObj.neurons]
        #get the maximum firing time
        #variable for handling absence of spikes
        maxTimes = [np.max(x) for x in simulObj.spikes if len(x) > 0]
        if len(maxTimes) > 0:
            maxSpikeTime = np.max(maxTimes)
        #y-axis values
        yvalues = []
        #x-axis values
        xvalues = []
        #determines whether neuron fired or not
        spike = []

        if len(maxTimes) > 0:
            for k in range(numNeurons):
                spk = simulObj.spikes[k]
                if len(spk) > 0:
                    spike.append(True) #neuron spiked
                    # yvalues.append(np.ones(len(spk))*(4.25-((k+1)*0.025)))
                    yvalues.append(np.ones(len(spk))*(k+1))
                else:
                    spike.append(False)
                    spk = [0,maxSpikeTime] #neuron didn't spike
                    yvalues.append(np.ones(len(spk))*(k+1))
                    # yvalues.append(np.ones(len(spk))*(4.25-((k+1)*0.025)))
                xvalues.append(spk)

            yv = [np.max(x) for x in yvalues] #the values in y-axis

            return rasters(xvalues,yvalues,yv,neuronNames,spike,numNeurons)
        else:
            return False
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# DEFINES METHODS FOR MEASURING THE DISTANCE BETWEEN SPIKE TRAINS
#-------------------------------------------------------------------------------
class distance():
    def victor_purpura(simulObj,q):
        vpd_spikes = [neo.SpikeTrain(x,units='milliseconds',t_start=simulObj.t0,t_stop=simulObj.tf) for x in simulObj.spikes]
        vpd_distance = spktd.victor_purpura_dist(vpd_spikes,sort=False,q=q*pq.Hz)
        return vpd_distance
    def van_rossum(simulObj,tau):
        vrm_spikes = [neo.SpikeTrain(x,units='milliseconds',t_start=simulObj.t0,t_stop=simulObj.tf) for x in simulObj.spikes]
        vrm_distance = spktd.van_rossum_dist(vrm_spikes,tau=tau*pq.second,sort=False)
        return vrm_distance
    def isi(simulObj):
        isid_spikes = [spk.SpikeTrain(x,[simulObj.t0,simulObj.tf]) for x in simulObj.spikes]
        isidist = spk.isi_distance_matrix(isid_spikes)
        return isidist
    def spikerate(simulObj):
        return 0
#-------------------------------------------------------------------------------
class information():
    class spdf():
        def __init__(self,xvals,yvals):
            self.xvals = xvals
            self.yvals = yvals
#-------------------------------------------------------------------------------
    def fit_kde_isi(spikes,numSignals=20,op='class',xgrid=np.linspace(0,1000,1000)):
        '''
        using kde to fit a gaussian distribution to the isis. kde can be used
        to fit over the isis of individual taxels (op = 'class') or over all the
        neurons (op = 'neurons').
        '''
        #if option is class, then 'spikes' contains the timing of spikes from
        #an individual neuron
        if op == 'class':
            #retrieve the vector containing all the isis
            isiv = information.get_global_isi(spikes,numSignals)
            numClasses = len(isiv) #find the number of classes
            #fit kde
            #create the object
            kdeobj = [stat.gaussian_kde(isiv[w]) for w in range(numClasses)]
            #fit to the desired interval
            kdefit = [x.evaluate(xgrid) for x in kdeobj]
            #return the result
            return kdefit
        #if option is 'neurons', then 'spikes' is a vector containing the timing
        #of spikes from all the neurons that should be grouped together
        #(one class)
        elif op == 'neurons':
            numNeurons = len(spikes) #find the number of neurons
            kdefit = [[] for k in range(numNeurons)]
            for k in range(numNeurons):
                kdefit[k] = information.fit_kde_isi(spikes[k],len(spikes[k]),op='class',xgrid=xgrid)[0]
            return kdefit
#-------------------------------------------------------------------------------
    def kldivergence(pk,qk):
        pk = np.array(pk)
        qk = np.array(qk)
        idxpk = np.where(np.logical_or(np.equal(pk,0),np.less_equal(pk,1e-300)))
        idxqk = np.where(np.logical_or(np.equal(qk,0),np.less_equal(qk,1e-300)))
        pk[idxpk] = 1e-100
        qk[idxqk] = 1e-100
        return stats.entropy(pk,qk,base=2)
#-------------------------------------------------------------------------------

    def get_global_isi(spikeVector,numSignals):
        numInputs = int(len(spikeVector) / numSignals)
        isiv = [[] for k in range(numInputs)]

        auxv = 0
        for k in range(numInputs):
            for w in range(numSignals):
                isi = analysis.get_isi(spikeVector[k*numSignals + w])
                isiv[auxv].extend(copy(isi))
                # print(isiv[auxv])
                # l=input()
            # print(isiv[auxv]) #debugging
            auxv += 1

        return isiv

    #estimate probability density function from spike trains
    #bin the signal into same intervals
    #count the number of spikes across same input
    def estimate_spike_pdf(simulObj,numSignals=1,binsize=2):
        #estimate the number of different (not repeated) number of inputs
        numInputs = int(len(simulObj.neurons) / numSignals)
        #estimate the number of bins given the size of the signal
        numbins = int(len(simulObj.timev)/binsize)
        idx = 0 #aux variable for indexing repetition of signals
        #generate the x-axis values which is the bin time
        xvalues = np.arange(0,len(simulObj.timev),binsize)
        #store the number of spikes in each bin
        yvalues = [[] for k in range(numInputs)]

        #loop through all the inputs
        for k in range(numInputs):
            nspikes = []
            t0 = 0
            t1 = binsize
            for w in range(numbins):
                spkv = [np.where(np.logical_and(np.greater_equal(x,t0),np.less_equal(x,t1)))[0] for x in simulObj.spikes[idx:idx+numSignals]]
                nspk = np.sum([len(x) for x in spkv])
                nspikes.append(nspk)
                # print(t0,t1,idx,spkv) #debugging
                # print(nspk) #debugging
                t0 += binsize
                t1 += binsize
            idx += numSignals
            yvalues[k] = nspikes
        return information.spdf(xvalues,yvalues)

    def estimate_asr_pdf(simulObj,binsize=2):
        #estimate the number of different (not repeated) number of inputs
        numInputs = len(simulObj.neurons)
        #estimate the number of bins given the size of the signal
        numbins = int(len(simulObj.timev)/binsize)
        #generate the x-axis values which is the bin time
        xvalues = np.arange(0,len(simulObj.timev),binsize)
        #store the number of spikes in each bin
        yvalues = [[] for k in range(numInputs)]
        #loop through all the inputs
        for k in range(numInputs):
            nspikes = []
            t0 = 0
            t1 = binsize
            for w in range(numbins):
                spkv = np.where(np.logical_and(np.greater_equal(simulObj.spikes[k],t0),np.less_equal(simulObj.spikes[k],t1)))
                nspk = len(spkv[0])
                nspikes.append(nspk)
                # nspikes.append(nspk/((binsize*simulObj.dt)/1000))
                # print(t0,t1,idx,spkv) #debugging
                # print(nspk) #debugging
                t0 += binsize
                t1 += binsize
            yvalues[k] = nspikes
        return information.spdf(xvalues,yvalues)

    def isi_histogram(simulObj,numSignals):
        return 0

    def entropy(spdfObj,binsize):
        #estimate the number of different (not repeated) number of inputs
        numInputs = len(spdfObj.yvals)
        entropy = [[] for k in range(numInputs)]
        #loop over the neurons to find the probabilities
        for k in range(numInputs):
            probs = np.histogram(spdfObj.yvals[k], bins=binsize)[0]
            probs = probs / np.sum(probs)
            sumv = 0
            for w in range(len(probs)):
                if probs[w] != 0:
                    sumv += probs[w] * np.log2(probs[w])
            entropy[k] = sumv * -1
        return entropy

    def mutual_information(spdfObj,binsize):
        #estimate the number of different (not repeated) number of inputs
        numInputs = len(spdfObj.yvals)
        #vector for storing the probability distribution for each input
        probs = [[] for k in range(numInputs)]
        #matrix for storing the mutual information value between all the
        #inputs
        MI = np.zeros((numInputs,numInputs))
        #loop over the neurons to find the probabilities
        for k in range(numInputs):
            probs[k] = np.histogram(spdfObj.yvals[k], bins=binsize)[0]
            probs[k] = probs[k] / np.sum(probs[k])
        #measure mutual information
        for k in range(numInputs):
            for w in range(numInputs):
                # print(probs[k]) #debugging
                # print(probs[w]) #debugging
                #joint probs
                pxy = np.histogram2d(spdfObj.yvals[k],spdfObj.yvals[w],bins=binsize)[0]
                pxy = pxy / len(spdfObj.yvals[k])
                # print(pxy) #debugging
                #product between probs
                pxpy = np.outer(probs[k],probs[w])
                # print(pxpy) #debugging
                #log part
                logp = np.log2(pxy/pxpy)
                # print(logp)
                MI[k,w] = np.nansum(pxy * logp)

        return MI

    def covariance_matrix():

        return 0
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# DEFINES METHODS FOR CLASSIFICATION OF DIFFERENT PATTERNS IN SPIKE TRAINS
#-------------------------------------------------------------------------------
class classification():
    #class containing the features and targets to be used for classification
    class spike_train_features():
        def __init__(self,features,featurenames,targets):
            self.features = features
            self.featurenames = featurenames
            self.targets = targets

    #based on the features proposed by Rongala et al., 2015
    #extracts two features from the spike trains
    #adding some exception control here....
    def feature_extraction(simulObj,numSignals):
        numNeurons = len(simulObj.neurons)
        features = np.zeros((numNeurons,2))
        isicv = []
        isifr = []

        X = np.zeros((numNeurons,2))
        Y = np.zeros(numNeurons)
        aux = 0

        #loop over all the neurons
        for k in range(numNeurons):
            auxisicv = analysis.get_isi(simulObj.spikes[k])
            if auxisicv == 0 or auxisicv == []:
                print('error in iteration ' + str(k) + ' found')
                # l = input()
                X[k,1] = 0
            else:
                #ddof should be specified!
                X[k,1] = np.std(auxisicv,ddof=1) / np.mean(auxisicv)

            X[k,0] = len(simulObj.spikes[k]) / (simulObj.tf/1000)
            if np.isnan(X[k,1]) or np.isnan(X[k,0]):
                print(X[k,0],X[k,1])
                X[k,1] = 0
                X[k,0] = 0
                print('NaN found!')
                print(X[k,0],X[k,1])
                # l = input()

            Y[k] = aux
            if (k+1)%numSignals == 0:
                aux += 1

        #returns the calculated features from the spike train
        return classification.spike_train_features(X,['isifr','isicv',],Y)

    #leave one out cross validation
    #features should be arranged as a mxn matrix
    #where m is the number of examples and n is the number of features
    #classifierObj is an object from sklearn that represents a given classifier
    def LOOCV(classifierObj,features,targets,target_names=None):

        loo = LeaveOneOut() #create the object to handle leave one out cross validation
        #auxiliary variables
        y_true = []
        y_pred = []
        #for each test performed with leave one out
        for train_index,test_index in loo.split(features):
            x_train = features[train_index,:] #get the input training samples
            y_train = targets[train_index] #get the output training samples
            x_test = features[test_index,:] #get the input testing samples
            y_test = targets[test_index] #get the output testing samples

            #create the classifier
            #training --> fit the knn classifier
            classifierObj.fit(x_train,y_train)
            #get the target class
            y_true.append(y_test[0])
            #get the output of the classifier
            y_pred.append(classifierObj.predict(x_test)[0])

        #get the confusion matrix
        confm = confusion_matrix(y_true,y_pred)

        #get the classification report
        if target_names is not None:
            report = classification_report(y_true,y_pred,target_names=target_names)
        else:
            report = classification_report(y_true,y_pred)

        #returns the confusion matrix and the classification report
        return confm, report
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    from sklearn import neighbors #required for KNN

    #create the neurons
    n = [model.izhikevich() for k in range(6)]

    #create the input currents
    I1 = np.ones(1000) * 8
    I2 = np.ones(1000) * 10
    I3 = np.ones(1000) * 11
    I4 = np.ones(1000) * 20
    I5 = np.ones(1000) * 16
    I6 = np.ones(1000) * 19

    #prepare the simulation
    s = simulation(I=[I1,I2,I3,I4,I5,I6],neurons=n)
    #run the simulation
    s.run()

    spkk = information.estimate_asr_pdf(s,50)

    # f = open('spikestimes.txt','w')
    # for k in range(len(s.neurons)):
    #     for w in range(len(spkk.yvals[k])):
    #         f.write(str(spkk.yvals[k][w]) + ' ')
    #     f.write('\n')
    # f.close()

    mi = information.mutual_information(spkk,5)
    en = information.entropy(spkk,5)
    print(en)
    print(mi)
    print(mi[0,:])
    # print(s.spikes[0])
    # print(spkk.yvals[0])
    # print('---------------')
    # px = np.histogram(spkk.yvals[0],bins=5)[0]
    # py = np.histogram(spkk.yvals[0],bins=5)[0]
    # pxy = np.histogram2d(spkk.yvals[0],spkk.yvals[0],bins=5)[0]
    # px = px / np.sum(px)
    # py = py / np.sum(py)
    # pxy = pxy / len(spkk.yvals[0])
    # print('px')
    # print(px)
    # print('py')
    # print(py)
    # print('pxy')
    # print(pxy)
    # pxpy = np.outer(px,py)
    # print('pxpy')
    # print(pxpy)
    # pp = pxy/pxpy
    # logp = np.log2(pxy/pxpy)
    # print('logp')
    # print(logp)
    # p = pxy * logp
    # print('pxy * logp')
    # print(p)
    # mi = np.nansum(p)
    # print('mi')
    # print(mi)
    # print('---------------')
    # # print(np.outer(px[0],py[0]))
    # # print(np.outer(np.transpose(px[0]),py[0]))
    # pxpy = np.outer(np.transpose(px[0]),py[0])
    # pxy[0][np.where(pxy[0] == 0)] = 1
    # pxpy[np.where(pxpy == 0)] = 1
    # print('---------------')
    # # print((np.log2(pxy[0]) - np.log2(pxpy)))
    # print(pxy[0] * (np.log2(pxy[0]) - np.log2(pxpy)))
    # print(np.sum(pxy[0] * (np.log2(pxy[0]) - np.log2(pxpy))))
    # print('---------------')
    # print('mutual information', np.sum())
    # plt.subplot(2,1,1)
    # plt.hist(spkk.yvals[0],bins=2,normed=True,range=[np.min(spkk.yvals[0]),np.max(spkk.yvals[0])])
    # plt.subplot(2,1,2)
    # plt.hist(spkk.yvals[5],bins=2,normed=True,range=[np.min(spkk.yvals[5]),np.max(spkk.yvals[5])])
    # plt.figure()
    # plt.hist2d(spkk.yvals[0],spkk.yvals[5],bins=5)
    # plt.show()
    # print(spkk.yvals)
    # z = np.vstack([spkk.yvals[0],spkk.yvals[1],spkk.yvals[2],spkk.yvals[3],spkk.yvals[4],spkk.yvals[5]])
    # print(np.cov(z))

    # spkk = information.estimate_spike_pdf(s,3,2)
    # print(len(spkk.yvals[0]))
    # print(len(spkk.yvals[1]))
    # print(np.histogram(spkk.yvals[0],10))
    # # r = np.histogram2d(y0,y1,bins=(10,10))
    # print(y1)

    #information theoryidx = 0 #aux variable for indexing repetition of signals
    # resp = information.estimate_spike_pdf(s,3,20)

    # r = information.mutual_information(s,10)
    # i0 = analysis.get_isi(s.spikes[0])
    # i1 = analysis.get_isi(s.spikes[1])
    #
    # diffl = len(i0) - len(i1)
    # if diffl > 0:
    #     [i1.append(0) for k in range(diffl)]
    # elif diffl < 0:
    #     [i0.append(0) for k in range(diffl)]
    #
    # print(len(i0),len(i1))
    #
    # pxy = np.histogram2d(i0,i1,bins=(10,10))
    # print(pxy)

    plt.figure()
    plt.subplot(2,1,1)
    plt.plot(s.timen[1],s.vneurons[1])
    plt.subplot(2,1,2)
    plt.plot(s.timen[4],s.vneurons[4])
    # plt.show()

    #
    # #extract the features for classification
    # spkfeat = classification.feature_extraction(s,3)
    # #create the classifier
    # clf = neighbors.KNeighborsClassifier(1,weights='distance')
    # #leave one out cross validation
    # conf = classification.LOOCV(clf,spkfeat.features,spkfeat.targets)
    #
    # #print the features
    # print('features')
    # print(spkfeat.features)
    # #print the confusion matrix
    # print('confusion matrix')
    # print(conf)
    #
    # #plot the feature space
    # colors = ['r','g']
    # plt.figure()
    # for k in range(6):
    #     idx = int(spkfeat.targets[k])
    #     plt.scatter(spkfeat.features[k,0],spkfeat.features[k,1],c=colors[idx])
    # plt.show()
