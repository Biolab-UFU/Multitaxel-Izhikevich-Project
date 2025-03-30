from serialhandler import *
from threadhandler import *
from threading import Thread, Lock
from copy import copy

thLock = Lock()

def update():
    global serialHandler, thLock
    thLock.acquire()
    n = len(serialHandler.dataQueue)
    q = copy(serialHandler.dataQueue)
    serialHandler.dataQueue.clear()
    thLock.release()
    for k in range(n):
        data = q.popleft()
        print(data)
    time.sleep(0.01)

serialHandler = SerialHandler(_port='/dev/ttyACM0',_baud=115200,_timeout=0.5,_header=0x24,_end=0x21,_numDataBytes=160,_thLock=None)
thAcq = ThreadHandler(serialHandler.readPackage)
thProc = ThreadHandler(update)
thAcq.start()
thProc.start()
a = input()
