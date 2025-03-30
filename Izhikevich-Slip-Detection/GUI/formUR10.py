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
# Description: GUI for controlling the UR10
# With this GUI it is possible to create a text file containing several positions
# or joint angles that can be used to generate standard UR10 poses
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
import os, sys, glob
sys.path.append('../framework/libraries/general')
sys.path.append('../framework/libraries/iLimb')
sys.path.append('../framework/libraries/UR10')
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QFileDialog #file management
import numpy as np #numpy
from UR10 import * #UR10 libraries
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formUR10_gui.ui')
#-------------------------------------------------------------------------------
class FormUR10(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(FormUR10,self).__init__()
        self.setupUi(self)
        self.UR10Cont = None #object that will be used for controlling the UR10
        #create the pose manager object
        #object that will be used for managing poses
        self.UR10PoseManager = URPoseManager()
        #timer to update the GUI
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update)
        #create a list with the keys -> name of positions or joints
        self.dictKeys = []
        #dictionary containing the stored positions or joints
        self.dictPosJoints = dict()
        self.init() #initialize the GUI

    #initalize the GUI
    def init(self):
        #create the events
        #connect to UR10
        self.btnConnect.clicked.connect(self.doConnect)
        #move UR10
        self.btnMove.clicked.connect(self.doMove)
        #move joints
        self.btnMoveJoints.clicked.connect(self.doMoveJoints)
        #add a new position to the list
        self.btnAddPosition.clicked.connect(self.doAddPos)
        #add a new set of joints to the list
        self.btnAddJoint.clicked.connect(self.doAddJoints)
        #save the pose file
        self.btnSave.clicked.connect(self.doSave)
        #update the positions and joints
        self.btnUpdatePosJoints.clicked.connect(self.doUpdatePosJoints)
        #create an array with all the textbox
        self.tbCont = [self.tbX,self.tbY,self.tbZ,self.tbRx,self.tbRy,self.tbRz]
        self.tbJoints = [self.tbBase,self.tbShoulder,self.tbElbow,self.tbWrist1,self.tbWrist2,self.tbWrist3]
        #sets the initial position values to '0'
        [x.setText('0') for x in self.tbCont]
        #sets the initial joint values to '0'
        [x.setText('0') for x in self.tbJoints]
        #set default time to 10 s
        self.tbTime.setText('10')
        #define the most likely ip anda port
        self.tbIP.setText('10.1.1.6') #ip
        self.tbPort.setText('30002') #port_send

    #connect to the UR10
    def doConnect(self):
        #create the controller object
        #self.UR10Cont = UR10Controller(int(self.tbPort.text()),self.tbIP.text(),1024)
        self.UR10Cont = UR10Controller(self.tbIP.text(),port_send=int(self.tbPort.text()))
        #connect to the UR10
        self.UR10Cont.connect()
        #read positions and joints for the first time to populate the textbox
        self.UR10Cont.read_joints_and_xyzR()
        #populate the positions
        for i in range(len(self.tbCont)):
            self.tbCont[i].setText(str(self.UR10Cont.xyzR[i]))
        #populate the joints
        for i in range(len(self.tbJoints)):
            self.tbJoints[i].setText(str(self.UR10Cont.joints[i]))
        #wait and then start reading continuously
        time.sleep(0.01)
        #if connected, activate the reading function
        self.timer.start()
        #debugging
        #print(self.UR10Cont.ip,self.UR10Cont.port)

    #move the UR10
    def doMove(self):
        #check if the UR10 controller object has been instantiated
        if self.UR10Cont is not None:
            #retrieve the coordinates
            x = float(self.tbX.text())
            y = float(self.tbY.text())
            z = float(self.tbZ.text())
            #retrieve the orientation of the end-effector
            rx = float(self.tbRx.text())
            ry = float(self.tbRy.text())
            rz = float(self.tbRz.text())
            #time duration of the movement
            t = float(self.tbTime.text())
            #create the pose vector
            posevec = [x,y,z,rx,ry,rz]
            #move the UR10
            self.UR10Cont.movej(posevec,t)
            print('moving...')
            #debugging
            print(posevec)
        else:
            return False

    #move UR10 to specified joints
    def doMoveJoints(self):
        if self.UR10Cont is not None:
            t = 10 #always 20 seconds for now
            j = [0]*len(self.tbJoints)
            for k in range(len(self.tbJoints)):
                j[k] = np.deg2rad(float(self.tbJoints[k].text()))
            self.UR10Cont.movejoint(j,t)
            print(j) #debugging

    #add position to the list
    def doAddPos(self):
        if self.UR10PoseManager is not None:
            pose = []
            #create the pose vector with the values contained in the
            #textbox related to position and orientation of the UR10
            [pose.append(float(x.text())) for x in self.tbCont]
            #retrieve the name of the position
            posname = self.tbName.text()
            #add the position to the pose manager
            self.UR10PoseManager.addPosition(posname,pose)
            #saving the position
            print('saving the position:', pose)
            #add the position saved to the list box containing the positions saved
            self.updatePoses()

    #add joint to the list
    def doAddJoints(self):
        if self.UR10PoseManager is not None:
            joints = []
            #create the joints vector with the values contained in the
            #textbox related to the joints of the UR10
            [joints.append(np.deg2rad(float(x.text()))) for x in self.tbJoints]
            #retrieve the name of the position
            posname = self.tbName.text()
            #add the position to the pose manager
            self.UR10PoseManager.addJoint(posname,joints)
            #saving the position
            print('saving the joints:', joints)
            #add the position saved to the list box containing the positions saved
            self.updatePoses()

    #save the positions or joints stored in the dictionary to a
    #file
    def doSave(self):
        if self.UR10PoseManager is not None:
            #open a save file dialog
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            #open the dialog and receives the filename
            diag = QFileDialog()
            filename,_ = diag.getSaveFileName(None,'Title','','URPose (*.urpose)')
            #saves the poses
            #if clicked 'Cancel', then string will be False
            if filename:
                self.UR10PoseManager.save(filename) #saving

    def updatePoses(self):
        #clear the list
        self.lbPoses.clear()
        #get all the keys
        keys = self.UR10PoseManager.getPoseNames()
        for k in range(len(keys)):
            #get the positions/joints for a given key (name)
            value = self.UR10PoseManager.getPosJoint(keys[k])
            #add to the list of poses
            self.lbPoses.addItem(str(keys[k]) + ' ' + str(value))

    #read from the UR10 and update the GUI
    def update(self):
        #check if the controller object has been instantiated
        if self.UR10Cont is not None:
            self.UR10Cont.read_joints_and_xyzR()
            #print(self.UR10Cont.xyzR) #debugging
            strposjoints = ''
            strposjoints += 'X: ' + str(self.UR10Cont.xyzR[0]) + '\n'
            strposjoints += 'Y: ' + str(self.UR10Cont.xyzR[1]) + '\n'
            strposjoints += 'Z: ' + str(self.UR10Cont.xyzR[2]) + '\n'
            strposjoints += 'RX: ' + str(self.UR10Cont.xyzR[3]) + '\n'
            strposjoints += 'RY: ' + str(self.UR10Cont.xyzR[4]) + '\n'
            strposjoints += 'RZ: ' + str(self.UR10Cont.xyzR[5]) + '\n'
            strposjoints += 'Base: ' + str(self.UR10Cont.joints[0]) + '\n'
            strposjoints += 'Shoulder: ' + str(self.UR10Cont.joints[1]) + '\n'
            strposjoints += 'Elbow: ' + str(self.UR10Cont.joints[2]) + '\n'
            strposjoints += 'Wrist 1: ' + str(self.UR10Cont.joints[3]) + '\n'
            strposjoints += 'Wrist 2: ' + str(self.UR10Cont.joints[4]) + '\n'
            strposjoints += 'Wrist 3: ' + str(self.UR10Cont.joints[5]) + '\n'
            self.tbStatus.setPlainText(strposjoints)

    def doUpdatePosJoints(self):
        #read positions and joints for the first time to populate the textbox
        self.UR10Cont.read_joints_and_xyzR()
        #populate the positions
        for i in range(len(self.tbCont)):
            self.tbCont[i].setText(str(self.UR10Cont.xyzR[i]))
        #populate the joints
        for i in range(len(self.tbJoints)):
            self.tbJoints[i].setText(str(self.UR10Cont.joints[i]))
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormUR10()
    main.show()
    sys.exit(app.exec_())
