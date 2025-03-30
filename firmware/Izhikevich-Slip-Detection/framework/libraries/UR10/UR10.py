# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
# Author: Rohan Ghosh, MSc
# Contact:
#-------------------------------------------------------------------------------
# Description: UR10 controller in python
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
import socket
import numpy as np
from ur10_simulation import ur10_simulator
import time
import struct
import binascii
from copy import copy
import os.path
#-------------------------------------------------------------------------------
class UR10Controller:
    def __init__(self, ip,port_recv = 30003, port_send=30002, buffer_size=1024):

        self.port_send = port_send
        self.port_recv = port_recv
        self.ip = ip
        self.buffer_size = buffer_size
        self.joints = np.zeros((6))
        self.xyzR = np.zeros((6))
        self.timer_start = time.time()

        self.connect()
        self.read_start = copy(self.read_time())
        self.read_timer = 0


    def connect(self):
        self.urcont_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.urcont_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.urcont_send.connect((self.ip,self.port_send))
        self.urcont_recv.connect((self.ip,self.port_recv))

    def disconnect(self):
        self.urcont_send.close()

    def read_time(self):
        packet_1 = self.urcont_recv.recv(4)
        packet_2 = self.urcont_recv.recv(8)
        packet_3 = self.urcont_recv.recv(1048)
        Time = self.get_xyzR(packet_2)
        return Time


    def movej(self,posevec,t):
        X = 0.001*posevec[0]
        Y = 0.001*posevec[1]
        Z = 0.001*posevec[2]
        Rx = posevec[3]
        Ry = posevec[4]
        Rz = posevec[5]
        cmd = "movej(p[" + str(X) + "," + str(Y) + "," + str(Z) + "," + str(Rx) + "," + str(Ry) + "," + str(Rz) + "], t =" + str(t) + ")\n"
        # print(cmd)
        # a = input("")
        cmd = bytes(cmd, 'utf-8')
        self.urcont_send.send(cmd)

    def movel(self,posevec,t):
        X = 0.001*posevec[0]
        Y = 0.001*posevec[1]
        Z = 0.001*posevec[2]
        Rx = posevec[3]
        Ry = posevec[4]
        Rz = posevec[5]
        cmd = "movel(p[" + str(X) + "," + str(Y) + "," + str(Z) + "," + str(Rx) + "," + str(Ry) + "," + str(Rz) + "], t =" + str(t) + ")\n"
        # print(cmd)
        # a = input("")
        cmd = bytes(cmd, 'utf-8')
        self.urcont_send.send(cmd)

    def movejoint(self,jointvec,t):
        cmd = "movej([" + str(jointvec[0]) + "," + str(jointvec[1]) + "," + str(jointvec[2]) + "," + str(jointvec[3]) + "," + str(jointvec[4]) + "," + str(jointvec[5]) + "], t =" + str(t) +  ") \n"
        cmd = bytes(cmd, 'utf-8')
        # print(cmd)
        self.urcont_send.send(cmd)

    def stopj(self,a = 2.0):
        cmd = "stopj(" + str(a) + ") \n"
        cmd = bytes(cmd, 'utf-8')
        print(cmd)
        self.urcont_send.send(cmd)


    def clear_buffer(self):
        #t1 = time.time()
        self.timer_current = copy(time.time()) - self.timer_start
        t1 = time.time()
        while 1:
            time.sleep(0.00001)
            T = self.read_time()
            self.read_timer = T - self.read_start
            if  self.timer_current - self.read_timer <0.05:
                break
        #t2 = time.time() - t1





    def read_xyz(self):
        #time.sleep(0.05)
        self.clear_buffer()
        #time.sleep(0.05)
        packet_1 = self.urcont_recv.recv(4)
        packet_2 = self.urcont_recv.recv(8)
        self.read_timer = self.get_xyzR(packet_2) - self.read_start
        self.timer_current = time.time() - self.timer_start

        packet_3 = self.urcont_recv.recv(48)
        packet_4 = self.urcont_recv.recv(48)
        packet_5 = self.urcont_recv.recv(48)
        packet_6 = self.urcont_recv.recv(48)
        packet_7 = self.urcont_recv.recv(48)
        packet_8 = self.urcont_recv.recv(48)
        packet_9 = self.urcont_recv.recv(48)
        packet_10 = self.urcont_recv.recv(48)
        packet_11 = self.urcont_recv.recv(48)

        for i in range(6):
            packet = self.urcont_recv.recv(8)
            if i<3:
                self.xyzR[i] = self.get_xyzR(packet)*1000
            else:
                self.xyzR[i] = self.get_xyzR(packet)

        useless = self.urcont_recv.recv(568)


    def get_joint(self,packet):
        #x = packet[0:8].encode("hex")
        #x = binascii.hexlify(packet[0:8].encode('utf8'))
        x = packet[0:8].hex()
        y = str(x)
        y = struct.unpack('!d', bytes.fromhex(y))[0]
        val = y * (180.0/3.1419)
        return val

    def get_xyzR(self,packet):
        #x = packet[0:8].encode("hex")
        #x = binascii.hexlify(packet[0:8].encode('utf8'))
        x = packet[0:8].hex()
        y = str(x)
        y = struct.unpack('!d', bytes.fromhex(y))[0]
        val = y
        return val


    def read_joints(self):
        t1 = time.time()
        self.clear_buffer()
        print("Time to learn",time.time() - t1)

        #time.sleep(0.05)
        packet_1 = self.urcont_recv.recv(4)
        packet_2 = self.urcont_recv.recv(8)
        self.read_timer = self.get_xyzR(packet_2) - self.read_start
        self.timer_current = time.time() - self.timer_start
        packet_3 = self.urcont_recv.recv(48)
        packet_4 = self.urcont_recv.recv(48)
        packet_5 = self.urcont_recv.recv(48)
        packet_6 = self.urcont_recv.recv(48)
        packet_7 = self.urcont_recv.recv(48)

        for i in range(6):
            packet = self.urcont_recv.recv(8)
            self.joints[i] = self.get_joint(packet)

        useless = self.urcont_recv.recv(760)




    def read_joints_and_xyzR(self):
        self.clear_buffer()
        # time.sleep(0.05)
        packet_1 = self.urcont_recv.recv(4)
        packet_2 = self.urcont_recv.recv(8)
        packet_3 = self.urcont_recv.recv(48)
        packet_4 = self.urcont_recv.recv(48)
        packet_5 = self.urcont_recv.recv(48)
        packet_6 = self.urcont_recv.recv(48)
        packet_7 = self.urcont_recv.recv(48)

        for i in range(6):
            packet = self.urcont_recv.recv(8)
            self.joints[i] = self.get_joint(packet)

        packet_9 = self.urcont_recv.recv(48)
        packet_10 = self.urcont_recv.recv(48)
        packet_11 = self.urcont_recv.recv(48)

        for i in range(6):
            packet =  self.urcont_recv.recv(8)
            if i < 3:
                self.xyzR[i] = self.get_xyzR(packet)*1000
            else:
                self.xyzR[i] = self.get_xyzR(packet)

        useless = self.urcont_recv.recv(568)


    def move_joint_with_constraints(self, joints_vec, dist_pivot):
        #joints_vec is in degrees

        # self.read_joints_and_xyzR()

        self.read_joints()
        # time.sleep(0.5)
        self.read_xyz()
        S1 = ur10_simulator()



        S1.set_joints(self.joints)
        S1.tcp_vec = S1.joints2pose()
        S1.set_tcp(self.xyzR)
        pivot_curr,unit_vector = copy(S1.position_along_endaxis(dist_pivot))
        # print(pivot_curr)

        S1.set_joints(joints_vec)
        S1.tcp_vec = copy(S1.joints2pose())
        pivot_new,unit_vector = copy(S1.position_along_endaxis(dist_pivot))


        xyz_shift = pivot_curr[0:3] - pivot_new[0:3]
        new_xyzR = copy(S1.tcp_vec)
        new_xyzR[0:3] = np.add(S1.tcp_vec[0:3],xyz_shift)

        S1.tcp_vec = copy(new_xyzR)
        # print(S1.position_along_endaxis(dist_pivot))

        return new_xyzR

    def move_joints_with_grasp_constraints(self, joints_vec, dist_pivot,grasp_pivot,constant_axis):

        self.read_joints()
        # time.sleep(0.5)
        self.read_xyz()
        S1 = ur10_simulator()



        S1.set_joints(self.joints)
        S1.tcp_vec = S1.joints2pose()
        S1.set_tcp(self.xyzR)
        pivot_curr,unit_vector = copy(S1.grasp_position_endaxis(dist_pivot,grasp_pivot,constant_axis))
        # print(pivot_curr)

        S1.set_joints(joints_vec)
        S1.tcp_vec = copy(S1.joints2pose())
        pivot_new,unit_vector = copy(S1.grasp_position_endaxis(dist_pivot,grasp_pivot,constant_axis))


        xyz_shift = pivot_curr[0:3] - pivot_new[0:3]
        new_xyzR = copy(S1.tcp_vec)
        new_xyzR[0:3] = np.add(S1.tcp_vec[0:3],xyz_shift)

        S1.tcp_vec = copy(new_xyzR)
        # print(S1.position_along_endaxis(dist_pivot))

        return new_xyzR


    def circular_pivot_motion(self, angle, dist_pivot,axis):

        self.read_joints()
        # time.sleep(0.5)
        self.read_xyz()
        S1 = ur10_simulator()

        S1.set_joints(self.joints)
        S1.tcp_vec = S1.joints2pose()
        S1.set_tcp(self.xyzR)
        pivot_curr,unit_vector = copy(S1.position_along_endaxis(dist_pivot))

        pivot_new = S1.circular_motion(dist_pivot,angle,axis)

        xyz_shift = pivot_curr[0:3] - pivot_new[0:3]

        new_xyzR = copy(S1.tcp_vec)
        new_xyzR[0:3] = np.add(S1.tcp_vec[0:3],xyz_shift)

        S1.tcp_vec = copy(new_xyzR)

        return new_xyzR

    def do_circular_pivot_motion(self, angle, dist_pivot,axis,t,correction):

        Sim = ur10_simulator()
        self.read_joints()
        wrist1 = copy(self.joints[5])
        print("Wrist_old",wrist1)
        Sim.set_joints(self.joints)
        useless = copy(Sim.joints2pose())
        new_xyzR = self.circular_pivot_motion(angle,dist_pivot,axis)
        self.movej(new_xyzR,t)
        time.sleep(t + 0.2)
        self.read_joints()
        newjoints = copy(self.joints)
        # newjoints[5] = wrist1+correction
        newjoints[5] = newjoints[5] + correction
        self.movejoint(np.deg2rad(newjoints),2)
        time.sleep(2.1)
        self.read_joints()
        print("Wrist_new",self.joints[5])




