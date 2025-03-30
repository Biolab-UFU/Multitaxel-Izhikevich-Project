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
# GUI design and implementation: Following a simple View-Controller framework
#-------------------------------------------------------------------------------
'''
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
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('tactile_gui.ui')
#-------------------------------------------------------------------------------
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-------------------------------------------------------------------------------
class TBCONSTS():
    NROWS = 3
    NCOLS = 2
    NTAXELS = 6
    SAMPFREQ = 2000 #Hz
    NUMDATABYTES = 12
    LSBV = 3.3 / 4096
#-------------------------------------------------------------------------------
class FormTactile(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(FormTactile,self).__init__()
        self.setupUi(self)

        #curve
        self.patchIdx = 0
        self.timev = [0]
        self.timestep = 0
        self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.dt = 1.0 / TBCONSTS.SAMPFREQ #sampling time
        self.maxTime = 10 #10 seconds window

        #timer to update the GUI with tactile patch data
        self.tactileTimer = QTimer()
        #connect the timer
        self.tactileTimer.timeout.connect(self.tactileUpdate)
        #set the interval
        self.tactileTimerItv = 50 #in ms
        self.tactileTimer.setInterval(self.tactileTimerItv)

        #matrix storing taxel values
        self.taxelMat = [[] for k in range(TBCONSTS.NTAXELS)]

        #board handler
        self.tactileHandler = None
        self.thAcq = None
        self.lock = Lock()

        #filehandler
        self.fileHandler = None
        self.flagRecording = False

        #initialize the GUI
        self.init()

    #initalize the GUI
    def init(self):
        #load the available comports
        #find the available serial ports
        res = list_serial_ports()
        #add the serial ports to the combo box
        self.cbPorts.addItems(res)

        #button events
        self.btnConnect.clicked.connect(self.doConnect)
        self.btnStart.clicked.connect(self.doStart)
        self.btnStop.clicked.connect(self.doStop)
        #recording option --> will save data to a file
        self.chRecording.toggled.connect(self.doRecording)

        #curve
        self.taxelCurves = []
        for k in range(TBCONSTS.NROWS*TBCONSTS.NCOLS):
            self.taxelCurves.append(self.pltTactilePatch.plot(pen=pg.mkPen(k,7,width=1)))
        self.pltTactilePatch.setXRange(min=0,max=self.maxTime,padding=0.1)

    def doConnect(self):
        selectedPort = self.cbPorts.currentText()
        self.tactileHandler = SerialHandler(_port=selectedPort,_header=0x24,_end=0x21,_numDataBytes=TBCONSTS.NUMDATABYTES,_thLock=self.lock)
        self.tactileHandler.open()
        time.sleep(1)
        self.thAcq = ThreadHandler(self.tactileHandler.readPackage)

    def doStart(self):
        self.thAcq.start()
        self.tactileTimer.start()

    def doStop(self):
        self.tactileTimer.stop()

    def doRecording(self):
        if self.sender().isChecked():
            self.fileHandler = open('opd_data_filter.txt','w')
            self.flagRecording = True
            print('recording started!')
        else:
            self.flagRecording = False
            self.fileHandler.close()
            print('recording finished!')

    def tactileUpdate(self):
        self.lock.acquire()
        n = len(self.tactileHandler.dataQueue)
        # print(n)
        for k in range(n):
            data = self.tactileHandler.dataQueue.popleft()
            strdata = ''
            aux_idx = 0
            for i in range(0,TBCONSTS.NUMDATABYTES,2):
                aux_tactile_data = data[i]<<8|data[i+1]
                aux_tactile_data = aux_tactile_data * TBCONSTS.LSBV
                if self.flagRecording is True:
                    self.fileHandler.write(str(aux_tactile_data) + ' ')

                if k == n-1:

                    self.taxelMat[aux_idx].append(aux_tactile_data)
                    self.taxelCurves[aux_idx].setData(self.timev,self.taxelMat[aux_idx])
                    aux_idx += 1

            if self.flagRecording is True:
                self.fileHandler.write('\n')

            if k == n-1:
                self.timev.append(self.timestep)
                self.timestep += (self.dt*n)
                if self.timestep >= self.maxTime:
                    self.timev = [0]
                    self.taxelMat = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
                    self.timestep = 0
                # print(aux_tactile_data)
            # print(strdata)
            #update curve
            #self.taxelCurve.setData(self.timev,self.taxelv)

        self.lock.release()
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormTactile()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
