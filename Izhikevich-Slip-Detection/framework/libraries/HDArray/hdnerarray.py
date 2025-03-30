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
# Description: Class for handling socket communication with the HD Neuromorphic
# Array. The original software was written in C#. Therefore, we are using sockets
# to read the array from C# and then sending the data via sockets to a Python
# server where shape recognition is implemented.
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
import os, sys, glob
sys.path.append('../general')
import numpy as np
import pyqtgraph as pg
from collections import deque #necessary for acquisition
from copy import copy #useful for copying data structures
from threading import Lock #control access in threads
from threadhandler import ThreadHandler #manage threads
from sockethandler import * #import socket communication handlers
#-------------------------------------------------------------------------------
class HDNerArray():
    def __init__(self,_ip='127.0.0.1',_port=8888):
        self.ip = _ip #ip of host
        self.port = _port #port number
        self.server = None
        self.NROWS = 64
        self.NCOLS = 64
    #start the server
    def start(self):
        self.server = SocketServerHandler(self.ip,self.port)
    #retrieve the data queue, process the incoming data
    #and convert it to a queue containing spiking events
    #with the following structure
    #[SPIKE_TIME][POS_X][POS_Y][SPIKE_POLARITY]
    def getData(self):
        if self.server is not None:
            q = self.server.getDataQueue()
            self.dataQueue = deque()
            numData = len(q)
            if numData > 0:
                for k in range(numData):
                    #retrieve the spike events contained in the data queue
                    #the join function concatenates to a list the
                    #byte values converted to chr, forming a string
                    #that is being split by new lines (\n)
                    spikeEvents = "".join(map(chr,q.popleft())).split('\n')
                    #for every event, do a post-processing in the data
                    for z in range(len(spikeEvents)-1):
                        correctedData = []
                        #convert the data to int
                        [correctedData.append(int(x)) for x in spikeEvents[z].split(' ')]
                        #add to the class queue
                        self.dataQueue.append(correctedData)
                        #debugging
                        #print(correctedData) #print the read values
                return copy(self.dataQueue) #return a copy of the queued spike event
            else:
                return False
#-------------------------------------------------------------------------------
#Run the appo
if __name__ == '__main__':
    #create an object
    hdarray = HDNerArray()
    def read():
        global hdarray
        z = hdarray.getData()
        n = len(z)
        for k in range(n):
            print(z.popleft())
    #thread to read
    th = ThreadHandler(read)
    #waits for input to start
    input('press ENTER to start...')
    hdarray.start()
    th.start()
    #wait for input to finish
    input('press ENTER to finish...')
    th.kill()
