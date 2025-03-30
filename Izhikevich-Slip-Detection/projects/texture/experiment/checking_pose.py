import sys
sys.path.append('../../../framework/libraries/UR10')
import numpy as np
from UR10 import *
import time
from copy import copy

x = UR10Controller('10.1.1.6')
y = URPoseManager()
y.load('texture_new.urpose')

y.moveUR(x,'gobackJ',2)
time.sleep(2)

y.moveUR(x,'homeJ',2)
time.sleep(2)

y.moveUR(x,'objectJ',2)
time.sleep(2)

x.read_joints_and_xyzR()
j = copy(x.xyzR)
print(j)
j[2] += 100

x.movej(j,5)
time.sleep(5)

y.moveUR(x,'gobackJ',2)
time.sleep(2)
