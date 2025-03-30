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
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#EXAMPLE AND VALIDATION
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    def run():
        global s, l
        l.acquire()
        q = copy(s.dataQueue)
        s.dataQueue.clear()
        l.release()
        n = len(q)
        # print(n)
        if n > 0:
            print(n)
        time.sleep(1)

    p = '/dev/ttyACM0'
    l = Lock()
    s = SerialHandler(p,_numDataBytes=10,_thLock=l)
    s.open()
    thAcq = ThreadHandler(s.readPackage)
    th = ThreadHandler(run)
    thAcq.start()
    th.start()
    a = input()
    s.serialPort.write('START'.encode())
    a = input() #press ENTER to stop running
#-------------------------------------------------------------------------------
