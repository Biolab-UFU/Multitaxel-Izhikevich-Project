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
import os, sys, glob
sys.path.append('../neuromorphic') #neuromorphic libraries
sys.path.append('../general') #general libraries
import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt
from multiprocessing import Pool
from dataprocessing import *
from tactileboard import *
#classification
from sklearn import neighbors, datasets
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
#spiking models
import spiking_neurons as spkn
#pickle for data persistence - saving objects
import pickle
#-------------------------------------------------------------------------------(
class TRCONSTS():
    PREPROC_NOFILTER = 0
    PREPROC_HIGHPASS = 1
    PREPROC_LOWPASS = 2
    PREPROC_BANDPASS = 3
#-------------------------------------------------------------------------------
def analysis_kde_class(results_path,results=None,xgrid=np.linspace(0,1000,1000)):
    '''
    compute kde over the isi of individual neurons for each class
    '''
    if results is None:
        #load all the results
        results = [np.load(results_path + '/results_taxel' + str(k) + '.npz') for k in range(16)]

    #find the number of iterations
    numRep = int(len(results[0]['spikes']) / len(results[0]['texturev']))
    kdetaxels = [[] for k in range(16)] #vector for storing all the isis
    #analyze each taxel individually
    for k in range(16):
        print('fitting kde for taxel ' + str(k) + '...')
        #get the kde fit for each taxel
        kdetaxels[k] = spkn.information.fit_kde_isi(results[k]['spikes'],op='class',xgrid=xgrid)
    #save the results
    np.savez('results_kde.npz',kdetaxels=kdetaxels)
    #return the results
    return kdetaxels
#-------------------------------------------------------------------------------
def analysis_kde_taxel(results_path='./',results=None,spkvItv=[0,20],xgrid=np.linspace(0,1000,1000)):
    if results is None:
        #load all the results
        results = [np.load(results_path + '/results_taxel' + str(k) + '.npz') for k in range(16)]

    #get the spikes required for computing the kde
    spkv = [[results[k]['spikes'][w] for w in range(spkvItv[0],spkvItv[1])] for k in range(16)]
    #compute kde
    kdefit = spkn.information.fit_kde_isi(spkv,0,op='neurons',xgrid=xgrid)
    return kdefit

#-------------------------------------------------------------------------------
class TextureResults():
    '''
    defines a class that handles the files containing the results of the
    processing
    '''
    def __init__(self):
        self.fileHandler = None

    def loadFolder(self,folder):
        for k in range(TBCONSTS.NTAXELS):
            results = [np.load(folder + '/results_taxel' + str(k) + '.npz') for k in range(TBCONSTS.NTAXELS)]
            self.features = [results[k]['features'] for k in range(TBCONSTS.NTAXELS)]
            self.targets = [results[k]['targets'] for k in range(TBCONSTS.NTAXELS)]
            self.inputCurrent = [results[k]['inputCurrent'] for k in range(TBCONSTS.NTAXELS)]
            self.rawInputs = [results[k]['rawCurrent'] for k in range(TBCONSTS.NTAXELS)]
            self.spikes = [results[k]['spikes'] for k in range(TBCONSTS.NTAXELS)]
            self.isihist_xvals = [results[k]['isihist_xvals'] for k in range(TBCONSTS.NTAXELS)]
            self.isihist_yvals = [results[k]['isihist_yvals'] for k in range(TBCONSTS.NTAXELS)]
            self.confmatrix = [results[k]['confmatrix'] for k in range(TBCONSTS.NTAXELS)]

    def loadFile(self,filename):
        try:
            res = np.load(filename)
            self.features = res['features']
            self.targets = res['targets']
            self.inputCurrent = res['inputCurrent']
            self.rawInputs = res['rawCurrent']
            self.spikes = res['spikes']
            self.isihist_xvals = res['isihist_xvals']
            self.isihist_yvals = res['isihist_yvals']
            self.confmatrix = res['confmatrix']
            return True
        except:
            return False