#-------------------------------------------------------------------------------
#class for managing UR10 poses and
class URPoseManager():
    def __init__(self):
        #PROPERTY FOR MANAGING POSES (POSITIONS OR JOINTS)
        self.dictKeys = list() #list containing the names of positions/joints
        self.dictPosJoints = dict() #dictionary
        self.dictRelativePos = dict() #dictionary for relative positions

    #MANAGING POSES (POSITIONS OR JOINTS)
    #save pose file
    #filename should contain the full path for the file
    def save(self,filename):
        #open the file stream
        f = open(filename,'w')
        #loop through all the keys
        for k in range(len(self.dictKeys)):
            key = self.dictKeys[k]
            value = self.dictPosJoints[key]
            f.write(key + ' ' + value[0] + ' ')
            [f.write(str(v)+' ') for v in value[1]]
            f.write('\n')
        f.close()

    #load pose file
    #filename should contain the full path for the file
    def load(self,filename):
        if os.path.isfile(filename):
            with open(filename) as f:
                lines = f.readlines()
            #clear the current keys
            self.dictKeys = list()
            #clear the current dictionary
            self.dictPosJoints = dict()
            #for every line, split the string by new line and spaces
            #the actual data will be stored as a list where each position
            #will correspond to a position/joint in the file
            data = [l.split('\n')[0].split(' ') for l in lines]
            #save all the dictionary keys
            self.dictKeys = [str(d[0]) for d in data]
            #update the dictionary
            #loop through all the keys
            for k in range(len(self.dictKeys)):
                # print('loop')
                posevec = [float(x) for x in data[k][2:8]]
                value = [data[k][1],posevec]
                self.dictPosJoints[self.dictKeys[k]] = value
            #print(self.dictKeys) #debugging
            #print(self.dictPosJoints) #debugging
            print('UR poses were loaded successfuly!')
            return True #successfuly managed to load the files
        else:
            return False #could not find the file

    #move the UR robot to the specified pose
    def moveUR(self,urobj,name,time):
        if name in self.dictKeys and name in self.dictPosJoints and isinstance(urobj,UR10Controller):
            if self.dictPosJoints[name][0] == 'p':
                urobj.movej(self.dictPosJoints[name][1],time)
            elif self.dictPosJoints[name][0] == 'j':
                urobj.movejoint(self.dictPosJoints[name][1],time)
            return True
        else:
            return False

    #move the UR robot to a specified pose
    #adding or subtracting a specified angle
    def moveUR_new_joint(self,urobj,name,jointId,angle,time):
        if name in self.dictKeys and name in self.dictPosJoints and isinstance(urobj,UR10Controller):
            pj = self.getPosJoint(name)
            pj[jointId] += np.deg2rad(angle)
            urobj.movejoint(pj,time)
            return True
        else:
            return False

    #get pose names
    def getPoseNames(self):
        return copy(self.dictKeys)

    #get the joint position
    def getPosJoint(self,name):
        if name in self.dictKeys and name in self.dictPosJoints:
            return copy(self.dictPosJoints[name][1])
        else:
            return False #could not find the name

    #adding a new position
    #WARNING: Adding a new position with the same name will overwrite any
    #previous entry
    #WARNING: position should be in m!!
    #WARNING: joints should be in radians!!
    def addPosition(self,name,position):
        if not name in self.dictKeys:
            self.dictKeys.append(name)
        self.dictPosJoints[name] = ['p',position]
        return True

    #adding a new joint
    #WARNING: Adding a new joint with the same name will overwrite any
    #previous entry
    #WARNING: joints should be in radians!!
    def addJoint(self,name,joint):
        if not name in self.dictKeys:
            self.dictKeys.append(name)
        self.dictPosJoints[name] = ['j',joint]
        return True

    #removing a position/joint
    def removePosJoint(self,name):
        if name in self.dictKeys and name in self.dictPosJoints:
            del(self.dictKeys[self.dictKeys.index(name)])
            del(self.dictPosJoints[name])
            return True
        else:
            return False

    #this function remaps all the positions that have been saved to a new
    #home position. necessary when remapping has changed. as long as it is
    #possible to create positions relative to an origin or home position, this
    #method can be used to convert all the stored positions to new values
    #based on a new origin
    #def conv2newHome(self,_home):
    #    print('ok')

