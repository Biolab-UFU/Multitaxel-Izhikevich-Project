# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
# Author: Andrei Nakagawa-Silva, MSc
# Contact: nakagawa.andrei@gmail.com
#-------------------------------------------------------------------------------
# Description: GUI for the demo: Pick and Place with HD Neuromorphic Array
#-------------------------------------------------------------------------------
# Update 26/05:
*   - Including slip controller: When the object is grasped, slip controller
#   gets activated to prevent bad grasps
#-------------------------------------------------------------------------------
# Hints: To add an image to the GUI designed in QtDesigner, follow the steps:
#   1) Create a QGraphisView in the designer
#   2) Promote the QGraphisView to a GraphisLayoutWidget, header = pyqtgraph in
#      the QtDesigner
#   3) Add a viewBox to the created GraphicsView
#   4) Create an ImageItem object with the array to be displayed as image
#   5) Use the 'addItem' to add the image to the ViewBox
#   5) Use the 'setImage' method of the ImageItem object to update the image
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
import os, sys, glob
sys.path.append('../framework/libraries/general')
sys.path.append('../framework/libraries/HDArray')
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
import numpy as np
import pyqtgraph as pg
from scipy.io import loadmat
import serial #serial handler
from collections import deque #necessary for acquisition
from copy import copy #useful for copying data structures
from threading import Thread, Lock #control access in threads
from threadhandler import ThreadHandler #manage threads
from hdnerarray import HDNerArray #Socket communication with the HD Neuromorphic tactile array
from dataprocessing import *
from serialhandler import SerialHandler #serial handler to read the slip sensor
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formHDArray_gui.ui')
## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#-----------------------------------------------------------------------------
class FormHDArray(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(FormHDArray,self).__init__()
        self.setupUi(self)
        #determines number of rows and columns
        #HD array
        self.NROWS = 64 #lines
        self.NCOLS = 64 #columns
        #lock to control access to threads
        self.dataLock = Lock()
        #data queue
        self.dataQueue = deque()
        #object for handling socket communication with the HD array
        #self.hdarrayip = '172.23.38.148' #localhost through wi-fi
        self.hdarrayip = '127.0.0.1' #localhost
        self.hdarrayport = 8888 #can be other values
        #create the object
        self.hdarray = HDNerArray(self.hdarrayip,self.hdarrayport)
        #-----------------------------------------------------------------------
        #timer to update the GUI
        self.timer = QTimer()
        #connect the timer to its function
        self.timer.timeout.connect(self.update)
        #set the interva
        self.itv = 50 #ms
        self.timer.setInterval(self.itv)
        #file controller
        self.fileHandler = None
        #file
        self.filename = 'newsquare4.txt'

        #debugging
        #print('t', self.templates.dtype)
        #print(self.orientations)
        #print(self.objects.shape)
        #initialize the GUI
        self.init()

    #initalize the GUI
    def init(self):
        #initialize the plots
        #create a viewbox to the neuromorphic array
        #pltArray is the GraphisView object promoted to GraphisLayoutWidget
        #in QtDesigner
        self.pltArray.ci.layout.setContentsMargins(0,0,0,0)
        self.pltArray.ci.layout.setSpacing(0)
        self.vbNerArray = self.pltArray.addViewBox()
        #create the image of the neuromorphic array
        self.nerArrayImg = pg.ImageItem(np.zeros((self.NROWS,self.NCOLS)))
        #add the image to the component
        self.vbNerArray.addItem(self.nerArrayImg)
        #events from the buttons
        #starts recording
        self.btnStart.clicked.connect(self.doStart)
        #stops recording
        self.btnStop.clicked.connect(self.doStop)
        #flags
        self.flagRecording = False #signals ongoing data recording

    #start reading from the neuromorphic HD tactile array
    def doStart(self):
        self.timer.start() #start the timer to update the GUI
        self.hdarray.start() #start the acquisition of data from the HD array
        #self.thAcq.start() #start the thread for reading data from the HD array
        self.filename = self.tbFile.text()
        print(self.filename)
        self.fileHandler = open(self.filename,'w')
        #update the status
        self.lbStatus.addItems(['File: ' + self.filename])
        self.lbStatus.addItems(['Server started!\nAcquisition running!'])
        self.flagRecording = True
        self.tbFile.setDisabled(True)

    def doStop(self):
        self.timer.stop()
        #update the status
        self.lbStatus.addItems(['Acquisition stopped!'])
        #close the file
        if self.fileHandler is not None:
            self.fileHandler.close()
        self.flagRecording = False
        self.tbFile.setDisabled(False)
        #self.thAcq.kill()

    #updates the GUI
    def update(self):
        #gets data from the HD tactile array
        q = self.hdarray.getData()
        #debugging
        #if q is not False:
        #    print("len",len(q))
        #create a new empty matrix
        ar = np.ones((self.NROWS,self.NCOLS))*0.5
        #if there is data to be read
        if q is not False:
            n = len(q) #find the number of samples
            for k in range(n):
                data = q.popleft() #take an element from the queue

                #saving data to a text file
                if self.fileHandler is not None:
                   [self.fileHandler.write(str(x)+' ') for x in data]
                   self.fileHandler.write('\n')

                ar[data[1],data[2]] = data[3] #assign the polarity to the specified X and Y coordinates
                #assign the spike event to the spike array for shape recognition
                self.spikeArray[self.spikeCounter,:] = data[0:3] #pass time, x and y
                self.spikeCounter += 1 #increment the spike counter
                #if the number of spikes have been reached, call the shape recognition function
                if self.spikeCounter >= self.numSpikesRecog:
                    #call the function to do template matching -> shape recognition
                    # self.objName,self.objLocation,self.objOrientation,imgSpikes,self.match_val = find_class_orient_position(self.spikeArray[:,1],self.spikeArray[:,2],self.spikeArray[:,0], self.templates, self.orientations, self.objects, 1)
                    self.spikeCounter = 0

            self.nerArrayImg.setImage(ar,levels=(0,1)) #draw the spikes in the GUI
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormHDArray()
    main.show()
    sys.exit(app.exec_())
