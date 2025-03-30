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
#Paths
import os, sys, glob
sys.path.append('../framework/libraries/general')
sys.path.append('../framework/libraries/iLimb')
sys.path.append('../framework/libraries/UR10')
sys.path.append('../framework/libraries/HDArray')
sys.path.append('../framework/libraries/shape_recognition')
sys.path.append('../framework/libraries/neuromorphic')
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
#from UR10 import * #UR10 controller
#from iLimb import * #iLimb controller
#from hdnerarray import HDNerArray #Socket communication with the HD Neuromorphic tactile array
#from template_matcher import find_class_orient_position #shape recognition
from tactileboard import * #4x4 tactile board
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formTactileBoard_gui.ui')
#-------------------------------------------------------------------------------
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-------------------------------------------------------------------------------
#controller for the GUI
class GUIController(QObject):
    calibFinished = pyqtSignal() #triggers an event when calibration is finished
    def __init__(self,flagSpike=False,_comport='COM3'):
        super(GUIController, self).__init__()
        self.tactileBoard = TactileBoard(_comport) #create a new object of the tactile board
        self.dataQueue = deque() #data queue
        self.calibTimer = QTimer() #timer for checking the status of the calibration procedure
        self.calibTimer.timeout.connect(self.checkCalibration) #connect timer to the method
    #initializes data acquisition
    def init(self):
        self.tactileBoard.start()
        self.tactileBoard.swMaxSamples = 2000
        self.tactileBoard.swT0 = datetime.datetime.now()
        self.tactileBoard.swFlag = True
    #-------------------------------------------------------------------------------------
    def setPort(self,port):
        self.tactileBoard = TactileBoard(port)
    #-------------------------------------------------------------------------------------
    def changeSensitivity(self,sens):
        if sens == 1:
            self.tactileBoard.sensitivity = TBCONSTS.HIGH_SENS
        elif sens == 2:
            self.tactileBoard.sensitivity = TBCONSTS.MEDIUM_SENS
        elif sens == 3:
            self.tactileBoard.sensitivity = TBCONSTS.LOW_SENS
        elif sens == 0:
            self.tactileBoard.sensitivity = TBCONSTS.DEFAULT_SENS
    #-------------------------------------------------------------------------------------
    #read tactile sensors
    def getTactile(self):
        q = self.tactileBoard.getData()
        return q
    #---------------------------------------------------------------------------
    def useCalibration(self,flag):
        if flag == True:
            if(self.tactileBoard.loadCalibration()):
                self.tactileBoard.useCalib = True
                return True
            else:
                self.tactileBoard.useCalib = False
                return False
        else:
            self.tactileBoard.useCalib = False
            return True
    #---------------------------------------------------------------------------
    def runCalibration(self):
        numsamples = TBCONSTS.SAMPFREQ*2 #determines the maximum number of samples for calibration
        self.tactileBoard.startCalibration(numsamples)
        #starts the calibration procedure
        self.calibTimer.start()
    #---------------------------------------------------------------------------
    def checkCalibration(self):
        #checks if calibration has finished
        if self.tactileBoard.calibStatus == TBCONSTS.CALIBRATION_FINISHED:
            self.calibFinished.emit() #emit the signal for the GUI to handle
            #resets the status of calibration back to IDLE
            self.tactileBoard.calibStatus = TBCONSTS.CALIBRATION_IDLE
    #---------------------------------------------------------------------------
    def convert2raw(self,value,patch,col,row):
        return self.tactileBoard.conv2raw(value,patch,col,row)
    #---------------------------------------------------------------------------
    def startRecording(self,filename):
        self.tactileBoard.startRecording(filename)
    def stopRecording(self):
        self.tactileBoard.stopRecording()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#parent: the parent window which will hold objects to every controller
