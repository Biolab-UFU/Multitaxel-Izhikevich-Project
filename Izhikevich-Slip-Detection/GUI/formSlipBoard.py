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
from dataprocessing import MovingAverage #moving average
import datetime #stopwatch
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
    PORT = '/dev/ttyACM0'
    SAMPFREQ = 40 #Hz
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
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def initGUI(self):
        #button events
        self.btnStart.clicked.connect(self.doStart)
        self.btnStop.clicked.connect(self.doStop)
        self.btnDistance.clicked.connect(self.doDistance)

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
        self.filehandler = open('../projects/slip/slip_experiment_black_40hz_textured_500_1.txt','w')
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
    def updateGUI(self):
        q = self.slipBoard.getData()
        n = len(q)
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

            #save data to file
            [self.filehandler.write(str(x) + ' ') for x  in d]
            self.filehandler.write(str(filtsamp) + ' ' + str(self.slipevsum) + '\n')

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

        self.curveAccelX.setData(self.timev, self.dataAccelX)
        self.curveAccelY.setData(self.timev, self.dataAccelY)
        self.curveAccelZ.setData(self.timev, self.dataAccelZ)
        self.curveDistance.setData(self.timev, self.dataDistance)
        self.curveOptic.setData(self.timev, self.dataOptic)
        self.curveSlipEvents.setData(self.timev, self.dataSlipNumEvents)
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