#-------------------------------------------------------------------------------
class TextureRecognition():
    '''
    defines the class that analyzes tactile data based on a header file
    '''
    def __init__(self):
        self.fileHeader = None
#-------------------------------------------------------------------------------
    def createDatasetFiles(self):
        '''
        create a list with the tactile files that should be processed
        '''
        if self.fileHeaderOk: #parameters were loaded ok
            self.files = []
            for k in range(len(self.texturev)):
                if self.texturev[k] == '':
                    break
                for i in range(len(self.forcev)):
                    if self.forcev[i] == '':
                        break
                    for j in range(len(self.palpationv)):
                        if self.palpationv[j] == '':
                            break
                        for z in range(self.numIterations):
                            filename = ''
                            filename = self.dataFolder + '/texture_' + self.texturev[k] + '_' + self.forcev[i] + '_' + self.palpationv[j] + '_Ite' + str(z) + '.txt'
                            # print(filename)
                            self.files.append(filename)
            return True
            # print(self.files) #debugging
            # print(len(self.files)) #debugging
        else:
            return False #parameters are not loaded
#-------------------------------------------------------------------------------
    def loadExp(self,file):
        '''
        loads a single experimental tactile data file and converts the matrix
        format to a vector of vectors
        '''
        s = np.loadtxt(file)
        return [s[:,k] for k in range(np.size(s,1))]
#-------------------------------------------------------------------------------
    def postProcessing(self,folderpath):
        #load the results
        self.results = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(TBCONSTS.NTAXELS)]