class FormTactileBoard(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(FormTactileBoard,self).__init__()
        self.setupUi(self)

        #gui controller
        self.guiController = GUIController(self)
        self.flagRecording = False

        #curve
        self.patchIdx = 0
        self.timev = [0]
        self.timestep = 0
        self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
        self.dt = 1.0 / TBCONSTS.SAMPFREQ #sampling time
        self.maxTime = 10 #10 seconds window

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
        self.cbSerialPort.addItems(res)
        #combo box for tactile patches
        self.cbTactilePatch.addItems(['1','2','3','4','5'])
        self.cbTactilePatch.currentIndexChanged.connect(self.doChangeTactilePatch)

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
        self.pltTactile = [self.pltTS0,self.pltTS1,self.pltTS2,self.pltTS3,self.pltTS4]

        #remove borders
        [x.ci.layout.setContentsMargins(0,0,0,0) for x in self.pltTactile]
        [x.ci.layout.setSpacing(0) for x in self.pltTactile]

        #right hand tactile sensors
        self.vbTactile = []
        [self.vbTactile.append(x.addViewBox()) for x in self.pltTactile]
        self.tactileImg = []
        for k in range(self.guiController.tactileBoard.NPATCH):
            self.tactileImg.append(pg.ImageItem(np.zeros((TBCONSTS.NROWS,TBCONSTS.NCOLS))))
        for k in range(self.guiController.tactileBoard.NPATCH):
            self.vbTactile[k].addItem(self.tactileImg[k])

        #radio button events
        #right hand
        self.rbHigh.toggled.connect(self.sensChanged)
        self.rbMedium.toggled.connect(self.sensChanged)
        self.rbLow.toggled.connect(self.sensChanged)
        self.rbDefault.toggled.connect(self.sensChanged)

        #events from the buttons
        self.btnStart.clicked.connect(self.doStart)
        self.btnStop.clicked.connect(self.doStop)
        self.btnConnect.clicked.connect(self.doConnect)
        self.btnCalibration.clicked.connect(self.doCalibration)

        #event from the checkbox that determines whether calibration should
        #be employed
        self.chCalibration.toggled.connect(self.doUseCalibration)
        #recording option --> will save data to a file
        self.chRecording.toggled.connect(self.doRecording)

        #events from the GUI controller
        self.guiController.calibFinished.connect(self.doCalibFinished)

        #stopwatch
        self.timestart = None
        self.timestop = None
        self.flagCounter = 0
        self.sampleCounter = 0

        #frame counter
        self.frameCounter = 0

    def doChangeTactilePatch(self,i):
        self.patchIdx = i
        #print(i)

    # def doRecording(self):
    #     if self.sender().isChecked():
    #         self.flagRecording = True
    #         self.fileHandler = open('tactiledata.txt','w')
    #     else:
    #         print('stop recording')
    #         self.flagRecording = False
    #         self.fileHandler.close()

    def doRecording(self):
        if self.sender().isChecked():
            self.guiController.startRecording('tactiledata.txt')
            print('recording started!')
        else:
            self.guiController.stopRecording()
            print('recording finished!')

    #perform the calibration of the tactile sensors
    def doCalibration(self):
        self.guiController.runCalibration()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Calibration undergoing")
        msg.setInformativeText("Please, do not touch the sensors during calibration")
        msg.setWindowTitle("Calibration")
        msg.exec_()

    #shows a message when calibration has finished
    def doCalibFinished(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Calibration finished!")
        msg.setWindowTitle("Calibration")
        msg.exec_()

    def doUseCalibration(self):
        if self.sender().isChecked():
            ret = self.guiController.useCalibration(True)
        else:
            ret = self.guiController.useCalibration(False)

        if ret is False:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Calibration File Not found!")
            msg.setWindowTitle("Error")
            msg.exec_()
            self.sender().setChecked(False)

    def sensChanged(self):
        rb = self.sender()
        if rb == self.rbHigh:
            self.guiController.changeSensitivity(1)
        elif rb == self.rbMedium:
            self.guiController.changeSensitivity(2)
        elif rb == self.rbLow:
            self.guiController.changeSensitivity(3)
        elif rb == self.rbDefault:
            self.guiController.changeSensitivity(0)

    #connect
    def doConnect(self):
        self.guiController.setPort(self.cbSerialPort.currentText())

    #create the controller
    def doStart(self):
        self.guiController.init()
        self.tactileTimer.start()
        self.timestart = datetime.datetime.now()
        self.flagCounter = 1

    def doStop(self):
        self.tactileTimer.stop()

    def tactileUpdate(self):
        q = self.guiController.getTactile()

        #plot right hand tactile sensors
        n = len(q)
        for k in range(n):
            tactileSample = q.popleft()

            #------------------------------------------------------------------------
            #------------------------------------------------------------------------
            #debugging sampling rate and stuff
            # if self.flagCounter == 1:
            #     self.sampleCounter += 1
            #     if self.sampleCounter >= 2400*2:
            #         self.timestop = datetime.datetime.now()
            #         # print('finished',self.sampleCounter,n,k,self.timestart,self.timestop,self.timestop-self.timestart)
            #         self.flagCounter = 0
            #------------------------------------------------------------------------
            #------------------------------------------------------------------------

            if k == n-1:
                for z in range(TBCONSTS.NPATCH):
                    auxcounter = 0
                    for i in range(TBCONSTS.NROWS):
                        for j in range(TBCONSTS.NCOLS):
                            if self.rbGray.isChecked():
                                self.tactileRGB[z][i][j] = self.conv2grayscale(tactileSample[z][i][j])
                            elif self.rbColor.isChecked():
                                self.tactileRGB[z][i][j] = self.conv2color(tactileSample[z][i][j])
                            elif self.rbHeat.isChecked():
                                self.tactileRGB[z][i][j] = self.conv2yellowred(tactileSample[z][i][j])

                            #plot
                            if z == self.patchIdx:
                                self.taxelv[auxcounter].append(tactileSample[z][i][j])
                                self.taxelCurves[auxcounter].setData(self.timev,self.taxelv[auxcounter])
                                auxcounter += 1

                            #if recording, save taxel value to file
                            #each line is one frame
                            #80 taxels in sequence
                            if self.flagRecording:
                                rawValue = self.guiController.convert2raw(tactileSample[z][i][j],z,i,j)
                                # print(rawValue) #debugging
                                # self.fileHandler.write(str(rawValue) + ' ') #writing to file

                    #print(self.tactileRGB[z]) #debugging
                    self.tactileImg[z].setImage(self.tactileRGB[z],levels=(0,255))

                #update curve
                #self.taxelCurve.setData(self.timev,self.taxelv)
                self.timev.append(self.timestep)
                self.timestep += (self.dt*n)
                if self.timestep >= self.maxTime:
                    self.timev = [0]
                    self.taxelv = [[] for x in range(TBCONSTS.NROWS*TBCONSTS.NCOLS)]
                    self.timestep = 0

            #skips next line --> next frame
            if self.flagRecording:
                self.fileHandler.write('\n')

    def conv2grayscale(self,adcValue):
        #convert the raw value to 8 bits
        correctedVal = min(255,adcValue*256)
        return [int(correctedVal)]*3

    def conv2yellowred(self,vnorm):
        a = 1-vnorm
        y=np.floor(255*a)
        r=255; g=y; b=0;
        return [int(r),int(g),int(b)]

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

    #convert 12 bit values to RGB mapping
    #linear regression for each of the RGB values with different
    #ranges (min and max values)
    def conv2colormap(self,adcValue):

        #convert the raw value to 8 bits
        correctedVal = min(255,adcValue*256)

        #from the corrected value, return RGB
        #RED
        if correctedVal <= 32*4:
            red = 0
        elif correctedVal > 32*4 and correctedVal < 32*6:
            red = ((correctedVal-(32*4))*(255))/((32*6)-(32*4))
        else:
            red = 255

        #BLUE
        if correctedVal >= 32*4:
            blue = 0
        elif correctedVal > (32*2) and correctedVal < 32*4:
            blue = ((correctedVal-(32*2))*(-255))/(32*4-(32*2)) + 255
        else:
            blue = 255

        #GREEN
        if correctedVal >= 0 and correctedVal < (32*2):
            green = ((correctedVal)*(255))/((32*2))
        elif correctedVal >= (32*2) and correctedVal <= (32*6):
            green = 255
        else:
            green = ((correctedVal-(32*6))*(-255))/(255-(32*6)) + 255

        #convert all values to integers
        red = int(red)
        green = int(green)
        blue = int(blue)

        #print(correctedVal,red,green,blue) #debugging
        return [red,green,blue]

    def conv2heatmap(self,adcValue):

        #convert the raw value to 8 bits
        correctedVal = min(255,adcValue*256)

        #from the corrected value, return RGB
        if correctedVal <= 160:
            red = 255
        else:
            red = ((correctedVal-(160))*(-255))/(255-160) + 255

        if correctedVal >= 96:
            blue = 0
        elif correctedVal > 32 and correctedVal < 96:
            blue = ((correctedVal-(32))*(-204))/(96-32)+ 204
        else:
            blue = 204

        if correctedVal <= 128:
            green = 255
        else:
            green = max(0,((correctedVal-(128))*(-255))/(192-128)+ 255)

        red = int(red)
        green = int(green)
        blue = int(blue)

        #print(correctedVal,red,green,blue) #debugging
        return [red,green,blue]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormTactileBoard()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
