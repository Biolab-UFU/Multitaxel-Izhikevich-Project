#python basic script

#importing UR10 library
from UR10 import *
#important libraries
import numpy as np
from copy import copy
import time

#create an object
ip = '10.1.1.6' #ip address of the UR10 --> 10.1.1.4: left | 10.1.1.6 --> right
ur10cont = UR10Controller(ip) #object for controlling the UR10

#read current joints and xyzR
#remember that the UR10 tablet has to be in 'base' mode
ur10cont.read_joints_and_xyzR() #this function reads the current joints and position (xyzR)

#after reading, if you want to use the xyzR
#xyzR: position in X, Y and Z in mm and orientation Rx, Ry and Rz
xyzR = copy(ur10cont.xyzR) #copy is essential

#after reading, if you want to use the joints
#joints are: base, shoulder, elbow, wrist1, wrist2 and wrist3 IN DEGREES
joints = copy(ur10cont.joints) #copy is essential
# print(joints)
# a=input()

#moving the UR10 --> REMEMBER: Speed should be 100%
#USING MOVEJ --> The UR10 moves to a position specified by X, Y and Z with
#the orientation specified by Rx, Ry and Rz
#moving up
#indexing starts with 0
xyzR[0] += 100 #move to the left
xyzR[2] += 100 #move up  by 10 cm
#moving
timetomove = 5 #seconds
ur10cont.movej(xyzR,timetomove) #move to xyzR within the specified time
time.sleep(timetomove) #wait for move to be completed
a=input()
#moving the UR10 --> REMEMBER: Speed should be 100%
#USING MOVEJOINT --> Every joint will rotate by the specified amount. The notion
#of endpoint positions and orientations are not explicit
#rotating the last joint
joints[5] += 90 #rotating by 90 degrees
#moving
timetomove = 10 #seconds
#ALWAYS REMEMBER TO CONVERT TO RADIANS THE `joints` vector
ur10cont.movejoint(np.deg2rad(joints),timetomove) #move to xyzR within the specified time
time.sleep(timetomove) #wait for move to be completed
# a=input()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#UR10 Pose Manager
ur10pose = URPoseManager() #create an object
#load a file
ur10pose.load('example.urpose') #loads a file containing positions and joints previously saved
#move to a saved position or joint configuration
timetomove = 10 #seconds
ur10pose.moveUR(ur10cont, 'homej', timetomove)
time.sleep(timetomove)
#retrieve the position values or joint configurations from file
posJoint = ur10pose.getPosJoint('homej')