#-------------------------------------------------------------------------------
    def runProcessing(self,parallel=True,fileResultsPath='./'):
        '''
        run the analysis according to the header file
        '''
        #load data
        print('loading files...')
        tt0 = time.time()
        if parallel is True:
            #parallel
            global load
            pool = Pool() #for multiprocessing, use all available cores
            data = pool.map(load,self.files) #load all the data files
            pool.close()
            pool.join()
        else:
            #normal, sequential, takes 3.4x more time to run
            # data = [np.loadtxt(f) for f in self.files]
            # data = [[data[k][:,i] for i in range(17)] for k in range(numFiles)]
            # #for debugging purposes
            for f in self.files:
                print('loading file: ' + f)
                data = np.loadtxt(f)
        ttf = time.time()
        print('total time:',ttf-tt0)


        #list containing the processed tactile signals
        numData = len(self.files)
        procData = [[] for k in range(len(self.files))]
        if len(self.files) > 1:
            eventData = [[] for k in range(len(self.files)-1)]
        else:
            eventData = [[] for k in range(len(self.files))]

        #pre-processing
        #create the filter
        if self.filterType == TRCONSTS.PREPROC_LOWPASS:
            wn = self.lowPassFc / (TBCONSTS.SAMPFREQ/2.0)
            self.filtb, self.filta = sig.butter(self.npoles,wn,'low')

        #normalize and filter the signal
        tb0 = int(0 * TBCONSTS.SAMPFREQ)
        tbf = int(1 * TBCONSTS.SAMPFREQ)

        #normalize all the signals individually
        #loop through the files
        # plt.figure() #debugging
        for k in range(len(self.files)):
            #save the event data
            #the last trial is bad, should be discarded
            if k == 0 or k < len(self.files) - 1:
                eventData[k] = data[k][-1]
            #loop through the taxels
            for i in range(TBCONSTS.NTAXELS):
                if self.normalize == 'True': #normalization
                    #take mean value at rest (baseline)
                    baselinev = np.mean(data[k][i][tb0:tbf])
                    #convert to scale and normalize
                    normv = convscale(data[k][i],baselinev,
                    self.baselinePercentage*baselinev,
                    self.normVmin,self.normVmax)
                    #apply filter
                    if self.filterType != TRCONSTS.PREPROC_NOFILTER:
                        procData[k].append(sig.filtfilt(self.filtb,self.filta,normv))
                    else: #no filter
                        procData[k].append(normv)
                else: #no normalization
                    #apply filter
                    if self.filterType != TRCONSTS.PREPROC_NOFILTER:
                        procData[k].append(sig.filtfilt(self.filtb,self.filta,data[k][i]))
                    else: #no filter
                        procData[k].append(data[k][i])
                # plt.plot(procData[k][-1]) #debugging
        # plt.show() #debugging

        #prepare the inputs
        #segmenting the signal accordingly
        #find the initial and final time
        #initial time should be the first event to go high
        #final time should be the last to go low
        #initial time
        tstartCut = np.min([np.min(np.where(x == 2)[0]) for x in eventData])
        tstartCut += int(self.tstart*TBCONSTS.SAMPFREQ)
        # tstartCut -= int(0.5*TBCONSTS.SAMPFREQ)
        # tstartCut += 3000
        print('tstart:', tstartCut)
        # tendCut = np.max([np.max(np.where(x == 2)[0]) for x in eventData])
        sizeTexture = 100 #mm
        lengthMoveUp = 150 #mm
        palpv = [float(x) for x in self.palpationv]
        maxPalpationTime = np.max(palpv)
        palp = sizeTexture / (lengthMoveUp / maxPalpationTime) #how long it takes to move 10 cm
        palp += 10
        tendCut = int(tstartCut + palp*TBCONSTS.SAMPFREQ + (self.tend*TBCONSTS.SAMPFREQ))
        # tendCut -= 1000
        # tendCut = tstartCut + 6500
        print('tend:', tendCut)

        #create the inputs - currents
        #each neuron will correspond to an individual taxel over all the inputs -> files
        i = [[procData[k][i] for k in range(numData)] for i in range(TBCONSTS.NTAXELS)]
        i = [[i[k][w][tstartCut:tendCut] for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        rawi = copy(i)
        #gain factor applied to normalized signal
        #find the maximum value over all the inputs
        maxv = [np.max([np.max(i[k][w]) for w in range(numData)]) for k in range(TBCONSTS.NTAXELS)]
        # i = [[(i[k][w]/maxv[k])*self.izGain for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        # i = [[((i[k][w]/np.max(i[k][w]))*self.izGain) for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        i = [[(i[k][w]*20)+10 for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        #add an offset
        # i = [[((i[k][w]/np.max(i[k][w]))*self.izGain)+10 for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        # i = [[i[k][w]*self.izGain for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
        # #permute the signals
        # for k in range(TBCONSTS.NTAXELS):
        #     for w in range(numData):
        #         permut = np.random.permutation(len(i[k][w]))
        #         i[k][w] = np.array(i[k][w])
        #         i[k][w] = i[k][w][permut]

        #create neurons
        #create a vector containing 16 neurons per input
        n = [[spkn.model.izhikevich(a=self.iza,b=self.izb,c=self.izc,d=self.izd)
         for k in range(numData)] for i in range(TBCONSTS.NTAXELS)]

        #vector containing the simulation objects
        self.simulObj = [[] for k in range(TBCONSTS.NTAXELS)]
        #analysis
        self.rasters = [[] for k in range(TBCONSTS.NTAXELS)] #rastergram
        self.isihist = [[] for k in range(TBCONSTS.NTAXELS)] #isi histogram
        #features for classification
        self.featObj = [[] for k in range(TBCONSTS.NTAXELS)]
        #find the number of signals per class
        signalsPerClass = int(numData / self.numClasses)
        #classifier
        self.classifierObj = neighbors.KNeighborsClassifier(self.numNeighbors,weights='distance')
        #classification results
        self.confMatrix = [[] for k in range(TBCONSTS.NTAXELS)]
        self.clfReport = [[] for k in range(TBCONSTS.NTAXELS)]

        #fix the time
        tstart = 0
        tend = tendCut - tstartCut
        dt = 1

        #get the name of the header file
        fileResultsPrefix = self.fileHeader.split('/')[-1].split('.txt')[0]
        #folder to save the results
        completePathFolderResults = fileResultsPath + fileResultsPrefix
        # print(completePathFolderResults)
        #create folder for storing the results if it has not been
        #created yet
        if not os.path.exists(completePathFolderResults):
            os.makedirs(completePathFolderResults)

        #file to save the report
        self.fileReport = open(completePathFolderResults + '/report.txt','w')

        #run the simulation
        #each taxel is simulated individually
        tt0 = time.time()
        for k in range(TBCONSTS.NTAXELS):
            #indicates which simulation is running
            print('Simulation: ' + str(k))
            #create the object
            self.simulObj[k] = spkn.simulation(dt,tstart,tend,i[k],n[k])
            #run the simulation
            self.simulObj[k].optIzhikevich()
            # self.simulObj[k].run()
            #analysis
            #rastergram
            self.rasters[k] = spkn.analysis.raster(self.simulObj[k])
            #isi gaussian fit
            self.isihist[k] = spkn.analysis.isi_histogram(self.simulObj[k], signalsPerClass, type='gaussian')
            #feature extraction
            self.featObj[k] = spkn.classification.feature_extraction(self.simulObj[k],signalsPerClass)
            #run the classification with leave-one-out cross validation
            ret = spkn.classification.LOOCV(self.classifierObj,self.featObj[k].features,self.featObj[k].targets, target_names=self.texturev)
            # if ret is not False:
            self.confMatrix[k] = ret[0]
            self.clfReport[k] = ret[1]
            self.fileReport.write('-----------------------------------------------------------------\n')
            self.fileReport.write('Report Taxel ' + str(k) + '\n')
            self.fileReport.write('-----------------------------------------------------------------\n')
            self.fileReport.write(ret[1])
            self.fileReport.write('-----------------------------------------------------------------\n')
            self.fileReport.write('\n')

            #saving the results
            np.savez(completePathFolderResults + '/results_taxel' + str(k),
            tstart=tstartCut,tend=tendCut,features=self.featObj[k].features,targets=self.featObj[k].targets,
            isihist_xvals=self.isihist[k].xvals,isihist_yvals=self.isihist[k].yvals,inputCurrent=self.simulObj[k].I,
            spikes=self.simulObj[k].spikes,confmatrix=self.confMatrix[k],clfreport=self.clfReport[k],
            target_names=self.texturev,rawCurrent=rawi[k],texturev=self.texturev,raster_xvals=self.rasters[k].xvals,
            raster_yvals=self.rasters[k].yvals,timev=self.simulObj[k].timev)

            # print(ret[1]) #debugging
        ttf = time.time()
        print('total time:',ttf-tt0)

        self.fileReport.close()

        #plot the inputs
        plt.figure(figsize=(19.2,10.8),dpi=100)
        for k in range(TBCONSTS.NTAXELS):
            plt.subplot(TBCONSTS.NROWS, TBCONSTS.NCOLS, k+1)
            auxv = 0
            for i in range(self.numClasses):
                plt.plot(self.simulObj[k].timev,self.simulObj[k].I[auxv])
                auxv += signalsPerClass
            plt.xlim([self.simulObj[k].timev[0],self.simulObj[k].timev[-1]])
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        plt.savefig(completePathFolderResults + '/inputs.png', bbox_inches='tight')

        #plot the isi gaussians
        plt.figure(figsize=(19.2,10.8),dpi=100)
        for k in range(TBCONSTS.NTAXELS):
            plt.subplot(TBCONSTS.NROWS, TBCONSTS.NCOLS, k+1)
            for i in range(self.numClasses):
                plt.plot(self.isihist[k].xvals[i],self.isihist[k].yvals[i])
            plt.xlim([0,400])
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        plt.savefig(completePathFolderResults + '/isihist.png', bbox_inches='tight')

        #plot the rastergram
        plt.figure(figsize=(19.2,10.8),dpi=100)
        for k in range(TBCONSTS.NTAXELS):
            plt.subplot(TBCONSTS.NROWS, TBCONSTS.NCOLS, k+1)
            if self.rasters[k] is not False:
                for w in range(numData):
                    plt.scatter(self.rasters[k].xvals[w],self.rasters[k].yvals[w],color='k',marker='|')
                plt.xlim([self.simulObj[k].timev[0],self.simulObj[k].timev[-1]])
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        plt.savefig(completePathFolderResults + '/raster.png', bbox_inches='tight')

        #plot the features
        plt.figure(figsize=(19.2,10.8),dpi=100)
        for k in range(TBCONSTS.NTAXELS):
            plt.subplot(TBCONSTS.NROWS, TBCONSTS.NCOLS, k+1)
            auxv = 0
            for w in range(self.numClasses):
                plt.scatter(self.featObj[k].features[auxv:auxv+signalsPerClass,0],self.featObj[k].features[auxv:auxv+signalsPerClass,1])
                auxv += signalsPerClass
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        plt.savefig(completePathFolderResults + '/features.png', bbox_inches='tight')

        #plot the confusion matrices
        plt.figure(figsize=(19.2,10.8),dpi=100)
        for k in range(len(self.featObj)):
            plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
            plt.matshow(self.confMatrix[k],fignum=False,vmin=0,vmax=signalsPerClass)
            plt.colorbar()
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        plt.savefig(completePathFolderResults + '/confmatrix.png', bbox_inches='tight')

        return True
#-------------------------------------------------------------------------------
    def loadHeader(self,_fileHeader):
        '''
        loads all the parameters required for analyzing the tactile data
        and performing texture recognition
        '''
        try:
            f = open(_fileHeader,'r') #open the file for reading
            self.fileHeader = _fileHeader
            lines = f.readlines() #read all the lines
            lines = [x.strip('\n') for x in lines] #remove line break
            #find the line related to pre-processing
            preProcLine = lines.index('Pre-processing')
            #find the line related to normalization
            normLine = lines.index('Normalization')
            #find the line related to segmentation of the signal
            cutLine = lines.index('Segmenting the tactile signal')
            #find the line related to the Izhikevich neuron model
            izhikevichLine = lines.index('Izhikevich model')
            #find the line related to the dataset
            datasetLine = lines.index('Dataset')
            #find the line related to classification
            classificationLine = lines.index('Classification')

            #1) pre-processing
            #get filter type
            self.filterType = float(lines[preProcLine+1].split(': ')[1])
            #get number of poles
            self.npoles = float(lines[preProcLine+2].split(': ')[1])
            #get the high-pass cut-off frequency
            self.highPassFc = float(lines[preProcLine+3].split(': ')[1].split(' ')[0])
            #get the low-pass cut-off frequency
            self.lowPassFc = float(lines[preProcLine+3].split(': ')[1].split(' ')[1])
            # print(self.filterType,self.npoles,self.highPassFc,self.lowPassFc) #debugging

            #2) normalization
            #determines whether signal should be normalized
            self.normalize = lines[normLine+1].split(': ')[1]
            #get the percentage of baseline for normalization
            self.baselinePercentage = float(lines[normLine+2].split(': ')[1])/100.0
            #get the minimum value for the normalized scale
            self.normVmin = float(lines[normLine+3].split(': ')[1])
            #get the maximum value for the normalized scale
            self.normVmax = float(lines[normLine+4].split(': ')[1])
            # print(self.normalize,self.baselinePercentage,self.normVmin,self.normVmax) #debugging

            #3) segmentation
            #determines how the segmentation should work
            self.segmentation = lines[cutLine+1].split(': ')[1]
            #how much time before the actual start
            self.tstart = float(lines[cutLine+2].split(': ')[1])
            #how much time after the actual end
            self.tend = float(lines[cutLine+3].split(': ')[1])
            # print(self.segmentation, self.tstart, self.tend) #debugging

            #4) izhikevich
            self.iza = float(lines[izhikevichLine+1].split(': ')[1])
            self.izb = float(lines[izhikevichLine+2].split(': ')[1])
            self.izc = float(lines[izhikevichLine+3].split(': ')[1])
            self.izd = float(lines[izhikevichLine+4].split(': ')[1])
            self.izGain = float(lines[izhikevichLine+5].split(': ')[1])
            # print(self.iza, self.izb, self.izc, self.izd, self.izGain) #debugging

            #5) dataset
            self.dataFolder = lines[datasetLine+1].split(': ')[1]
            self.texturev = lines[datasetLine+2].split(': ')[1].split(' ')
            self.forcev = lines[datasetLine+3].split(': ')[1].split(' ')
            self.palpationv = lines[datasetLine+4].split(': ')[1].split(' ')
            self.numIterations = int(lines[datasetLine+5].split(': ')[1])
            # print(self.dataFolder, self.texturev, self.forcev, self.palpationv) #debugging

            #6) classification
            self.numClasses = int(lines[classificationLine+1].split(': ')[1])
            self.numNeighbors = int(lines[classificationLine+2].split(': ')[1])

            #determines if the header file was read properly
            self.fileHeaderOk = True

            return True

        except:
            return False

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def load(file):
    '''
    loads a single file and converts the matrix format to a vector of vectors
    '''
    s = np.loadtxt(file)
    return [s[:,k] for k in range(np.size(s,1))]
#-------------------------------------------------------------------------------
def preproc_single(signal,filtObj):
    '''
    applies the pre-processing stage to one signal
    '''
    return sig.filtfilt(filtObj.b,filtObj.a,signal)
#-------------------------------------------------------------------------------
def load_and_preprocessing(files,numData,parallel=True,ord=4,fc=10,sampfreq=TBCONSTS.SAMPFREQ,tb0=0,tbf=1000,sensfactor=0.6):
    '''
    loads all the files and pre-process each signal individually
    '''
    numFiles = len(files)
    # print(files) # debugging

    #load data
    if parallel is True:
        #parallel
        pool = Pool() #for multiprocessing, use all available cores
        data = pool.map(load,files) #load all the data files
        pool.close()
        pool.join()
    else:
        #normal, sequential, takes 3.4x more time to run
        data = [np.loadtxt(f) for f in files]
        data = [[data[k][:,i] for i in range(17)] for k in range(numFiles)]

    #pre-processing
    #filter parameters
    filtobj = LowPass(ord,fc,sampfreq)
    #vector with filtered data
    filtData = [[] for k in range(numFiles)]
    #vector with event marking
    eventProtocol = []
    #counter for specific data type
    countdata = 0
    #apply pre-processing
    for k in range(numFiles):
        #pre-processing over the taxels
        for i in range(TBCONSTS.NTAXELS):
            #find the baseline value
            baselinev = np.mean(data[k][i][tb0:tbf])
            #convert to scale and normalize
            normv = convscale(data[k][i],baselinev,sensfactor*baselinev,0,1)
            #filter
            filtv = preproc_single(normv,filtobj)
            #saturation function
            filtsatv = funcsat(filtv,0,1)
            #apply filter
            filtData[k].append(filtsatv)

        #event curve
        #discard the last one since the event
        #was not properly created in the software
        if countdata < numData-1:
            eventProtocol.append(data[k][-1])
        elif countdata == 1:
            eventProtocol.append(data[k][-1])

        #increment the counter that tracks different data types
        countdata += 1
        #if all the samples from a given data type have been read
        #reset the counter
        if countdata >= numData:
            countdata = 0

    #return the pre-processed signals and the markings for each
    #file
    return filtData,eventProtocol
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def simulateParallel(simulobj):
    return simulobj.optParallel()

#run the simulation
def simulate(filtData,eventData,palpationtime,opt=True,fileHeaderName='fileHeader.txt'):
    '''
    generate spikes
    '''
    #get the number of different inputs --> files
    numData = len(filtData)
    #vector containing the simulation objects
    simulObj = [[] for k in range(TBCONSTS.NTAXELS)]
    #create a vector containing 16 neurons per input
    n = [[spkn.model.izhikevich() for k in range(numData)] for i in range(TBCONSTS.NTAXELS)]
    #each neuron will correspond to an individual taxel over all the inputs -> files
    i = [[filtData[k][i] for k in range(numData)] for i in range(TBCONSTS.NTAXELS)]
    #simulation parameters
    dt = 1 #time step
    # tstart = 0 #initial time
    # tend = 20000 #final time

    #find the initial and final time
    #initial time should be the first event to go high
    #final time should be the last to go low
    #initial time
    tstartCut = np.min([np.min(np.where(x == 2)[0]) for x in eventData])
    tstartCut += int(3.0*TBCONSTS.SAMPFREQ)
    # tstartCut -= int(0.5*TBCONSTS.SAMPFREQ)
    # tstartCut += 3000
    print('tstart:', tstartCut)
    # tendCut = np.max([np.max(np.where(x == 2)[0]) for x in eventData])
    palp = 100 / (150 / palpationtime) #how long it takes to move 10 cm
    tendCut = int(tstartCut + palp*TBCONSTS.SAMPFREQ + 1.0*TBCONSTS.SAMPFREQ)
    # tendCut -= 1000
    # tendCut = tstartCut + 6500
    print('tend:', tendCut)

    #save a file with the details of the processing
    fileHeader = open(fileHeaderName,'w')
    fileHeader.write('processing details')
    fileHeader.write('initial time: 3 seconds after pressing finished - ' + str(tstartCut))
    fileHeader.write('final time: palpation time + 0.5 ms after start - ' + str(tendCut))
    fileHeader.close()

    #cut the signals
    i = [[i[k][w][tstartCut:tendCut] for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
    #normalizing
    i = [[(i[k][w]/np.max(i[k][w]))*30 for w in range(numData)] for k in range(TBCONSTS.NTAXELS)]
    tstart = 0
    tend = tendCut - tstartCut

    #run the simulation
    #each taxel is simulated individually
    for k in range(TBCONSTS.NTAXELS):
        #indicates which simulation is running
        print('Simulation: ' + str(k))
        #create the object
        simulObj[k] = spkn.simulation(dt,tstart,tend,i[k],n[k])
        #run the simulation
        if opt is True: #optimal integration
            simulObj[k].optIzhikevich()
        else: #sequential
            simulObj[k].run()

    #return the vector containing the simulation results for each taxel
    return simulObj
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def analysis(simul,numSignals):
    '''
    analyze the simulation results
    '''
    nsimul = len(simul)
    rasters = [[] for k in range(nsimul)]
    isihist = [[] for k in range(nsimul)]
    for k in range(nsimul):
        #rastergram
        rasters[k] = spkn.analysis.raster(simul[k])
        #isi histogram
        isihist[k] = spkn.analysis.isi_histogram(simul[k],numSignals)

    #return the analysis
    return rasters,isihist
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def classification(simul,numSignals):
    '''
    run classification
    '''
    #output variables
    featobj = [[] for k in range(len(simul))] #feature extraction objects
    confmatrix = [[] for k in range(len(simul))] #confusion matrices
    clfreport = [[] for k in range(len(simul))] #classification reports
    #create the classifier
    n_neighbors = 10 #number of neighbors
    #create a k-NN classifier
    clf = neighbors.KNeighborsClassifier(n_neighbors,weights='distance')
    #feature extraction and classification
    #run each individually
    for k in range(len(simul)):
        #feature extraction
        featobj[k] = spkn.classification.feature_extraction(simul[k],numSignals)
        #run the classification with leave-one-out cross validation
        ret = spkn.classification.LOOCV(clf, featobj[k].features, featobj[k].targets)
        #save the outputs
        confmatrix[k] = ret[0]
        clfreport[k] = ret[1]

    #return the results
    return featobj, confmatrix, clfreport
#-------------------------------------------------------------------------------
def speed_analysis(numtextures,simulobj,isihist,filesuffix='',filepath='./results_speed/'):
    '''
    compare the results of different speeds on the same texture
    '''
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(isihist)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        for i in range(len(isihist[k].xvals)):
            plt.plot(isihist[k].xvals[i],isihist[k].yvals[i])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    filename = filepath + 'isigaussian_' + filesuffix + '.png'
    print(filepath)
    print(filename)
    plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def plotisi(numtextures,simulobj,isihist,filesuffix='',filepath='./'):
    '''
    compare the results of different speeds on the same texture
    '''
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(isihist)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        for i in range(len(isihist[k].xvals)):
            plt.plot(isihist[k].xvals[i],isihist[k].yvals[i])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    filename = filepath + 'isigaussian_' + filesuffix + '.png'
    print(filepath)
    print(filename)
    plt.savefig(filename, bbox_inches='tight')
#-------------------------------------------------------------------------------
def plot(simulobj,rasters,isihist,featobj,confmatrix,numsignals,numclasses,filesuffix='',filepath='./results/img/'):
    '''
    generates all the plots
    '''
    #plot the inputs
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(simulobj)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        for i in range(0,len(simulobj[k].I),numsignals):
            plt.plot(simulobj[k].timev,simulobj[k].I[i])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(filepath + 'inputs_' + filesuffix + '.png', bbox_inches='tight')

    #plot the rastergrams
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(rasters)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        for i in range(len(rasters[k].xvals)):
            plt.scatter(rasters[k].xvals[i],rasters[k].yvals[i],marker='|',color='k')
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(filepath + 'rasters_' + filesuffix + '.png', bbox_inches='tight')

    #plot the isi gaussians
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(isihist)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        for i in range(len(isihist[k].xvals)):
            plt.plot(isihist[k].xvals[i],isihist[k].yvals[i])
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(filepath + 'isigaussian_' + filesuffix + '.png', bbox_inches='tight')

    #plot the features
    print('plotting features')
    print(filepath)
    print(numclasses)
    l = input()
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(featobj)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        auxv = 0
        for i in range(numclasses):
            plt.scatter(featobj[k].features[auxv:auxv+numsignals,0],featobj[k].features[auxv:auxv+numsignals,1])
            auxv += numsignals
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(filepath + 'features_' + filesuffix + '.png', bbox_inches='tight')

    #plot the confusion matrices
    plt.figure(figsize=(19.2,10.8),dpi=100)
    for k in range(len(featobj)):
        plt.subplot(TBCONSTS.NROWS,TBCONSTS.NCOLS,k+1)
        plt.matshow(confmatrix[k],fignum=False,vmin=0,vmax=numsignals)
        plt.colorbar()
    manager = plt.get_current_fig_manager()
    manager.resize(*manager.window.maxsize())
    plt.savefig(filepath + 'confmatrix_' + filesuffix + '.png', bbox_inches='tight')

    #show the plots
    # plt.show()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    print('debugging')
    # fileHeader = '../../../projects/texture/analysis/testHeader.txt'
    # textureRecog = TextureRecognition()
    # ret = textureRecog.loadHeader(fileHeader)
    # if ret:
    #     textureRecog.createDatasetFiles()
    #     textureRecog.runProcessing()
