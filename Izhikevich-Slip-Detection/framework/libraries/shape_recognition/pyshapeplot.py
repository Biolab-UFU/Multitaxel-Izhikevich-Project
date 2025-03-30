import socket
import threading
import SocketServer
from mutex import mutex
from collections import deque
from threading import Lock
from threadhandler import ThreadHandler
import matplotlib.pyplot as plt
import numpy as np
import time
from template_matcher import find_class_orient_position
from scipy.io import loadmat
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

N_ROWS = 64
N_COLS = 64
sensor = np.ones((N_ROWS,N_COLS)) * 0.5

#SET THE APP AND MAIN WINDOW  (GUI)
pg.setConfigOptions(imageAxisOrder='row-major')
pg.setConfigOptions(antialias=True)
app = QtGui.QApplication([])
app.aboutToQuit.connect(app.deleteLater)

win = pg.GraphicsWindow(size=(1000,800), border=True)
win.setWindowTitle('Tactile Array')

text="Sensor Output"
sensor_view = win.addLayout(row=0, col=0)
label = sensor_view.addLabel(text,row=0,col=0)
label.setText(text,size='22pt')

sensor_box = sensor_view.addViewBox(row=1, col=0, lockAspect=True)
sensor_image = pg.ImageItem( np.zeros((N_ROWS,N_COLS)) )
sensor_box.addItem(sensor_image)
sensor_box.setLimits(xMin=0,xMax=N_ROWS,yMin=0,yMax=N_COLS)
sensor_box.setRange(xRange=[0,N_ROWS],yRange=[0,N_COLS])
sensor_image.setImage(sensor,levels=(0,1))

#adding a save button
proxy1 = QtGui.QGraphicsProxyWidget()
btnSave = QtGui.QPushButton('Save')
proxy1.setWidget(btnSave)
win.addItem(proxy1,row=3,col=1)
imgSpikes = np.zeros((64,64))
def doSave():
    global filename, imgSpikes
    np.savetxt(filename,imgSpikes,fmt='%.2f')

btnSave.clicked.connect(doSave)


# create the figure
#fig = plt.figure()
#ax = fig.add_subplot(111)
#im = ax.imshow(np.random.random((64,64)))
#plt.show(block=False)
m = Lock()
q = deque()
spikeQueue = deque()
spikeCounter = 0
filename = 'output.txt'
fileHandler = open(filename,'w')
#loading the templates
matl =  loadmat('templates_morph.mat')
templates =  matl['mat_arr']
orientations =  matl['orientation_arr']
objects = matl['object_ar']
print 't', templates.dtype
print orientations
print objects.shape
#
obj1 = templates[:,:,1]
obj1_f = obj1.flatten()

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        global m,q
        data = self.request.recv(2000)
        #data = bytearray(data)        
        cur_thread = threading.current_thread()
        #response = "{}: {}".format(cur_thread.name, data)
        m.acquire()
        q.append(data)
        #q.append((data[0]<<8 | data[1]))
        m.release()
        #print data
        #print (data[0]<<8 | data[1])
        #print data
        #self.request.sendall(response)

def updateFile():
    global m,q, filename
    f = open(filename,'a')
    m.acquire()
    n = len(q)
    for k in range(n):
        sample = q.popleft() #queue
        f.write(sample + '\n')
        #spike queue
        data = map(float,sample.split(' '))
        #print data

spikeCounter = 0
numSpikes = 500
spikeArray = np.zeros((numSpikes,3))
spikeArray = spikeArray.astype(int)
from copy import copy
def update():
    global spikeCounter, spikeQueue, counter, q, thLock, sensor, sensor_image, templates, orientations, objects, sensor
    m.acquire()
    dataQueue = copy(q)
    q.clear()
    m.release()

    n = len(dataQueue)
    for w in range(n):
        d = dataQueue.popleft().split('\n') #dataQueue
        for k in range(len(d)-1):
            correctedData = map(int,d[k].split(' '))
            spikeArray[spikeCounter,:] = correctedData[0:3]
            spikeCounter += 1
            if spikeCounter >= numSpikes:
                #recognition time
                spikeCounter = 0
                print 'recog time!'
                objectNames,location,orientation,imgSpikes = find_class_orient_position(spikeArray[:,1],spikeArray[:,2],spikeArray[:,0], templates, orientations, objects, 1)
                print objectNames
                print location
                print orientation
                print imgSpikes.shape
                sensor_image.setImage(imgSpikes,levels=(0,1))
                QtGui.QApplication.processEvents()

            #print correctedData
        #sensorData = map(float,dataQueue.pop().split(' '))
        #sensor[sensorData[0],sensorData[1]] = sensorData[2]
        #print sensorData
    
if __name__ == "__main__":    
    # Port 0 means to select an arbitrary unused port
    
    HOST, PORT = "127.0.0.1", 8888

    server = SocketServer.TCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name

    #client(ip, port, "Hello World 1")
    #client(ip, port, "Hello World 2")
    #client(ip, port, "Hello World 3")

    fileThread = ThreadHandler(update)
    fileThread.start()

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

    x = raw_input('type any key to finish....\n')

    fileThread.kill()

    server.shutdown()
    server.server_close()
    fileHandler.close()