import sys
sys.path.append('../../framework/libraries/general')
import numpy as np
import time
from serialhandler import *
from threading import Lock
from threadhandler import ThreadHandler

l = Lock()
s = SerialHandler(_numDataBytes = 10, _thLock = l)
f = open('sensors_data.txt','w')

def run():
    global s,l,f
    l.acquire()
    n = len(s.dataQueue)
    for k in range(n):
        data = s.dataQueue.popleft()
        strdata = ''
        for i in range(0,10,2):
            if i < 6:
                strdata += str(s.to_int16(data[i],data[i+1])) + ' '
            else:
                strdata += str(data[i]<<8|data[i+1]) + ' '
        print(strdata)
        f.write(strdata + '\n')
    l.release()
    time.sleep(0.0001)

s.open()
time.sleep(1)
print('ready')
# print(s.serialPort.in_waiting)
# s.serialPort.read(s.serialPort.in_waiting)
t = ThreadHandler(s.readPackage)
t.start()
p = ThreadHandler(run)
p.start()
# a = input()
# flagRec = True
# t0 = datetime.datetime.now()
# time.sleep(2)
# t1 = datetime.datetime.now()
# flagRec = False
# print('total samples:', counter, t1-t0, numsamples)
a = input()
t.kill()
p.kill()
s.close()
f.close()
