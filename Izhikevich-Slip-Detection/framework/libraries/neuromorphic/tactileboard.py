# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
# ONR Presentation: June 13th, 2018
#-------------------------------------------------------------------------------
# Description: Library for handling serial communication with the main board
# that reads the 4x4 tactile sensors
# The values returned by the library are normalized between 0 and 1 according
# to the specified sensitivity using TBCONSTS. If default is chosen, then
# the value will be normalized using the full range of the ADC.
#-------------------------------------------------------------------------------
# Notes:
# 1) Columns and Rows have been swapped for proper visualization. That is why
# rows and cols will appear weird in the code (rows first, then cols when
# accessing the taxel matrix).
# 2) The complete tactile sensor matrix have been flipped in the end also for
# visualization purposes
# 3) Moving average is already being applied to the raw signal
# 4) Returns normalized values between 0 and 1 with respect to the desired
# sensitivity
# 5) A text file can be generated when calibrating the sensors. The calibration
# procedure can be implemented in a GUI such as the 'formTactileBoard' contained
# at ONR-2018/GUI.
# 6) The calibration procedure will generate a new maximum value for each taxel
# of each tactile patch
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#Paths
import os, sys, glob
sys.path.append('../general') #general libraries
import numpy as np #numpy
import time #sleep
import datetime
from threading import Thread, Lock #handling concurrent threads
from collections import deque #queue for handling data
from copy import copy #copy is necessary to avoid problems
from serialhandler import SerialHandler #serial handler for communication
from threadhandler import ThreadHandler #thread handler for data acquisition
from dataprocessing import * #moving average
#-------------------------------------------------------------------------------
class TBCONSTS:
    #---------------------------------------------------------------------------
    #Hardware parameters
    #Number of rows in the tactile sensor
    NROWS = 4
    #Number of columns in the tactile sensor
    NCOLS = 4
    #Total number of taxels
    NTAXELS = NROWS * NCOLS
    #Number of tactile patches in the main board
    NPATCH = 5
    #---------------------------------------------------------------------------
    #sensitivity
    #---------------------------------------------------------------------------
    DEFAULT_SENS = 0x00
    HIGH_SENS = 0x01
    MEDIUM_SENS = 0x02
    LOW_SENS = 0x03
    #---------------------------------------------------------------------------
    #calibration procedure
    CALIBRATION_IDLE = 0x00
    CALIBRATION_ONGOING = 0x01
    CALIBRATION_FINISHED = 0x02
    #---------------------------------------------------------------------------
    SAMPFREQ = 1000 #Hz
    #---------------------------------------------------------------------------
    ROW_IDX = [1,0,3,2]
    # ROW_IDX = [0,1,2,3]
    # COL_IDX = []
    #---------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class TactileBoard():
    def __init__(self,_port='COM3',_flagSpike=False,_sensitivity=TBCONSTS.HIGH_SENS,_filter=True):
        self.NROWS = 4 #number of rows
        self.NCOLS = 4 #number of columns
        self.NPATCH = 5 #number of sensors
        self.port = _port #port name
        self.filter = _filter #determines whether input data should be filtered
        self.dataQueue = deque() #data queue
        self.thAcqLock = Lock() #lock for data acquisition
        self.thProcLock = Lock() #lock for data processing
        #serial handler for receiving data
        self.serialHandler = SerialHandler(self.port,7372800,_header=0x24,_end=0x21,_numDataBytes=162,_thLock=self.thAcqLock)
        #thread for receiving packages
        self.thAcq = ThreadHandler(self.serialHandler.readPackage)
        #thread for processing the packages
        self.thProc = ThreadHandler(self.processData)
        #moving average for all taxels of each tactile sensor patch
        self.mva = [[] for k in range(TBCONSTS.NPATCH*TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        for k in range(len(self.mva)):
            self.mva[k] = copy(MovingAverage(_windowSize = TBCONSTS.SAMPFREQ/10)) #10 Hz cut-off frequency
        self.taxelCounter = 0 #counter for moving average across all taxels
        #matrix for storing previous values --> necessary for integrate and fire spikes
        self.prevTactile = np.zeros((TBCONSTS.NPATCH,TBCONSTS.NROWS,TBCONSTS.NCOLS),dtype=float)
        #threshold for spike detection
        self.threshold = 100
        #flag that determines whether spikes or raw values should be used
        self.flagSpike = _flagSpike
        #flag that determines whether the slip sensor should be used
        self.useSlipSensor = False
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #NORMALIZATION --> adjusts sensitivity of the tactile sensors
        #-----------------------------------------------------------------------
        self.sensitivity = _sensitivity #determines which sensitivity should be used
        self.vmax = 2.46 #maximum possible voltage
        self.vhigh = 0.85 #voltage range for high sensitivity as a ratio of self.vmax
        self.vmed = 0.6 #voltage range for medium sensitivity as a ratio of self.vmax
        self.vlow = 0.3 #voltage range for low sensitivity as a ratio of self.vmax
        self.vdef = 0 #voltage range for default sensitivity (no normalization)
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #CALIBRATION
        #-----------------------------------------------------------------------
        #temporary matrix to store the calibration values
        self.calibMatrix = None #initializes the calibration matrix
        #initializes the temporary matrix containing the calibration values
        self.tempCalib = [np.zeros((TBCONSTS.NROWS,TBCONSTS.NCOLS)) for k in range(TBCONSTS.NPATCH)]
        self.flagCalib = False #determines whether calibration is ongoing
        self.calibCount = 0 #counter necessary for keeping track of the number of samples
        self.useCalib = False #determines whether calibration should be used
        self.calibStatus = TBCONSTS.CALIBRATION_IDLE #initializes calibration as idle
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #RECORDING
        self.flagRecording = False
        self.filename = None
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #STOPWATCH DEBUGGING
        #-----------------------------------------------------------------------
        self.swFlag = False
        self.swCounter = 0
        self.swMaxSamples = TBCONSTS.SAMPFREQ * 2
        self.swT0 = None
        self.swT1 = None

    #method to load text file containing calibration parameters for a specific
    #tactile board
    #file format has 5 lines, with 16 values each
    #each line corresponds to a patch --> from patch 1 to 5 following the schematics
    #each line (patch) contains 16 values (taxels) arranged with respect to
    #columns
    def loadCalibration(self):
        filename = self.port
        #'/' in the filename indicates path and causes error
        #'/' is present in linux based systems as com ports
        if '/' in self.port:
            filename =  filename.replace('/','_')
        filepath = 'tactileboard_' + filename + '_calib.cfg'
        print(filepath)
        #check if file exists
        if os.path.isfile(filepath):
            #load the file
            self.calibValues = np.loadtxt(filepath)
            #calibration matrix
            #list containing 4x4 matrices
            self.calibMatrix = [np.zeros((TBCONSTS.NROWS,TBCONSTS.NCOLS)) for k in range(TBCONSTS.NPATCH)]
            for n in range(TBCONSTS.NPATCH):
                auxcounter = 0
                for i in range(TBCONSTS.NROWS):
                    for j in range(TBCONSTS.NCOLS):
                        #create the calibration matrix
                        self.calibMatrix[n][i][j] = self.calibValues[n][auxcounter]
                        auxcounter+=1 #increment counter
            # print('calib ok')
            return True
        else:
            print('file not found')
            return False #file not found

    #saves the calibration result to a text file
    def saveCalibration(self):
        try:
            filename = self.port
            #'/' in the filename indicates path and causes error
            #'/' is present in linux based systems as com ports
            if '/' in self.port:
                filename = filename.replace('/','_')
            filepath = 'tactileboard_' + filename + '_calib.cfg'
            filehandler = open(filepath,'w')
            for n in range(TBCONSTS.NPATCH):
                strline = ''
                for i in range(TBCONSTS.NROWS):
                    for j in range(TBCONSTS.NCOLS):
                        strline = strline + str(self.tempCalib[n][i][j]) + ' '
                strline += '\n'
                filehandler.write(strline)
            filehandler.close()
            return True
        except:
            return False

    #start data acquisition
    def start(self):
        self.serialHandler.open() #open the serial port
        self.thAcq.start() #start data acquisition
        self.thProc.start() #start data processing

    #stop acquisition
    def stop(self):
        self.thAcq.kill() #kill thread
        self.thProc.kill() #kill thread

    #if nsamples == 0, then calibration will only stop when the method
    #doStopCalib is explicitly called. otherwise, the calibration process
    #will stop automatically once 'nsamples' have been acquired for each
    #taxel of all patches
    def startCalibration(self,nsamples=0):
        self.flagCalib = True
        self.calibCount = 0
        self.calibMaxSamples = nsamples
        self.calibStatus = TBCONSTS.CALIBRATION_ONGOING

    #stops calibration
    def stopCalibration(self):
        self.flagCalib = False
        self.calibCount = 0
        self.calibStatus = TBCONSTS.CALIBRATION_FINISHED
        th = Thread(target=self.saveCalibration)
        #th.daemon = True
        th.start()

    #start recording a file
    def startRecording(self,filename):
        self.filename = filename #receives the name of the file
        self.fileHandler = open(self.filename, 'w') #creates the file
        self.flagRecording = True #signals the thread to record data

    #stops recording the file
    def stopRecording(self):
        self.flagRecording = False #signals the thread to stop recording
        self.fileHandler.close() #saves the file

    #method that takes the raw data coming from the serial port and rearranges
    #them into proper 4x4 matrices
    def processData(self):
        #x = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.thAcqLock.acquire()
        n = len(self.serialHandler.dataQueue)
        q = copy(self.serialHandler.dataQueue)
        self.serialHandler.dataQueue.clear()
        self.thAcqLock.release()
        #y = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        #if n > 0:
        #    print(x,y,n)

        #3d array containing the 4x4 matrix of each tactile patch
        self.tactileSensors = np.zeros((TBCONSTS.NPATCH,TBCONSTS.NROWS,TBCONSTS.NCOLS),dtype=float)

        for k in range(n):
            data = q.popleft()
            # data = data[2:] + data[0:2]

            if self.swFlag is True:
                self.swCounter += 1
                # print(self.swCounter)
                if self.swCounter >= self.swMaxSamples:
                    self.swFlag = 0
                    self.swT1 = datetime.datetime.now()
                    print('here!',self.swT1 - self.swT0)

            for z in range(0,160,2):

                patchNum = int((z/2)%TBCONSTS.NPATCH)
                row = int((z/2)%(TBCONSTS.NROWS*TBCONSTS.NPATCH)//TBCONSTS.NPATCH)
                row = TBCONSTS.ROW_IDX[row]
                col = int((z/2)//(TBCONSTS.NCOLS*TBCONSTS.NPATCH))

                #re-arrange the adc sample
                sample = data[z]<<8 | data[z+1]
                # sample = sample >> 4

                # print(n,k,z,z/2,patchNum,row,col,sample) #debugging

                #if output format is spikes
                if self.flagSpike:
                    if(sample - self.prevTactile[patchNum][col][row] > self.threshold):
                        self.tactileSensors[patchNum][col][row] = 1
                        #print(sample,self.prevTactile[patchNum][col][row])
                    elif(self.prevTactile[patchNum][col][row] - sample > self.threshold):
                        self.tactileSensors[patchNum][col][row] = 0
                    else:
                        self.tactileSensors[patchNum][col][row] = 0.5
                    self.prevTactile[patchNum][col][row] = sample
                #if output format is normalized amplitude values
                else:
                    if self.filter: #if data should be filtered
                        # filtsample = sample
                        filtsample = self.mva[self.taxelCounter].getSample(sample)
                    else: #otherwise, read raw data
                        filtsample = sample

                    #saves data to a text file
                    if self.flagRecording:
                        self.fileHandler.write(str(sample*(3.3/4096)) + ' ')

                    #calibration process
                    if self.flagCalib:
                        auxmean = self.tempCalib[patchNum][col][row]
                        auxsample = self.tactileSensors[patchNum][col][row]
                        auxmean = auxmean*(self.calibCount/(self.calibCount+1)) + (filtsample/(self.calibCount+1))
                        self.tempCalib[patchNum][col][row] = auxmean

                    #normalizing the taxels and putting in the appropriate 5x4x4 matrix
                    # self.tactileSensors[patchNum][col][row] = filtsample
                    self.tactileSensors[patchNum][col][row] = self.normalize(filtsample,patchNum,col,row)
                    self.taxelCounter += 1
                    if self.taxelCounter >= (self.NPATCH*self.NROWS*self.NCOLS):
                        self.taxelCounter = 0

            #skips the file to the next line
            if self.flagRecording:
                self.fileHandler.write('\n')

            #calibration procedure
            if self.flagCalib:
                #increment the counter of samples for
                self.calibCount += 1
                #check if the number of specified samples have been acquired or not
                if self.calibMaxSamples > 0 and self.calibCount >= self.calibMaxSamples:
                    self.stopCalibration()
                    #print('finished') #debugging
                    #print(self.tempCalib[patchNum]) #debugging

            self.thProcLock.acquire()
            for w in range(self.NPATCH):
                self.tactileSensors[w] = self.tactileSensors[w]
                #self.tactileSensors[w] = np.flip(np.flip(self.tactileSensors[w],0),1)
            #if the slip sensor is being used, the data queue will be different
            if self.useSlipSensor is True:
                #slip sensor data
                slipSensor = (data[160]<<8 | data[161]) * (3.3/4096)
                # print(slipSensor)
                #print('slip sensor', slipSensor) #debugging
                #create a list where the first position refers to the tactile data
                #and the second position to the slip sensor data
                listdata = []
                listdata.append(copy(self.tactileSensors))
                listdata.append(copy(slipSensor))
                self.dataQueue.append(copy(listdata))
            else: #default -- no slip sensor
                self.dataQueue.append(copy(self.tactileSensors))
            self.thProcLock.release()

        time.sleep(0.001) #necessary to prevent really fast thread access

    #returns the data queue
    def getData(self):
        self.thProcLock.acquire()
        q = copy(self.dataQueue)
        self.dataQueue.clear()
        self.thProcLock.release()
        return q

    #normalize the tactile sensor signal according to the sensitivity specified
    def normalize(self,adcsample,patchNum=0,col=0,row=0):
        if self.sensitivity == TBCONSTS.HIGH_SENS: #high sens
            vsens = self.vhigh
        elif self.sensitivity == TBCONSTS.MEDIUM_SENS: #medium sens
            vsens = self.vmed
        elif self.sensitivity == TBCONSTS.LOW_SENS: #low sens
            vsens = self.vlow
        else:
            vsens = self.vdef #no normalization
        # print(self.useCalib)
        #if the calibration matrix is instantiated, use it as parameter for
        #normalization in a pixel by pixel fashion
        if self.calibMatrix is not None and self.useCalib is True:
            vmax = self.calibMatrix[patchNum][col][row] * (3.3/4096)
            # print(vmax) #debugging
        #otherwise, let default normalization take place where voltage values are
        #fixed without considering taxel behavior
        else:
            vmax = self.vmax

        #adjusts sensitivity based on the proper maximum value that is either
        #given by the calibration matrix or the fixed default value
        vsens *= vmax

        #convert the adc value back to volts
        vsample = adcsample * (3.3/4096.)

        #convert from volts to a normalized value given the sensitivity
        vnorm = ((vsample-vsens)*-1)/(vmax-vsens) + 1

        #check if the normalization values are within range (0 to 1)
        if vnorm > 1:
            vnorm = 1
        elif vnorm < 0:
            vnorm = 0

        #print(vnorm,vsample,vmax,vsens) #debugging

        #return the normalized value
        return vnorm

    def conv2raw(self,vnorm,patchNum=0,col=0,row=0):
        if self.sensitivity == TBCONSTS.HIGH_SENS: #high sens
            vsens = self.vhigh
        elif self.sensitivity == TBCONSTS.MEDIUM_SENS: #medium sens
            vsens = self.vmed
        elif self.sensitivity == TBCONSTS.LOW_SENS: #low sens
            vsens = self.vlow
        else:
            vsens = self.vdef #no normalization

        #if the calibration matrix is instantiated, use it as parameter for
        #normalization in a pixel by pixel fashion
        if self.calibMatrix is not None and self.useCalib is True:
            vmax = self.calibMatrix[patchNum][col][row] * (3.3/4096)
            #print(vmax) #debugging
        #otherwise, let default normalization take place where voltage values are
        #fixed without considering taxel behavior
        else:
            vmax = self.vmax

        #adjusts sensitivity based on the proper maximum value that is either
        #given by the calibration matrix or the fixed default value
        vsens *= vmax

        vsample = -1*(((vmax-vsens)*(vnorm-1)) - vsens)

        return vsample

    def conv2sens(self,vnorm,desiredSens,patchNum=0,col=0,row=0):
        if desiredSens == TBCONSTS.HIGH_SENS: #high sens
            vsens = self.vhigh
        elif desiredSens == TBCONSTS.MEDIUM_SENS: #medium sens
            vsens = self.vmed
        elif desiredSens == TBCONSTS.LOW_SENS: #low sens
            vsens = self.vlow
        else:
            vsens = self.vdef #no normalization

        #if the calibration matrix is instantiated, use it as parameter for
        #normalization in a pixel by pixel fashion
        if self.calibMatrix is not None and self.useCalib is True:
            vmax = self.calibMatrix[patchNum][col][row] * (3.3/4096)
            #print(vmax) #debugging
        #otherwise, let default normalization take place where voltage values are
        #fixed without considering taxel behavior
        else:
            vmax = self.vmax

        #adjusts sensitivity based on the proper maximum value that is either
        #given by the calibration matrix or the fixed default value
        vsens *= vmax

        vraw = self.conv2raw(vnorm,patchNum,col,row)

        newvnorm = ((vraw-vsens)*-1)/(vmax-vsens) + 1

        return newvnorm
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__=='__main__':
    def update():
        global tactileBoard
        q = tactileBoard.getData()
        n = len(q)
        for k in range(n):
            data = q.popleft()
            #print(data[0])
        time.sleep(0.001)

    thMain = ThreadHandler(update)
    # tactileBoard = TactileBoard('COM3')
    tactileBoard = TactileBoard('/dev/ttyACM0')
    tactileBoard.start() #starts data acquisition
    thMain.start() #starts the thread for the update function
    a = input() #wait for keyboard entry to stop the program
    tactileBoard.swT0 = datetime.datetime.now()
    tactileBoard.swFlag = True
    a = input() #wait for keyboard entry to stop the program

    #calibration
    #tactileBoard.start()
    #tactileBoard.startCalibration(1200) #1200 samples = 3 s
    #time.sleep(4) #wait for calibration to be over
    #tactileBoard.loadCalibration() #load the calibration file
