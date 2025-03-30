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
# Description: This file contains all the necessary methods for controlling
# the iLimb via Python
#-------------------------------------------------------------------------------
# Added wrist control as well. For now, I will treat the wrist as if it is just
# another
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#LIBRARIES
#-------------------------------------------------------------------------------
import numpy as np
import time
from threading import Thread
from serial import Serial
#------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# DICTIONARY CLASS
# The dictionary keys should be used for sending commands to the iLimb
class iLimb():
    fingers = dict(thumb=0,index=1,middle=2,ring=3,little=4,thumbRotator=5,wrist=6)
    cmds = dict(stop=0,close=1,open=2,position=3,clockwise=4,anticlockwise=5)
    poses = dict(openHand=0,powerGrasp=1,pinchGrasp=2,tripodGrasp=3,rest=4)
#-------------------------------------------------------------------------------
# CONTROLLER CLASS
#-------------------------------------------------------------------------------
#Class: iLimbController
#This class allows for individually controlling each finger of the iLimb
#and some pre-programmed gestures or grasps
class iLimbController:
    def __init__(self,comport='/dev/ttyACM0'):
        #serial port name
        self.portName = comport
        #baud rate
        self.UART_BAUD = 115200
        #serial handler
        self.serialHandler = Serial()
        #package constants
        self.PKG_ST = 0x24
        self.PKG_ET = 0x21
        #minimum and maximum positions for each finger
        self.fingerPosMinMax = np.zeros((6,2))
        #from thumb to little, there are 500 different positions
        for k in range(5):
            self.fingerPosMinMax[k,0] = 0
            self.fingerPosMinMax[k,1] = 500
        #for the thumb rotator, there is 750 different positions
        self.fingerPosMinMax[-1][0] = 0
        self.fingerPosMinMax[-1][1] = 750
        #vector for storing current positions of each finger
        self.currentFingerPos = np.zeros((6,1))
        #minimum and maximum pwm values
        self.minPwm = 0
        self.maxPwm = 297
        #defines the pre-defined grasps
        #whenever a new grasp is designed, it should be added in the class,
        #to this vector and to the iLimbPoses enum
        self.poses = [self.openHand,self.powerGrasp,self.pinchGrasp,self.tripodGrasp,self.rest]
        #-----------------------------------------------------------------------
        #FEEDBACK CONTROL BASED ON TACTILE SENSORS
        self.controlPos = 0
        self.controlSampleCounter = 0
        self.forceList = [[] for k in range(5)]
        self.ControlPowerGraspFinished = False
        self.ControlPinchTouchFinished = False
        self.ControlTouchForceFinished = False
        #-----------------------------------------------------------------------
    #connect with the iLimb
    def connect(self):
        try:
            self.serialHandler = Serial(self.portName, self.UART_BAUD)
            time.sleep(0.1) #necessary to wait before flushing
            if self.serialHandler.isOpen(): #check if port was open
                self.serialHandler.reset_input_buffer() #flush input
                self.serialHandler.reset_output_buffer() #flush output
            return True
        except:
            return False

    #disconnect
    def disconnect(self):
        #check if the serial handler object has been instantiated
        if(self.serialHandler is not None):
            #check if the serial port is open
            if(self.serialHandler.isOpen()):
                #close the serial port
                self.serialHandler.close()
                return True
            else:
                return False
        else:
            return False

    def resetControl(self):
        self.controlPos = 0
        self.controlSampleCounter = 0
        self.forceList = [[] for k in range(5)]
        self.ControlPowerGraspFinished = False
        self.ControlPinchTouchFinished = False

    #close all the fingers based on feedback
    def doFeedbackPowerGrasp(self,tactileArray,fingerArray,numberSamples):
        #add the force frame from the tactile array
        for k in range(len(fingerArray)):
            self.forceList[k].append(tactileArray[fingerArray[k][1]])

        if self.controlSampleCounter >= numberSamples:
            if self.ControlPowerGraspFinished is False:
                maximumValues = []
                meanv = []
                flagTouch = [False]*len(fingerArray)
                flagPower = [False]*len(fingerArray)
                ftouch = [] #which fingers to move for touch
                fpower = [] #which fingers to move for power grasp
                for k in range(len(fingerArray)):
                    #find the maximum values for each frame
                    maximumValues.append([np.max(x) for x in self.forceList[k]])
                    #find which frame had the maximum value
                    idxFrameMax = np.where(maximumValues[k] == np.max(maximumValues[k]))
                    #find which taxel had the maximum value
                    idxTaxel = np.where(self.forceList[k][idxFrameMax[0][0]] == np.max(maximumValues[k]))
                    #create a vector with the values for this taxel in every frame
                    taxelValues = [x[idxTaxel[0][0]][idxTaxel[1][0]] for x in self.forceList[k]]
                    #print(taxelValues) #debugging
                    #take the average of this taxel over all frames
                    meanv.append(np.mean(taxelValues))
                    #check if the finger has made contact
                    if meanv[k] > 0.05:
                        flagTouch[k] = True
                    else:
                        ftouch.append(fingerArray[k][0])
                    #check if the finger has reached the desired force
                    if meanv[k] < fingerArray[k][2]:
                        fpower.append(fingerArray[k][0]) #add the finger to the list of fingers to be closed
                    else:
                        flagPower[k] = True #otherwise, this finger is ok

                print(meanv)

                #not all fingers have made contact
                if flagTouch.count(True) < len(fingerArray):
                    self.control(ftouch,['position']*len(ftouch),[self.controlPos]*len(ftouch))
                    self.controlPos += 10
                elif flagPower.count(True) < len(fingerArray):
                    self.control(fpower,['close']*len(fpower),[297]*len(fpower))
                elif flagPower.count(True) == len(fingerArray):
                    for k in range(6):
                        #finish the power grasp
                        #close all fingers
                        f = ['thumb','index','middle','ring','little']
                        self.control(f,['close']*len(f),[297]*len(f))
                        time.sleep(0.1)
                        # time.sleep(0.1)
                        # self.control(['middle'],['close'],[297])
                        # time.sleep(0.1)
                        # self.control('little','close',297)
                        # time.sleep(0.1)
                    self.ControlPowerGraspFinished = True

            self.controlSampleCounter = 0
            self.forceList = [[] for x in range(5)]
            time.sleep(0.05)
        else:
            self.controlSampleCounter += 1

        return self.ControlPowerGraspFinished

    #pinch for slight touch --> useful for palpation
    def doFeedbackPinchTouch(self,tactileArray,fingerArray,numberSamples):
        #add the force frame from the tactile array
        for k in range(len(fingerArray)):
            self.forceList[k].append(tactileArray[fingerArray[k][1]])

        if self.controlSampleCounter >= numberSamples:
            if self.ControlPinchTouchFinished is False:
                maximumValues = []
                meanv = []
                flagTouch = [False]*len(fingerArray)
                flagPower = [False]*len(fingerArray)
                ftouch = [] #which fingers to move for touch
                fpower = [] #which fingers to move for power grasp
                for k in range(len(fingerArray)):
                    #find the maximum values for each frame
                    maximumValues.append([np.max(x) for x in self.forceList[k]])
                    #find which frame had the maximum value
                    idxFrameMax = np.where(maximumValues[k] == np.max(maximumValues[k]))
                    #find which taxel had the maximum value
                    idxTaxel = np.where(self.forceList[k][idxFrameMax[0][0]] == np.max(maximumValues[k]))
                    #create a vector with the values for this taxel in every frame
                    taxelValues = [x[idxTaxel[0][0]][idxTaxel[1][0]] for x in self.forceList[k]]
                    #print(taxelValues) #debugging
                    #take the average of this taxel over all frames
                    meanv.append(np.mean(taxelValues))
                    #check if the finger has made contact
                    if meanv[k] > 0.08:
                        flagTouch[k] = True
                    else:
                        ftouch.append(fingerArray[k][0])

                print(meanv)

                #not all fingers have made contact
                if flagTouch.count(True) < len(fingerArray):
                    self.control(ftouch,['position']*len(ftouch),[self.controlPos]*len(ftouch))
                    self.controlPos += 2
                else:
                    time.sleep(0.1)
                    print('here')
                    ftouch = ['thumb','index']
                    self.control(ftouch,['position']*len(ftouch),[self.controlPos-20]*len(ftouch))
                    self.ControlPinchTouchFinished = True

            self.controlSampleCounter = 0
            self.forceList = [[] for x in range(5)]
            time.sleep(0.05)
        else:
            self.controlSampleCounter += 1

        return self.ControlPinchTouchFinished

    #closes only one finger until a desired force is attained
    #look only for the central taxels for determining whether the contact
    #is ok
    def doFeedbackTouchForce(self,tactileArray,finger,numberSamples):

        self.forceList[0].append(tactileArray[finger[1]])
        # print(self.forceList[0][-1][1:3,1:3]) #debugging

        if self.controlSampleCounter >= numberSamples:
            self.controlSampleCounter = 0
            if self.ControlTouchForceFinished is False:
                #set touch flag to false
                flagTouch = False
                #retrieves the maximum value from the center taxels
                maximumValues = [np.max(x) for x in self.forceList[0]]
                maxv = np.max(maximumValues)
                idxFrameMax = np.where(maximumValues == maxv)[0][0]
                idxTaxel = np.where(self.forceList[0][idxFrameMax] == maxv)
                meanv = np.mean([x[idxTaxel[0][0]][idxTaxel[1][0]] for x in self.forceList[0]])
                # meanv = np.mean(self.forceList[0])
                self.forceList = [[] for x in range(5)]
                # print(meanv)
                #check if finger has touched object
                if meanv > 0.01:
                    # print(meanv)
                    flagTouch = True
                    if meanv < finger[2]:
                        if self.controlPos < 500:
                            self.control(finger[0],'position',self.controlPos)
                            self.controlPos += 5
                        else:
                            self.control(finger[0],'close',297)
                        return False
                    else:
                        self.ControlTouchForceFinished = True
                        return True
                else:
                    self.control(finger[0],'position',self.controlPos)
                    self.controlPos += 5
                    if self.controlPos > 500:
                        self.controlPos = 500
                    # print(self.controlPos,numberSamples) #debugging
                    return False
                    # print('here')

                #keep closing until one of the central taxels reach the desired
                #force
                #1) keep closing until contact is done
                #2) keep pressing until the desired force is obtained
        else:
            self.controlSampleCounter += 1

        return False

        # #check if the number of force samples have been collected
        # if self.controlSampleCounter >= numberSamples:
        #     if self.ControlPinchTouchFinished is False:
        #         maximumValues = []
        #         meanv = []
        #         flagTouch = [False]*len(fingerArray)
        #         flagPower = [False]*len(fingerArray)
        #         ftouch = [] #which fingers to move for touch
        #         fpower = [] #which fingers to move for power grasp
        #         for k in range(len(fingerArray)):
        #             #find the maximum values for each frame
        #             maximumValues.append([np.max(x) for x in self.forceList[k]])
        #             #find which frame had the maximum value
        #             idxFrameMax = np.where(maximumValues[k] == np.max(maximumValues[k]))
        #             #find which taxel had the maximum value
        #             idxTaxel = np.where(self.forceList[k][idxFrameMax[0][0]] == np.max(maximumValues[k]))
        #             #create a vector with the values for this taxel in every frame
        #             taxelValues = [x[idxTaxel[0][0]][idxTaxel[1][0]] for x in self.forceList[k]]
        #             #print(taxelValues) #debugging
        #             #take the average of this taxel over all frames
        #             meanv.append(np.mean(taxelValues))
        #             #check if the finger has made contact
        #             if meanv[k] > 0.08:
        #                 flagTouch[k] = True
        #             else:
        #                 ftouch.append(fingerArray[k][0])
        #
        #         print(meanv)
        #
        #         #not all fingers have made contact
        #         if flagTouch.count(True) < len(fingerArray):
        #             self.control(ftouch,['position']*len(ftouch),[self.controlPos]*len(ftouch))
        #             self.controlPos += 2
        #         else:
        #             time.sleep(0.1)
        #             print('here')
        #             ftouch = ['thumb','index']
        #             self.control(ftouch,['position']*len(ftouch),[self.controlPos-20]*len(ftouch))
        #             self.ControlPinchTouchFinished = True
        #
        #     self.controlSampleCounter = 0
        #     self.forceList = [[] for x in range(5)]
        #     time.sleep(0.05)
        # else:
        #     self.controlSampleCounter += 1
        #
        # return 0

    #sends a complete package via serial to the iLimb
    #the package is assembled by using the function 'controlFingers'
    def sendSerialPackage(self,package):
        if self.serialHandler.is_open and package is not None:
            #send the complete package => Python 3
            self.serialHandler.write(bytearray(package))
            '''
            for k in range(len(package)):
                if package[k] is not None:
                    self.serialHandler.write(chr(package[k]))
                else:
                    return False
            '''
        else:
            return False

        return True

    #control all or any of the fingers of the iLimb at once to avoid the pauses when
    #controlling individual fingers in a sequential manner. previously it required
    #a short delay between the calls, now the desired fingers can be sent in a
    #package and be controlled with minimal time difference
    #if the package was successfuly assembled and sent it returns TRUE
    #otherwise, returns FALSE
    def control(self,_fingers,_cmds,_pwmpos=290):
        #check if all the arguments are lists
        #if they are, it means that several fingers will be controlled at once
        if isinstance(_fingers,list) and isinstance(_cmds,list) and isinstance(_pwmpos,list):
            #check if all the arguments have the same length
            #if they are different, then return FALSE
            if (len(_fingers)) == len(_cmds) == len(_pwmpos):
                #create the serial package
                #the size of the package will be equal to:
                #4*N + 3 (header,numbytes,end) where N = number of fingers
                package = [None]*(4*len(_fingers)+3)
                #actual package data begins at index 2
                counter = 2
                #header
                package[0] = self.PKG_ST
                #number of bytes of actual data in the serial package
                package[1] = 4*len(_fingers)
                #end of package
                package[-1] = self.PKG_ET
                #iterate through the list to assemble the package
                for k in range(len(_fingers)):
                    #check if the finger and the command is valid
                    #returns FALSE otherwise
                    if(self.isValidFinger(_fingers[k])) and self.isValidCmd(_cmds[k]):
                        #checks if the pwm or positions is valid
                        #returns FALSE otherwise
                        #print('ok') #debugging
                        if self.isValidPos(_fingers[k],_pwmpos[k]) or self.isValidPwm(_fingers[k],_pwmpos[k]) or self.isValidAngle(_fingers[k],_pwmpos[k]):
                                package[counter] = iLimb.fingers[_fingers[k]] #finger id
                                package[counter+1] = iLimb.cmds[_cmds[k]] #command or action
                                package[counter+2] = _pwmpos[k] >> 8 #pwm or pos MSB
                                package[counter+3] = _pwmpos[k] & 0xFF #pwm or pos LSB
                                counter+=4 #increments the counter to write the next data
                        else:
                            return False #error: wrong values for pwm or position
                    else:
                        return False #error: wrong finger or cmd values
                print(package) #debugging
                #sends the serial package to the iLimb
                self.sendSerialPackage(package)
                return True
            else:
                return False
        else:
            #if the arguments are not lists, then only a single finger
            #will be controlled
            #checks if the finger and cmd are valid, returns FALSE otherwise
            #the package will contain 7 bytes
            package = [None]*7
            if self.isValidFinger(_fingers) and self.isValidCmd(_cmds):
                #checks if the pwm or the position are valid, returns FALSE otherwise
                if self.isValidPos(_fingers,_pwmpos) or self.isValidPwm(_fingers,_pwmpos) or self.isValidAngle(_fingers,_pwmpos):
                    #print('controlling',_pwmpos) #debugging
                    package[0] = self.PKG_ST #start
                    package[1] = 4 #number of bytes of actual data
                    package[2] = iLimb.fingers[_fingers] #finger id
                    package[3] = iLimb.cmds[_cmds] #command or action
                    package[4] = _pwmpos >> 8 #pwm or pos MSB
                    package[5] = _pwmpos & 0xFF #pwm or pos LSB
                    package[6] = self.PKG_ET #end
                else:
                    return False
            else:
                return False
            #print(package) #debugging
            #sends the serial package to the iLimb
            self.sendSerialPackage(package)
            return True

    #Performs a pre-defined grasp or pose of the iLimb
    #Since grasps in general require some delay to wait for the finger
    #to be opened or closed, this method is used as a bypass. Meaning that it
    #actually calls the right method (e.g. openHand) inside a different thread.
    #This way, the main thread of whatever application will not be
    #blocked during the execution of the grasp
    #UPDATE 09/05: Now that I have changed the protocol. this function started to
    #present a strange behavior that seems to be related to threading the serial
    #package. As of now, I have withdrawn the thread. IMPORTANT: therefore, performing
    #poses are BLOCKING since the time.sleep calls will happen inside the calling
    #thread (probably the main thread)
    def setPose(self, _pose):
        if(self.isValidPose(_pose)):
                if(self.serialHandler.isOpen()):
                    #th = Thread(target = self.poses[_pose.value])
                    #th.start()
                    #direct call to the functions
                    #this is not thread-safe = BLOCKING
                    self.poses[iLimb.poses[_pose]]()
                    return True
                else:
                    return False
        else:
            return False

    #completely open the hand
    def openHand(self):
        #first open thumb
        self.control('thumb', 'open', 295)
        time.sleep(1)
        #create a vector with the fingers to be opened
        fingers = ['index','middle','ring','little']
        #create a vector with the command -> all should be opened
        cmds = ['open']*len(fingers)
        #create a vector with the pwm -> all should use 297
        pwms = [295]*len(fingers)
        #open all the fingers
        self.control(fingers,cmds,pwms)
        time.sleep(1) #waits one second
        self.control('thumbRotator', 'open', 295)
        #setting the current position of all fingers to zero
        self.currentFingerPos = np.zeros((6,1))

    #perform power grasp
    def powerGrasp(self):
        #first rotate thumb
        self.control('thumbRotator', 'close')
        time.sleep(1.5) #necessary for waiting the thumb to fully rotate
        #create a vector with the fingers to be opened
        fingers = ['index','middle','ring','little']
        #create a vector with the command -> all should be opened
        cmds = ['close']*len(fingers)
        #create a vector with the pwm -> all should use 297
        pwms = [295]*len(fingers)
        #closes the fingers
        self.control(fingers,cmds,pwms)
        #waits one second
        time.sleep(1)
        #close the thumb, but not completely
        self.control('thumb', 'position', 400)

    def pinchGrasp(self):
        #first rotate thumb
        self.control('thumbRotator', 'position', 520)
        time.sleep(1.2) #necessary for waiting the thumb to rotate
        #move the index finger
        fingers = ['index', 'thumb']
        #action = position
        cmds = ['position']*len(fingers)
        #set the position
        pos = [250]*len(fingers)
        #send the serial command
        self.control(fingers,cmds,pos)

    def tripodGrasp(self):
        #first rotate thumb
        self.control('thumbRotator', 'position', 600)
        time.sleep(1.5) #necessary for waiting the thumb to fully rotate
        #move the index finger
        fingers = ['index', 'thumb', 'middle']
        #action = position
        cmds = ['position']*len(fingers)
        #set the position
        pos = [250]*len(fingers)
        #send the serial command
        self.control(fingers,cmds,pos)

    def rest(self):
        self.setPose('openHand')
        time.sleep(2) #waits for the hand to open
        #close the thumb a little bit
        self.control('thumb','position',400)

    #check if desired pose is valid or not
    def isValidPose(self, _pose):
        if not _pose in iLimb.poses:
            return False
        else:
            return True

    #check if finger is valid or nor
    def isValidFinger(self, _fingerId):
        if not _fingerId in iLimb.fingers:
            return False
        else:
            return True

    #check if the command is valid or not
    def isValidCmd(self, _cmd):
        if not _cmd in iLimb.cmds:
            return False
        else:
            return True

    #check if the position is valid or not
    def isValidPos(self, _fingerId, _pos):
        if self.isValidFinger(_fingerId) and _fingerId != 'wrist':
            _fingerId = iLimb.fingers[_fingerId]
            if(_pos < self.fingerPosMinMax[_fingerId,0] or _pos > self.fingerPosMinMax[_fingerId,1]):
                return False
        else:
            return False
        return True

    #check if the pwm value is valid or not
    def isValidPwm(self, _fingerId, _pwm):
        if (_pwm < self.minPwm or _pwm > self.maxPwm) or _fingerId == 'wrist':
            return False
        else:
            return True

    #check if the angle for the wrist is valid or not
    #should be between 0° and 360°
    def isValidAngle(self, _fingerId, _angle):
        if (_angle < 0 or _angle > 360) or _fingerId != 'wrist':
            return False
        else:
            return True
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#Use the main to test whatever functions of the iLimb
#When executed, it will open the hand and perform a hang-lose
if __name__ == '__main__':
    #creates a new object
    serialPort = 'COM12' #windows, for linux -> /dev/ttyACM0
    il = iLimbController(serialPort)
    il.connect()
    #first fully open the hand
    il.setPose('openHand')
    time.sleep(2)
    #perform a power grasp
    il.setPose('powerGrasp')
    time.sleep(2)
    #open the hand
    il.setPose('openHand')
    time.sleep(2)
    #do a hang lose
    f = ['index','middle','ring']
    c = ['close']*len(f)
    p = [290]*len(f)
    il.controlFingers(f,c,p)
    time.sleep(2)
    #fully open the hand
    il.setPose('openHand')
    time.sleep(2)
    #diconnects from the iLimb
    il.disconnect()
#-------------------------------------------------------------------------------
