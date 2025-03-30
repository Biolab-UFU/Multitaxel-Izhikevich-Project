#ilimb Library
from iLimb import *
#important libraries
import time

#create the object
# ilimbcont = iLimbController('COM49') #windows
ilimbcont = iLimbController('/dev/ttyACM0') #linux
# ilimbcont = iLimbController('/dev/usb.modem1423') #mac-os

#IMPORTANT
ilimbcont.connect() #connects to the ilimb

ilimbcont.setPose('openHand') #powerGrasp, pinchGrasp, tripodGrasp, rest
time.sleep(2)
a = input()
#
# #example of controlling an individual finger
# #complete actions
# finger = 'thumb' #thumb, index, middle, ring, little and thumbRotator
# action = 'close' #open, close, stop, position
# pwm = 297 #pwm: 0 - 297 --> suggested: 297
# ilimbcont.control(finger,action,pwm) #send the command
# time.sleep(1) #wait for completing the movement
#
# a = input()

#position
finger = 'thumbRotator'
action = 'position'
pos = 400 #positions: 0-500 for thumb,index,middle,ring and little; 0-750 for thumbRotator
ilimbcont.control(finger,action,pos) #send the command, control position
time.sleep(1) #wait for the finger to move
#a = input()
pos=500
#control of multiple fingers
#example: tripod grasp
fingers = ['thumb','index', 'ring', 'little']
actions = ['position','position', 'position', 'position']
pwmpos = [500,500,500,500]
ilimbcont.control(fingers,actions,pwmpos)
# a = input()
#alternative for multiple fingers
fingers = ['thumb', 'index', 'middle']
actions = ['position'] * len(fingers) #creates a vector of N elements where N is the number of fingers
pos = [150] * len(fingers)
ilimbcont.control(fingers,action,pos)
time.sleep(1)
# a = input()
#control of wrist
# fingers = 'wrist' #indicates the wrist
# action = 'clockwise' #anticlockwise
# pos = 90 #90 degrees #0-360
# ilimb.control(fingers,action,pos)
# time.sleep(1)

#control poses
ilimb.setPose('openHand') #powerGrasp, pinchGrasp, tripodGrasp, rest
time.sleep(2)

#feedback
#these methods should be called within a loop where acquisition or processing
#of tactile sensors are running
#tactileArray = 5x4x4 matrix containing the tactile readings
#fingerArray = vector of vectors where each position specifies
#the index of the tactileArray that corresponds to the finger
#name of the finger
#threshold --> only used for powergrasp. only after the specified amount of
#'force' is acquired, the power grasp is completed
#numberSamples = how many samples should be read for performing the grasping
#IMPORTANT: the iLimb can't go faster than 50 Hz. Based on the sampling rate
#of the tactile board, adjust the number of samples accordingly.
tactileArray = None #imagine that this is the 5x4x4 array
fingerArray = [[2,'thumb',0.1],[0,'index',0.08]]
numberSamples = 30
ilimb.doFeedbackPinchTouch(tactileArray,fingerArray,numberSamples)
ilimb.doFeedbackPowerGrasp(tactileArray,fingerArray,numberSamples)
