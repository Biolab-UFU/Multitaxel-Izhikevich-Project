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
# Texture data is saved in a way that the total number of samples between
# iterations might change. However, the number of samples after contact
# is established between the finger and the texture is fixed. In this sense,
# different palpation speeds will also produce the same number of data points
# during palpation.
#-------------------------------------------------------------------------------
# Possible values for force:
#   - 0.08, 0.14 and 0.20 in normalized scale for medium sensitivity
# Possible values for palpation time:
#   - 3, 6 and 9 seconds
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#Paths
import os, sys, glob
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/iLimb')
sys.path.append('../../../framework/libraries/UR10')
sys.path.append('../../../framework/libraries/HDArray')
sys.path.append('../../../framework/libraries/shape_recognition')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/statemachine')
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
from serialhandler import * #serial communication
from UR10 import * #UR10 controller
from iLimb import * #iLimb controller
from tactileboard import * #4x4 tactile board
from statemachine import * #state machines
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formTextures_gui.ui')
#-------------------------------------------------------------------------------
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-------------------------------------------------------------------------------
class CONSTS():
    RIGHT_TACTILE = '/dev/ttyACM0'
    RIGHT_ILIMB = '/dev/ttyACM1'
    RIGHT_UR10 = '10.1.1.6'
    PALPATION_TIME = 30 #10, 15, 30
    FORCE_THRESHOLD = 0.18
    TAXEL_INDEX_FINGER = 4
    MAX_ITERATIONS = 20