#-------------------------------------------------------------------------------

if __name__ == '__main__':

    port = 30003
    ip1 = '10.1.1.6'
    # ip2 = '10.1.1.6'


    import os,sys
    sys.path.append('../iLimb')
    from iLimb import *

    buffer_size = 1024
    U1 = UR10Controller(ip1)


    # U2 = UR10Controller(ip2)




    # U1.read_joints()
    # print(U1.joints)
    # U1.read_joints()
    # Sim = ur10_simulator()
    # Sim.set_joints(U1.joints)
    # U1.xyzR = Sim.joints2pose()
    # print(U1.xyzR)
    # new_joints = copy(U1.joints)
    mult = 1

    Sim = ur10_simulator()
    U1.do_circular_pivot_motion(-40, 190,"z",3,20)
    # time.sleep(3)
    U1.do_circular_pivot_motion(40, 190,"z",3,-20)
    # time.sleep(3)
    U1.do_circular_pivot_motion(-40, 190,"z",3,20)
    # time.sleep(3)
    U1.do_circular_pivot_motion(-40, 190,"z",3,-20)
    # time.sleep(3)

    # for i in range(100):

    #     t1 = time.time()
    #     # U1.read_joints()
    #     U1.read_xyz()
    #     print(time.time() - t1)
    #     print(U1.joints)
    #     # time.sleep(5)
        # print(U1.xyzR)
    #rpy_change = np.deg2rad([0, -10, 0])

    # l = iLimbController('COM16')
    # l.connect()
    # l.control(['thumb','index','middle'],['open']*3,[290]*3)

    angle = -10
    dist_pivot = 220
    grasp_pivot = 25



    # #open the fingers


    # for i in range(6):

    #      #new_xyzR = U1.move_rpy_with_constraints(rpy_change, 175)
    #     #U1.movej(new_xyzR,2)
    #     # l.control(['thumb','index','middle'],['position']*3,[140,120,120])
    #     U1.read_joints()
    #     Sim.set_joints(U1.joints)
    #     U1.xyzR = Sim.joints2pose()
    #     old_xyzR = copy(U1.xyzR)
    #     print(U1.xyzR)
    #     new_joints = copy(U1.joints)
    #     new_joints[4] = new_joints[4] + angle
    #     new_xyzR = U1.move_joints_with_grasp_constraints(new_joints,dist_pivot,grasp_pivot,"z")
    #     U1.movej(new_xyzR,3)
    #     time.sleep(3.2)

    #close the fingers
    # #Bimanual
    #     l.control(['thumb','index','middle'],['open']*3,[290]*3)
