#------------------------------------------------------------------------------------------------------s
import os, sys, glob
sys.path.append('../framework/libraries/general')
sys.path.append('../framework/libraries/iLimb')
sys.path.append('../framework/libraries/UR10')
sys.path.append('../framework/libraries/HDArray')
sys.path.append('../framework/libraries/shape_recognition')
sys.path.append('../framework/libraries/neuromorphic')
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
from template_matcher import find_class_orient_position #shape recognition
from UR10 import * #UR10 controller
from iLimb import * #iLimb controller
from ur10_simulation import ur10_simulator #UR10 simulator
from dataprocessing import *
from serialhandler import SerialHandler #serial handler to read the slip sensor
from tactileboard import * #handles communication with the tactile board
#------------------------------------------------------------------------------------------------------
def pivot_move(dist_pivot,delta_joints,t,orient,dist,Yoffset,ur10cont):
        Sim = ur10_simulator()
        ur10cont.read_joints()
        print(ur10cont.joints)
        Sim.set_joints(ur10cont.joints)
        ur10cont.xyzR = Sim.joints2pose()
        new_joints = copy(ur10cont.joints)
        new_joints = new_joints + delta_joints
        new_xyzR = ur10cont.move_joint_with_constraints(new_joints,dist_pivot)
        aux = copy(new_xyzR)
        aux[1] += (dist*np.cos(np.deg2rad(-orient)) - Yoffset*np.sin(np.deg2rad(-orient)))
        aux[0] += -(dist*np.sin(np.deg2rad(-orient)) + Yoffset*np.cos(np.deg2rad(-orient)))
        ur10cont.movej(aux,t)
        # self.UR10Cont.movej(new_xyzR,t)
        time.sleep(t+0.2)
        return new_xyzR
#------------------------------------------------------------------------------------------------------
def ur_home(ur10cont,ur10pose):
	xyzR = ur10pose.getPosJoint('homep')
	xyzR[0] += 100
	ur10cont.movej(xyzR,6)
	time.sleep(6)
#------------------------------------------------------------------------------------------------------
def ur_pick(ur10cont):
	ur10cont.do_circular_pivot_motion(-20, 180,"z",2,30)
	ur10cont.read_joints_and_xyzR()
	jointsv = copy(ur10cont.joints)
	print('joints',jointsv)
	new_jointsv = copy(jointsv)
	new_jointsv[-1] -= 13
	print('new_joints',new_jointsv)
	new_jointsv = np.deg2rad(new_jointsv)
	ur10cont.movejoint(new_jointsv,2)
	time.sleep(2)
	ur10cont.read_joints_and_xyzR()
	xyzR = copy(ur10cont.xyzR)
	xyzR[2] -= 130
	ur10cont.movej(xyzR,2)
	time.sleep(2)
#------------------------------------------------------------------------------------------------------
def ur_rotate(ur10cont,angle):
	orient = angle
	Xoffset = 10
	Yoffset = -20
	new_xyzR = pivot_move(180,[0,0,0,0,orient,0],4,orient,Yoffset,Xoffset,ur10cont)
#------------------------------------------------------------------------------------------------------
def grasp_off(ilimbcont):
	f = ['thumb','index','middle']
	a = ['open']*3
	p = [290]*3
	ilimbcont.control(f,a,p)
def grasp_on(ilimbcont):
	f = ['thumb','index','middle']
	a = ['open']*3
	p = [290]*3
	ilimbcont.control(f,a,p)
#------------------------------------------------------------------------------------------------------
#UR10 controller
UR10Cont = UR10Controller('10.1.1.6')
#UR10 pose manager
UR10PoseManager = URPoseManager()
UR10PoseManager.load('tangram.urpose')
#iLimb controller
# iLimbCont = iLimbController('COM16')
iLimbCont = iLimbController('/dev/ttyACM0')
iLimbCont.connect()
#iLimbCont.setPose('openHand')
#time.sleep(2)
#------------------------------------------------------------------------------------------------------
UR10Cont.read_joints_and_xyzR()
xyzR = copy(UR10Cont.xyzR)
jointsv = copy(UR10Cont.joints)
#------------------------------------------------------------------------------------------------------
#rotate the thumb back
#iLimbCont.control('thumbRotator','open',290)
f = ['thumbRotator','thumb','index','middle']
a = ['open']*4
p = [290]*4
iLimbCont.control(f,a,p)
time.sleep(2)
#open the fingers
#grasp_off(iLimbCont)
ur_home(UR10Cont,UR10PoseManager)
#move to the object
UR10PoseManager.moveUR(UR10Cont,'objectP',2)
time.sleep(2)
#rotate the thumb
#iLimbCont.control('thumbRotator','close',290)
f = ['thumbRotator']
a = ['close']
p = [150]
iLimbCont.control(f,a,p)
#time.sleep(2)
#pick orientation
ur_pick(UR10Cont)
#time.sleep(1)
#grasp
f = ['thumb','index','middle']
a = ['position']*3
p = [180,180,190]
iLimbCont.control(f,a,p)
time.sleep(2)
f = ['thumb','index','middle']
a = ['position']*3
p = [200,200,200]
iLimbCont.control(f,a,p)
time.sleep(2)
#go up
xyzR = UR10PoseManager.getPosJoint('objectP')
xyzR[2] += 10
UR10Cont.movej(xyzR,2)
time.sleep(2)

#move to tangram
xyzR_tangram = UR10PoseManager.getPosJoint('tangramP')
xyzR_move = copy(xyzR)
xyzR_move[0] = xyzR_tangram[0] - 15
xyzR_move[1] = xyzR_tangram[1] + 15
UR10Cont.movej(xyzR_move,5)
time.sleep(5)

#rotate
ur_rotate(UR10Cont,46)
time.sleep(1)
ur_pick(UR10Cont)
#UR10Cont.read_joints_and_xyzR()
#xyzR = copy(UR10Cont.xyzR)
#xyzR[2] += 135
#UR10Cont.movej(xyzR,3)
#time.sleep(3)
a=input('')
f = ['index','middle']
a = ['open']*2
p = [290]*2
iLimbCont.control(f,a,p)
time.sleep(2)
'''
#grasp
grasp_on(iLimbCont)
#restore orientation
UR10PoseManager.moveUR(UR10Cont,'objectP',2)
time.sleep(2)
#rotate
ur_rotate(UR10Cont)
#go to tangram
UR10PoseManager.moveUR(UR10Cont,'tangramP',2)
time.sleep(2)
#pick orientation again
ur_pick(UR10Cont)
#release
grasp_off(iLimbCont)
'''
#go up

#go back home

#UR10PoseManager.moveUR(UR10Cont,'objectP',2)
#time.sleep(2)
#ur_rotate(UR10Cont)
#ur_rotate(UR10Cont)
#ur_pick(UR10Cont)
#------------------------------------------------------------------------------------------------------
