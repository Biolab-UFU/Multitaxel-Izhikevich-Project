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
# Description: This file contains a class for handling serial communication
# with embedded systems such as Arduino boards or ARM dev kits
#-------------------------------------------------------------------------------
# [HEADER][NBYTES][ADC0_MSB][ADC0_LSB][ADC1_MSB][ADC1_LSB][END]
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
import sys
sys.path.append('../general')
from collections import deque
from threading import Lock
from copy import copy
import time
from threadhandler import ThreadHandler
from serialhandler import SerialHandler
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class SBCONSTS():
    NBYTES = 10

class SlipBoard():
    def __init__(self,portname):
        #create an internal object to handle serial communication
        self.serialHandler = SerialHandler(portname, _baud=115200, _numDataBytes=SBCONSTS.NBYTES)
        #data queue
        self.dataQueue = deque()
        #thread for reading data
        self.threadAcq = ThreadHandler(self.read)
        #lock for protecting access
        self.lock = Lock()
        #open the serial communication
        self.serialHandler.open()
        self.tstart = None
        self.tend = None
        self.counter = 0
        self.flagDebug = False

    #start acquisition
    def start(self):
        self.threadAcq.start()
        self.serialHandler.serialPort.write('START'.encode())
        self.tstart = time.time()

    def readDistance(self):
        self.serialHandler.serialPort.write('DIST'.encode())

    #stop acquisition
    def stop(self):
        self.serialHandler.serialPort.write('STOP'.encode())
        time.sleep(1)
        self.threadAcq.kill()

    #read one package from serial, arrange and add to data queue
    def read(self):
        #read one package from serial
        self.serialHandler.readPackage()

        if self.flagDebug:
            self.counter += 1
            if self.counter >= 10:
                self.tend = time.time()
                tt = self.tend - self.tstart
                print(tt)
                self.tstart = time.time()
                self.counter = 0
        #get the data
        if len(self.serialHandler.dataQueue) > 0:
            d = self.serialHandler.dataQueue.popleft()
            #arrange the data
            data = [] #aux variable
            for i in range(0,SBCONSTS.NBYTES,2):
                #accelerometer outputs are signed values
                if i < 6:
                    data.append(self.serialHandler.to_int16(d[i],d[i+1]))
                else: #distance and optic sensors outputs are integers
                    data.append(self.serialHandler.to_int16(d[i],d[i+1]))
            #convert the output of the optic sensor to Volts
            data[-1] = ((data[-1]+1)*5.0)/1024.0
            #lock access
            self.lock.acquire()
            #insert data to queue
            self.dataQueue.append(data)
            #release access
            self.lock.release()
        #required?
        # time.sleep(0.001)

    def getData(self):
        q = None
        self.lock.acquire()
        q = copy(self.dataQueue)
        self.dataQueue.clear()
        self.lock.release()
        return q
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#EXAMPLE AND VALIDATION
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    def run():
        global s, tstart, tend, counter
        q = s.getData()
        if q is not None:
            n = len(q)
            # print(n)
            for k in range(n):
                #get a sample
                d = q.popleft()
                # print(d)
                # counter += 1
                # if counter >= 100:
                #     tend = time.time()
                #     print(tend - tstart)
                #     counter = 0
                #     tstart = time.time()
        time.sleep(0.001)

    p = '/dev/ttyACM0'
    tend = 0
    counter = 0
    s = SlipBoard(p)
    s.flagDebug = True
    th = ThreadHandler(run)
    tstart = time.time()
    th.start()
    s.start()
    a = input() #press ENTER to stop running
#-------------------------------------------------------------------------------
