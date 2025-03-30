# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
#-------------------------------------------------------------------------------
# Description: GUI for recording palpation data from artificial or natural
textures
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#Paths
import os, sys, glob
sys.path.append('../framework/libraries/general')
sys.path.append('../framework/libraries/iLimb')
sys.path.append('../framework/libraries/UR10')
sys.path.append('../framework/libraries/HDArray')
sys.path.append('../framework/libraries/shape_recognition')
sys.path.append('../framework/libraries/neuromorphic')
sys.path.append('../framework/libraries/statemachine')
#-------------------------------------------------------------------------------
#PyQt libraries
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
#-------------------------------------------------------------------------------
#Important libraries
import numpy as np
import pyqtgraph as pg
from scipy.io import loadmat
from collections import deque #necessary for acquisition
from copy import copy #useful for copying data structures
from threading import Thread, Lock #control access in threads
from threadhandler import ThreadHandler #manage threads
import datetime #stopwatch
#-------------------------------------------------------------------------------
#Custom libraries
from confighardware import * #handles the configuration file
from serialhandler import * #serial communication
from UR10 import * #UR10 controller
from iLimb import * #iLimb controller
from tactileboard import * #4x4 tactile board
from statemachine import * #state machines
import spiking_neurons as spkn
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formTextures_gui.ui')
#-------------------------------------------------------------------------------
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-------------------------------------------------------------------------------
class CONSTS():
    RIGHT_TACTILE = '/dev/ttyACM2'
    RIGHT_ILIMB = '/dev/ttyACM1'
    RIGHT_UR10 = '10.1.1.6'
    TBNTAXELS = 16
