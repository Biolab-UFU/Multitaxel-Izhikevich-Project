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
sys.path.append('../framework/libraries/slip')
sys.path.append('../framework/libraries/iLimb')
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
from serialhandler import SerialHandler #manage serial communication
from threadhandler import ThreadHandler #manage threads
from dataprocessing import * #moving average and saturation function
import datetime #stopwatch
from iLimb import * #i-Limb control
#-------------------------------------------------------------------------------
#Custom libraries
from slipboard import *
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formSlipBoard_gui.ui')
#-------------------------------------------------------------------------------
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-------------------------------------------------------------------------------
class CONSTS():
    PORT = '/dev/ttyACM1'
    SAMPFREQ = 333 #Hz
    ILIMB_PORT = '/dev/ttyACM0'
    INITPOS = 125
#-------------------------------------------------------------------------------
#parent: the parent window which will hold objects to every controller
class FormSlipBoard(QMainWindow, Ui_MainWindow):
    FILEPREFIX = './data/testing_Ite'
    FILESUFIX = '.txt'
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def __init__(self, parent=None):
        super(FormSlipBoard,self).__init__()
        self.setupUi(self)
        #-----------------------------------------------------------------------
        self.filename = '../projects/slip/slip_experiment_water_transparent_dath_1.txt'
        #parameters
        self.maxTime = 10
        self.timev = []
        self.time = 0
        self.dt = 1.0 / CONSTS.SAMPFREQ
        # self.thAcq = ThreadHandler(self.serialport.readPackage)
        #-----------------------------------------------------------------------
        #SLIP BOARD
        self.slipBoard = SlipBoard(CONSTS.PORT)
        #-----------------------------------------------------------------------
        #SLIP EVENTS
        self.mvafc = 5
        self.mvawindow = CONSTS.SAMPFREQ/self.mvafc
        self.mva = MovingAverage(_windowSize=self.mvawindow,_sampfreq=CONSTS.SAMPFREQ)
        self.prev = 0
        self.slipth = 0.005
        self.slipcount = 0
        self.slipsum = 0
        self.maxcount = 10
        self.slipevqueue = deque()
        self.slipevsum = 0
        self.slipevminus = 0
        #-----------------------------------------------------------------------
        #FTH (fixed threshold) slip detection
        self.fth_prev = 0
        self.fth_th = self.slipth
        self.fth_ev = [] #vector of events
        self.fth_flagTh = 0
        self.fth_numEvents = 0
        self.fth_sumv = 0
        self.fth_maxCount = int(0.1*CONSTS.SAMPFREQ)
        self.fth_sampCounter = 0
        #-----------------------------------------------------------------------
        #FTH (fixed threshold) slip detection
        self.fth_prev = 0
        self.fth_th = self.slipth
        self.fth_ev = [] #vector of events
        self.fth_flagTh = 0
        self.fth_sumv = 0
        self.fth_countSum = 0
        self.fth_maxCountSum = int(0.1*CONSTS.SAMPFREQ)
        self.fth_maxCount = int(0.05*CONSTS.SAMPFREQ)
        self.fth_sampCounter = 0
        self.fth_dt = 0.03
        self.fth_windowEv = np.zeros(int(self.fth_dt * CONSTS.SAMPFREQ))
        self.fth_idxEv = 0
        self.fth_timev = []
        self.fth_numEv = []
        self.fth_time = 0
        #-----------------------------------------------------------------------
        #DATH (dynamic adaptive threshold) slip detection
        self.dath_prev = 0
        self.dath_th = self.slipth
        self.dath_ev = [] #vector of events
        self.dath_flagTh = 0
        self.dath_sumv = 0
        self.dath_countSum = 0
        self.dath_maxCountSum = int(0.1*CONSTS.SAMPFREQ)
        self.dath_maxCount = int(0.05*CONSTS.SAMPFREQ)
        self.dath_sampCounter = 0
        self.dath_dt = 0.03
        self.dath_windowEv = np.zeros(int(self.dath_dt * CONSTS.SAMPFREQ))
        self.dath_idxEv = 0
        self.dath_timev = []
        self.dath_numEv = []
        self.dath_time = 0
        #-----------------------------------------------------------------------
        # MPI controller
        self.flagControl = False
        self.p0 = CONSTS.INITPOS
        self.mpi = [self.p0]
        self.mpi0 = 0
        self.v = 0
        self.z = 0
        self.Kp = 5
        self.Ki = 5
        #-----------------------------------------------------------------------
        #TIMER
        #timer to update the GUI with tactile patch data
        self.timer = QTimer()
        #connect the timer
        self.timer.timeout.connect(self.updateGUI)
        #set the interval
        self.timerItv = 50 #in ms
        self.timer.setInterval(self.timerItv)
        #-----------------------------------------------------------------------
        self.initGUI() #initialize the GUI
        #-----------------------------------------------------------------------
        #close ilimb
        self.iLimb = iLimbController(CONSTS.ILIMB_PORT)
        self.iLimb.connect()

        f = ['thumb','index','middle']
        a = ['open'] * len(f)
        p = [290] * len(f)
        self.iLimb.control(f,a,p)
        time.sleep(2)
        # self.iLimb.control('thumbRotator','close',297)
        # time.sleep(2)
        a = ['position'] * len(f)
        p = [CONSTS.INITPOS,CONSTS.INITPOS,CONSTS.INITPOS+40]
        self.iLimb.control(f,a,p)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def initGUI(self):
        #button events
        self.btnStart.clicked.connect(self.doStart)
        self.btnStop.clicked.connect(self.doStop)
        self.btnDistance.clicked.connect(self.doDistance)
        self.btnControlOn.clicked.connect(self.doControlOn)

        #initialize the plots
        #curve for the optic sensor
        self.dataOptic = []
        self.curveOptic = self.pltOptic.plot(pen=pg.mkPen('b',width=1))
        self.pltOptic.setXRange(min=0,max=self.maxTime,padding=0.01)
        #curve for the slip events
        self.dataSlipEvents = []
        self.dataSlipNumEvents = []
        self.curveSlipEvents = self.pltEvents.plot(pen=pg.mkPen('b',width=1))
        self.pltEvents.setXRange(min=0,max=self.maxTime,padding=0.01)
        #curve for the accelerometer outputs
        self.dataAccelX = []
        self.dataAccelY = []
        self.dataAccelZ = []
        self.curveAccelX = self.pltAccel.plot(pen=pg.mkPen('r',width=1))
        self.curveAccelY = self.pltAccel.plot(pen=pg.mkPen('b',width=1))
        self.curveAccelZ = self.pltAccel.plot(pen=pg.mkPen('g',width=1))
        self.pltAccel.setXRange(min=0,max=self.maxTime,padding=0.01)
        #curve for the distance sensor
        self.dataDistance = []
        self.curveDistance = self.pltDistance.plot(pen=pg.mkPen('b',width=1))
        self.pltDistance.setXRange(min=0,max=self.maxTime,padding=0.01)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def doStart(self):
        self.filehandler = open(self.filename,'w')
        self.slipBoard.start()
        # self.thAcq.start()
        self.timer.start()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def doStop(self):
        self.slipBoard.stop()
        self.timer.stop()
        self.filehandler.close()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def doDistance(self):
        self.slipBoard.readDistance()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def doControlOn(self):
        print('control on')
        self.flagControl = True
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def updateGUI(self):
        q = self.slipBoard.getData()
        n = len(q)
        # print(n)
        for k in range(n):
            # print(n) #debugging
            d = q.popleft()
            # print(d) #debuggings

            self.timev.append(self.time)
            self.dataAccelX.append(d[0])
            self.dataAccelY.append(d[1])
            self.dataAccelZ.append(d[2])
            self.dataDistance.append(d[3])

            filtsamp = self.mva.getSample(d[-1])
            self.dataOptic.append(filtsamp)

            # print(filtsamp)
            # print(d[4])

            #generate slip events
            self.slipsum += (filtsamp - self.prev)
            if np.abs(self.slipsum) > self.slipth:
                self.dataSlipEvents.append(1)
                self.slipsum = 0
            else:

                self.dataSlipEvents.append(0)
            self.slipcount += 1
            if self.slipcount >= self.maxcount:
                self.slipsum = 0
            self.prev = filtsamp

            #count number of events in a sliding window
            if len(self.slipevqueue) >= self.mvawindow:
                self.slipevsum -= self.slipevqueue.popleft()
                self.slipevsum += self.dataSlipEvents[-1]
                self.slipevqueue.append(self.dataSlipEvents[-1])
            else:
                # print('a',self.slipevsum,self.slipevqueue)
                self.slipevsum += self.dataSlipEvents[-1]
                # print('b',self.slipevsum,self.slipevqueue)
                self.slipevqueue.append(self.dataSlipEvents[-1])
            # print(self.slipevsum)
            self.dataSlipNumEvents.append(self.slipevsum)
            # print(self.slipevsum)
            #-------------------------------------------------------------------
            #-------------------------------------------------------------------
            # slip events using FTH

            #-------------------------------------------------------------------
            #slip events using DATH
            #-------------------------------------------------------------------
            if self.dath_flagTh == 1:
                self.dath_sampCounter += 1
                if self.dath_sampCounter >= self.dath_maxCount:
                    self.dath_th = self.slipth
                    self.dath_flagTh = 0
            self.dath_sumv += (filtsamp - self.dath_prev)

            if np.abs(self.dath_sumv) > self.dath_th:
                self.dath_ev.append(1)
                self.dath_sumv = 0
                # if self.dath_flagTh == 0:
                #     self.dath_flagTh = 1
                #     self.dath_th =  np.abs(filtsamp - self.dath_prev)
            else:
                self.dath_ev.append(0)
            self.dath_prev = filtsamp
            self.dath_windowEv[self.dath_idxEv] = self.dath_ev[-1]

            #check if the sum should be reset
            self.dath_countSum += 1
            if self.dath_countSum >= self.dath_maxCountSum:
                self.dath_countSum = 0
                self.dath_sumv = 0

            #check if number of events should be counted
            self.dath_idxEv += 1

            if self.dath_idxEv >= len(self.dath_windowEv):
                # print(np.sum(self.dath_windowEv))
                self.dath_idxEv = 0
                self.dath_numEv.append(np.sum(self.dath_windowEv))
                # print(self.dath_numEv)
                self.dath_timev.append(self.dath_time)
                self.dath_time += self.dath_dt
                ################################################################
                #MPI controller
                if self.flagControl:
                    self.v = self.dath_numEv[-1]
                    self.z += self.v
                    pi = self.p0 + self.Kp*self.v + self.Ki*self.z
                    if pi > 500:
                        pi = int(500)
                    if pi < 0:
                        pi = int(0)
                    if pi > self.mpi[-1]:
                        self.mpi.append(pi)
                    else:
                        self.mpi.append(self.mpi[-1])
                    print(self.mpi[-1])
                    if self.mpi[-1] != self.mpi[-2]:
                        f = ['thumb','index','middle']
                        a = ['position'] * len(f)
                        p = [int(self.mpi[-1]),int(self.mpi[-1]),int(self.mpi[-1])+20]
                        self.iLimb.control(f,a,p)
                ################################################################

            #save data to file
            [self.filehandler.write(str(x) + ' ') for x  in d]
            self.filehandler.write(str(filtsamp) + ' ' + str(self.dath_ev[-1]) + ' ' + str(self.mpi[-1]) + ' ' + str(d[4]) + '\n')

            self.time += self.dt
            if self.time >= self.maxTime:
                self.time = 0
                self.dataAccelX = []
                self.dataAccelY = []
                self.dataAccelZ = []
                self.dataDistance = []
                self.dataOptic = []
                self.timev = []
                self.dataSlipEvents = []
                self.dataSlipNumEvents = []
                self.dath_ev = []
                self.dath_timev = []
                self.dath_numEv = []
                self.dath_time = 0

        self.curveAccelX.setData(self.timev, self.dataAccelX)
        self.curveAccelY.setData(self.timev, self.dataAccelY)
        self.curveAccelZ.setData(self.timev, self.dataAccelZ)
        self.curveDistance.setData(self.timev, self.dataDistance)
        self.curveOptic.setData(self.timev, self.dataOptic)
        self.curveSlipEvents.setData(self.dath_timev, self.dath_numEv)
        # self.curveSlipEvents.setData(self.timev, self.dataSlipNumEvents)
        # self.timev.append(self.time)
        # print(self.timev)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormSlipBoard()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