#-------------------------------------------------------------------------------
#parent: the parent window which will hold objects to every controller
class FormTextures(QMainWindow, Ui_MainWindow):

    FILEPREFIX = './artificial/texture_new3' + str(CONSTS.FORCE_THRESHOLD).replace('.','') + '_' + str(CONSTS.PALPATION_TIME) + '_Ite'
    FILESUFIX = '.txt'
    print('base filename: ', FILEPREFIX)

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
        self.indexTaxel = CONSTS.TAXEL_INDEX_FINGER
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # UR-10
        #-----------------------------------------------------------------------
        self.rightUR10 = UR10Controller(CONSTS.RIGHT_UR10)
        self.rightUR10PM = URPoseManager()
        self.rightUR10PM.load('newtexture.urpose')
        # print(self.rightUR10PM.getPosJoint('homeJ'))
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
        self.fingerArray = ['index',CONSTS.TAXEL_INDEX_FINGER,CONSTS.FORCE_THRESHOLD]
        time.sleep(1)
        # self.rightILimb.setPose('openHand')
        # time.sleep(2)
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # STATE MACHINE
        #-----------------------------------------------------------------------
        self.initState = 'idle'
        self.states = ['idle','home','object','pressing','touchok','palpation','waiting']
        self.machine = StateMachine(self.initState,self.states,self.stateChanged)
        self.machine.add_transition('moveHome','*','home',self.moveHome)
        self.machine.add_transition('restart','waiting','home',self.doRestart)
        self.machine.add_transition('moveObj','home','object',self.doMoveObj)
        self.machine.add_transition('touch','object','pressing')
        self.machine.add_transition('pressok','pressing','touchok')
        self.machine.add_transition('palpate','touchok','palpation',self.doPalpation)
        self.machine.add_transition('wait_save','palpation','waiting')
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # TEXTURES
        #-----------------------------------------------------------------------
        self.textureCounter = 0 #counts the number of iterations
        self.maxIt = CONSTS.MAX_ITERATIONS #number of iterations
        self.palpationTime = CONSTS.PALPATION_TIME #duration of the palpation itself
        #determines the total duration of the palpation sequence in seconds
        #includes moving to the object, closing the finger, palpating and
        #opening the finger
        self.totalPalpationTime = 34
        # self.totalPalpationTime = self.palpationTime + 4
        #-----------------------------------------------------------------------
        #file to store data
        self.fileHandler = None
        self.flagSave = False
        self.fileCounter = 0
        self.startCountingSamples = False
        self.samplesToSave = (TBCONSTS.SAMPFREQ * self.totalPalpationTime) + 1
        #-----------------------------------------------------------------------
        #curve
        self.patchIdx = 0
        self.timev = [0]
        self.timestep = 0
        self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.taxelPlot = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.dt = 1.0 / TBCONSTS.SAMPFREQ #sampling time
        self.maxTime = 40 #10 seconds window

        #3D array for each patch
        #right hand
        self.tactileRGB = []
        for k in range(TBCONSTS.NPATCH):
            self.tactileRGB.append([])
        for k in range(TBCONSTS.NPATCH):
            self.tactileRGB[k] = np.full((4,4,3),0,dtype=float)

        #timer to update the GUI with tactile patch data
        self.tactileTimer = QTimer()
        #connect the timer
        self.tactileTimer.timeout.connect(self.tactileUpdate)
        #set the interval
        self.tactileTimerItv = 50 #in ms
        self.tactileTimer.setInterval(self.tactileTimerItv)

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
        self.tactileBoard = TactileBoard(CONSTS.RIGHT_TACTILE,_filter=False,_sensitivity=TBCONSTS.MEDIUM_SENS)
        self.tactileBoard.loadCalibration() #loads the calibration file
        self.useCalib = True #use the calibration value
        # self.fileHandler = open(FormTextures.FILENAME,'w')

    #starts data acquisition
    def doStart(self):
        #move the UR10 to the home position
        self.machine.change('moveHome')
        #starts acquisition of the tactile board
        self.tactileBoard.start()
        #starts timer to process tactile data
        self.tactileTimer.start()
        #print a message to display that tactile data is being stored
        # print('saving...')

    #aborts data collection?
    def doStop(self):
        self.tactileTimer.stop()

    #event triggered when transition between states is completed
    def stateChanged(self):
        if self.machine.state == 'home':
            self.machine.change('moveObj')
        elif self.machine.state == 'object':
            self.machine.change('touch')
        elif self.machine.state == 'palpation':
            self.textureCounter += 1
            if self.textureCounter < self.maxIt:
                print('waiting for all samples')
                self.machine.change('wait_save')
        elif self.machine.state == 'touchok':
            print('palpation starting...')
            self.machine.change('palpate')

    #move to home position
    def moveHome(self):
        print('here!')
        self.rightILimb.disconnect()
        self.rightILimb = iLimbController(CONSTS.RIGHT_ILIMB)
        print(self.rightILimb.connect()) #connects to the iLimb
        #use saved position
        # self.rightUR10PM.moveUR_new_joint(self.rightUR10,'homeJ',5,-30,5)
        self.rightUR10PM.moveUR(self.rightUR10,'homeJ',3)
        time.sleep(3)

    def doMoveObj(self):
        print('Iteration: ', self.textureCounter+1)
        #open the file to be saved
        filename = FormTextures.FILEPREFIX + str(self.textureCounter) + FormTextures.FILESUFIX
        self.fileHandler = open(filename,'w')
        self.fileCounter = 0
        self.flagSave = True
        print('saving....')

        #move to the object where the texture is placed
        objP = self.rightUR10PM.getPosJoint('objectP')
        objP[2] += 75
        # self.rightUR10.movej(objP,2)
        # self.rightUR10.movel(objP,self.palpationTime)
        self.rightUR10PM.moveUR(self.rightUR10,'objectJ',2)
        # self.rightUR10PM.moveUR_new_joint(self.rightUR10,'objectJ',5,-30,2)
        time.sleep(2)
        # l=input()

        self.rightILimb.disconnect()
        self.rightILimb = iLimbController(CONSTS.RIGHT_ILIMB)
        self.rightILimb.connect() #connects to the iLimb


    #perform palpation
    def doPalpation(self):

        #start couting samples to be saved
        self.startCountingSamples = True

        # #close index finger
        # print('closing finger')
        # self.rightILimb.control('index','position',400)
        # time.sleep(2)

        #waits for a time before palpation
        time.sleep(3)

        #start the palpation
        objP = self.rightUR10PM.getPosJoint('objectP')
        objP[2] += 150
        self.rightUR10.movel(objP,self.palpationTime)
        # self.rightUR10.read_joints_and_xyzR()
        # xyzR = copy(self.rightUR10.xyzR)
        # # xyzR[1] += 18
        # xyzR[2] += 150
        # self.rightUR10.movel(xyzR,self.palpationTime)
        # self.rightUR10PM.moveUR_new_joint(self.rightUR10,'palpationJ',5,-30,self.palpationTime)
        # self.rightUR10PM.moveUR(self.rightUR10,'palpationP',self.palpationTime)
        time.sleep(self.palpationTime)

        print('opening finger')
        self.rightILimb.control('index','open',297)
        # time.sleep(2)

    #restart the palpation sequence
    def doRestart(self):
        #use saved position
        # self.rightUR10PM.moveUR(self.rightUR10,'gobackJ',2)
        # # self.rightUR10PM.moveUR_new_joint(self.rightUR10,'gobackJ',5,-30,3)
        # time.sleep(2)
        #use saved position
        self.rightUR10PM.moveUR(self.rightUR10,'homeJ',2)
        # self.rightUR10PM.moveUR_new_joint(self.rightUR10,'homeJ',5,-30,5)
        time.sleep(2)

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
            #matrix that converts tactile data back to raw format in V
            indexFingerRaw = np.zeros((TBCONSTS.NROWS,TBCONSTS.NCOLS))
            #loop through the taxels for converting the values back to V
            for i in range(TBCONSTS.NROWS):
                for j in range(TBCONSTS.NCOLS):
                    #convert tactile sample to raw voltage
                    indexFingerRaw[i][j] = self.tactileBoard.conv2raw(indexFingerData[i][j])
                    #save the sample to file
                    if self.fileCounter < self.samplesToSave and self.flagSave:
                        self.fileHandler.write(str(indexFingerRaw[i][j]) + ' ')

            #feedback control
            if self.machine.state == 'pressing':
                ret = self.rightILimb.doFeedbackTouchForce(tactileSample,self.fingerArray,100)
                if ret is True:
                    print('pressing finished')
                    self.machine.change('pressok')
                    self.rightILimb.resetControl()

            #checks if all the samples have been acquired
            #if not, increment the counter and skip to next line in file
            if self.fileCounter < self.samplesToSave and self.flagSave:
                # print(self.machine.state)
                # print(self.fileCounter,self.samplesToSave,self.flagSave,self.startCountingSamples)
                if self.startCountingSamples is True:
                    self.fileCounter += 1
                    if self.machine.state == 'touchok' or self.machine.state == 'palpation':
                        self.fileHandler.write('2')
                    elif self.machine.state == 'pressing':
                        self.fileHandler.write('1')
                    else:
                        self.fileHandler.write('0')
                else:
                    if self.machine.state == 'touchok' or self.machine.state == 'palpation':
                        self.fileHandler.write('2')
                    elif self.machine.state == 'pressing':
                        self.fileHandler.write('1')
                    else:
                        self.fileHandler.write('0')
                self.fileHandler.write('\n')
            #if all samples have been read, then close the file
            elif self.fileCounter == self.samplesToSave and self.flagSave:
                self.fileHandler.close()
                print('samples: ', self.fileCounter)
                self.fileCounter = 0
                self.flagSave = False
                self.startCountingSamples = False
                print('saved!')
                #restart acquisition
                if self.machine.state == 'waiting':
                    self.machine.change('restart')

            #plot only the last sample to improve fps
            #might look like a filter
            if k == n-1:
                auxcounter = 0
                for i in range(TBCONSTS.NROWS):
                    for j in range(TBCONSTS.NCOLS):
                        self.tactileRGB[0][i][j] = self.conv2color(indexFingerData[i][j])
                        self.taxelv[auxcounter].append(indexFingerRaw[i][j])
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