#-------------------------------------------------------------------------------
#parent: the parent window which will hold objects to every controller
class FormTextures(QMainWindow, Ui_MainWindow):

    FILEPREFIX = './data/testing_Ite'
    FILESUFIX = '.txt'

    def __init__(self, parent=None):
        super(FormTextures,self).__init__()
        self.setupUi(self)
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # TACTILE BOARD
        #-----------------------------------------------------------------------
        #define the object
        # self.tactileBoard = TactileBoard(CONSTS.RIGHT_TACTILE,_filter=False,_sensitivity=TBCONSTS.HIGH_SENS)
        #index finger taxel
        self.indexTaxel = 3
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # UR-10
        #-----------------------------------------------------------------------
        self.rightUR10 = UR10Controller(CONSTS.RIGHT_UR10)
        self.rightUR10PM = URPoseManager()
        self.rightUR10PM.load('new_palpation_positions.urpose')
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # ILIMB
        #-----------------------------------------------------------------------
        #creates the object
        self.rightILimb = iLimbController(CONSTS.RIGHT_ILIMB)
        self.rightILimb.connect() #connects to the iLimb
        self.rightILimb.control('index','open',297)
        # time.sleep(1)
        # self.rightILimb.control('thumb','open',0)
        self.fingerArray = ['index',2,0.15]
        time.sleep(1)
        a = input('waiting')
        # self.rightILimb.setPose('openHand')
        # time.sleep(2)
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # STATE MACHINE
        #-----------------------------------------------------------------------
        self.initState = 'idle'
        self.states = ['idle','home','grasping','slipexp']
        self.machine = StateMachine(self.initState,self.states,self.stateChanged)
        self.machine.add_transition('moveHome','*','home',self.moveHome)
        self.machine.add_transition('grasp','home','grasping')
        self.machine.add_transition('slip','grasping','slipexp',self.doSlipExp)
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # SLIP SUPPRESSION
        #-----------------------------------------------------------------------
        #counts number of samples
        self.countWinSamples = 0
        #size of window for measuring firing rate
        self.windowSize = 100 #samples
        #number of spikes in processing window
        self.numSpikes = [0 for k in range(CONSTS.TBNTAXELS)]
        #FA-I mechanoreceptor model
        self.famodel = [spkn.model.izhikevich(d=8.0) for k in range(CONSTS.TBNTAXELS)]
        #current for the neuron model
        self.facurrent = [[] for k in range(CONSTS.TBNTAXELS)]
        #aux vector for derivative
        self.prevsamp = [0 for k in range(CONSTS.TBNTAXELS)]
        #measure the firing rate of models
        self.firingFA = [[] for k in range(CONSTS.TBNTAXELS)]
        #mpi controller
        self.Kp = 0.5
        self.Ki = 0.5
        self.mpiv = [[] for k in range(CONSTS.TBNTAXELS)]
        #-----------------------------------------------------------------------
        #file to store data
        self.fileHandler = None
        self.flagSave = False
        self.fileCounter = 0
        self.startCountingSamples = True
        # self.samplesToSave = (TBCONSTS.SAMPFREQ * self.totalPalpationTime) + 1
        #-----------------------------------------------------------------------
        #curve
        self.patchIdx = 0
        self.timev = [0]
        self.timestep = 0
        self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.taxelPlot = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.dt = 1.0 / TBCONSTS.SAMPFREQ #sampling time
        self.maxTime = 10 #10 seconds window
        #-----------------------------------------------------------------------
        #3D array for each patch
        #right hand
        self.tactileRGB = []
        for k in range(TBCONSTS.NPATCH):
            self.tactileRGB.append([])
        for k in range(TBCONSTS.NPATCH):
            self.tactileRGB[k] = np.full((4,4,3),0,dtype=float)
        #-----------------------------------------------------------------------
        #timer to update the GUI with tactile patch data
        self.tactileTimer = QTimer()
        #connect the timer
        self.tactileTimer.timeout.connect(self.tactileUpdate)
        #set the interval
        self.tactileTimerItv = 50 #in ms
        self.tactileTimer.setInterval(self.tactileTimerItv)
        #-----------------------------------------------------------------------
        self.init() #initializes the GUI
    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #initalize the GUI
    def init(self):
        #load the available comports
        #find the available serial ports
        res = list_serial_ports()
        #add the serial ports to the combo box
        # self.cbSerialPort.addItems(res)

        #initialize the plots
        #curve
        self.taxelCurves = []
        for k in range(TBCONSTS.NROWS*TBCONSTS.NCOLS):
            self.taxelCurves.append(self.pltTactilePatch.plot(pen=pg.mkPen(k,7,width=1)))
        self.pltTactilePatch.setXRange(min=0,max=self.maxTime,padding=0.1)

        #create a viewbox to the neuromorphic array
        #pltArray is the GraphisView object promoted to GraphisLayoutWidget
        #in QtDesigner
        #tactile sensors
        #add the graphics for each 4x4 tactile sensor patch
        self.pltTactile = [self.pltTS0]

        #remove borders
        [x.ci.layout.setContentsMargins(0,0,0,0) for x in self.pltTactile]
        [x.ci.layout.setSpacing(0) for x in self.pltTactile]

        #right hand tactile sensors
        self.vbTactile = []
        [self.vbTactile.append(x.addViewBox()) for x in self.pltTactile]
        self.tactileImg = []
        for k in range(len(self.pltTactile)):
            self.tactileImg.append(pg.ImageItem(np.zeros((TBCONSTS.NROWS,TBCONSTS.NCOLS))))
        for k in range(len(self.pltTactile)):
            self.vbTactile[k].addItem(self.tactileImg[k])

        #events from the buttons
        self.btnStart.clicked.connect(self.doStart)
        self.btnStop.clicked.connect(self.doStop)
        self.btnConnect.clicked.connect(self.doConnect)

    #connects to the tactile board
    def doConnect(self):
        self.tactileBoard = TactileBoard(CONSTS.RIGHT_TACTILE,_filter=True,_sensitivity=TBCONSTS.HIGH_SENS)
        self.tactileBoard.loadCalibration() #loads the calibration file
        self.tactileBoard.useCalib = True #use the calibration value
        # self.fileHandler = open(FormTextures.FILENAME,'w')

    #starts data acquisition
    def doStart(self):
        #move the UR10 to the home position
        # self.machine.change('moveHome')
        #starts acquisition of the tactile board
        self.tactileBoard.start()
        #starts timer to process tactile data
        self.tactileTimer.start()
        #print a message to display that tactile data is being stored
        # print('saving...')
        self.fileHandler = open('slip2.txt','w')

    #aborts data collection?
    def doStop(self):
        self.tactileTimer.stop()
        self.fileHandler.close()

    #event triggered when transition between states is completed
    def stateChanged(self):
        if self.machine.state == 'home':
            self.machine.change('moveObj')
        elif self.machine.state == 'object':
            self.machine.change('touch')
        elif self.machine.state == 'palpation':
            self.textureCounter += 1
            if self.textureCounter < self.maxIt:
                self.machine.change('restart')
        elif self.machine.state == 'touchok':
            print('palpation starting...')
            self.machine.change('palpate')

    #move to home position
    def moveHome(self):
        # print('here!')
        self.rightILimb.disconnect()
        self.rightILimb = iLimbController(CONSTS.RIGHT_ILIMB)
        print(self.rightILimb.connect()) #connects to the iLimb
        #use saved position
        self.rightUR10PM.moveUR(self.rightUR10,'homeJ',5)
        time.sleep(5)

    def doSlipExp(self):
        return 0

    #timer that updates reads the tactile data, saves them to a text file
    #and plot the results on the screen
    def tactileUpdate(self):
        #retrieves the queue containing all the tactile data that has been
        #read from the board
        q = self.tactileBoard.getData()
        n = len(q) #get the number of samples available
        for k in range(n):
            #get one sample from the queue
            tactileSample = q.popleft()
            #get the index finger tactile data
            indexFingerData = tactileSample[self.indexTaxel]

            #take derivative of each signal
            #integrate the FA-I mechanoreceptor model
            #check if firing rate should be measured
            auxrow = 0
            auxcol = 0
            for w in range(CONSTS.TBNTAXELS):
                #derivative
                diffsamp = 500 * (np.abs(indexFingerData[auxrow,auxcol] - self.prevsamp[w]))
                self.facurrent[w].append(diffsamp)
                self.fileHandler.write(str(indexFingerData[auxrow,auxcol]) + ' ')
                self.prevsamp[w] = indexFingerData[auxrow,auxcol]
                # print(diffsamp)
                auxcol += 1
                if auxcol >= TBCONSTS.NCOLS:
                    auxcol = 0
                    auxrow += 1
                    if auxrow >= TBCONSTS.NROWS:
                        auxrow = 0
                #integrate the model
                resp = self.famodel[w].integrate(0,1)
                #check if a spike has been triggered
                if resp[0] is True:
                    self.numSpikes[w] += 1 #increment number of spikes
                    # self.facurrent[w].append(resp[2])
                # self.facurrent[w].append(resp[1])
                #slip suppression
                if self.machine.state == 'slipexp':
                    #check if it is time to measure firing rate
                    if self.countWinSamples == self.windowSize-1:
                        #measure firing rate
                        self.firingFA[w].append(self.numSpikes / (self.windowSize/1000.0))
                        #integrate the firing rate
                        self.integFA[w] += self.firingFA[w]
                        #PI response
                        auxv = self.Kp * self.firingFA[w] + self.Ki*self.integFA[w]
                        #saturation - min
                        if auxv < 0:
                            auxv = 0
                        #saturation - max
                        if auxv > 500:
                            auxv = 500
                        #mpi controller
                        if auxv > self.mpiv[w][-1]:
                            self.mpiv[w].append(auxv)
                            print(self.mpiv[w])

            self.fileHandler.write('\n')
            #increment the number of samples read
            self.countWinSamples += 1
            #reset the counter of samples
            if self.countWinSamples >= self.windowSize:
                self.countWinSamples = 0
                #reset the counter of spikes
                self.numSpikes = [0 for w in range (CONSTS.TBNTAXELS)]

            # #checks if all the samples have been acquired
            # #if not, increment the counter and skip to next line in file
            # if self.fileCounter < self.samplesToSave and self.flagSave:
            #     self.fileHandler.write('\n')
            #     # print(self.fileCounter,self.samplesToSave,self.flagSave,self.startCountingSamples)
            #     if self.startCountingSamples is True:
            #         self.fileCounter += 1
            # #if all samples have been read, then close the file
            # elif self.fileCounter == self.samplesToSave and self.flagSave:
            #     self.fileHandler.close()
            #     print('samples: ', self.fileCounter)
            #     self.fileCounter = 0
            #     self.flagSave = False
            #     self.startCountingSamples = False
            #     print('saved!')

            #plot only the last sample to improve fps
            #might look like a filter
            if k == n-1:
                auxcounter = 0
                for i in range(TBCONSTS.NROWS):
                    for j in range(TBCONSTS.NCOLS):
                        self.tactileRGB[0][i][j] = self.conv2color(indexFingerData[i][j])
                        self.taxelv[auxcounter].append(self.facurrent[auxcounter][-1])
                        # print(self.facurrent[auxcounter][-1])
                        # self.taxelv[auxcounter].append(indexFingerData[i][j])
                        # self.taxelv[auxcounter].append(indexFingerRaw[i][j])
                        self.taxelCurves[auxcounter].setData(self.timev,self.taxelv[auxcounter])
                        auxcounter += 1
                self.tactileImg[0].setImage(self.tactileRGB[0],levels=(0,255))

                #update curve
                #self.taxelCurve.setData(self.timev,self.taxelv)
                self.timev.append(self.timestep)
                self.timestep += (self.dt*n)
                if self.timestep >= self.maxTime:
                    self.timev = [0]
                    self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
                    self.timestep = 0
                    self.facurrent = [[] for k in range(CONSTS.TBNTAXELS)]

    #convert tactile data to RGB color --> colormap
    def conv2color(self,vnorm):
        a = (1-vnorm)/0.25
        x = np.floor(a)
        y = np.floor(255*(a-x))
        if x == 0:
            r = 255; g=y; b=0;
        elif x == 1:
            r = 255-y; g=255; b=0;
        elif x==2:
            r=0; g=255; b=y;
        elif x==3:
            r=0; g=255-y; b=255;
        else:
            r=0; g=0; b=255;
        return [int(r),int(g),int(b)]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormTextures()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