#     time.sleep(1)
        # U1.movej(old_xyzR,3)
    #     print(mult, new_joints)


    # old_XYZ = copy(U1.xyzR)
    # # U2.read_xyz()
    # print(U1.xyzR)
    # print(old_XYZ)
    # # Sim.tcp_vec = U1.xyzR

    # mult = 1
    # seconds = 2

    # for i in range(100):

    #     Sim.tcp_vec = Sim.position_along_endaxis(-30)
    #     U1.movej(Sim.tcp_vec,seconds)
    #     time.sleep(seconds)
    #     Sim.tcp_vec = Sim.position_along_endaxis(30)
    #     U1.movej(Sim.tcp_vec,seconds)
    #     time.sleep(seconds)




    # print(Sim.tcp_vec)



    # # print(U2.xyzR)

    # mult = 1
    # for i in range(100):

    #     U1.xyzR[0] = U1.xyzR[0] + (20*mult)
    #     # U2.xyzR[0] = U2.xyzR[0] + (20*mult)

    #     U1.movej(U1.xyzR,1)
    #     # pause(0.05)
    #     # U2.movej(U2.xyzR,0.4)
    #     time.sleep(1)
    #     mult = mult*(-1)






    # print("Joints from port", U.joints)
    # Sim.set_joints(U.joints)
    # Sim.tcp_vec = Sim.joints2pose()
