
from pybotics.predefined_models import UR10
from pybotics.geometry import matrix_2_vector
from pybotics.geometry import vector_2_matrix
import numpy as np
import math
np.set_printoptions(suppress=True)

#All the joint angle input arguments to the functions are in degrees
from copy import copy

class ur10_simulator:
    
    def __init__(self):
        self.robot = UR10()
        self.tcp_vec = []
        self.tcp_vec_rpy = []
        self.joints_vec = []

    def set_tcp(self,tcp_vec):
        #Rx, Ry, Rz always in radians
        self.tcp_vec = copy(tcp_vec)

    def set_joints(self,joints_vec):
        self.joints_vec = copy(np.deg2rad(joints_vec))

    def joints2pose(self):
        #Pose is in degrees
        pose = self.robot.fk(self.joints_vec)
        tcp_vec = matrix_2_vector(pose)
        self.tcp_vec_rpy = copy(tcp_vec)
        tcp_vec[3:6] = (tcp_vec[5], tcp_vec[4], tcp_vec[3])
        tcp_vec[2] = tcp_vec[2] + 10
        tcp_vec = copy(self.rpy_to_rxryrz(tcp_vec))
        return tcp_vec

    def ur10_rpy_to_rxryrz(self,tcp_vec_rpy):
        tcp_vec_rpy[3:6] = (tcp_vec_rpy[5], tcp_vec_rpy[4], tcp_vec_rpy[3])
        tcp_vec_rpy[2] = tcp_vec_rpy[2] + 10
        tcp_vec_rxryrz = copy(self.rpy_to_rxryrz(tcp_vec_rpy))
        return tcp_vec_rxryrz



    def newrpy_to_tcp(self,tcp_rpy):

        self.tcp_vec_rpy = copy(tcp_rpy)
        tcp_rpy[3:6] = (tcp_rpy[5], tcp_rpy[4], tcp_rpy[3])
        tcp_rpy[2] = tcp_rpy[2] + 10
        tcp_xyz = copy(self.rpy_to_rxryrz(tcp_rpy))
        return tcp_xyz


    def position_along_endaxis(self,dist_offset):
        #Returns the new X,Y,Z, keeping the same Rx, Ry, Rz, which
        #is at a distance of dist_offset from the end_effector position
        posemat = vector_2_matrix(self.tcp_vec_rpy)

        Rotmat = posemat[0:3,0:3]
        unit_vector = np.matmul(Rotmat,np.transpose([0,0,1]))
        tcp_vec = copy(self.tcp_vec)
        tcp_vec[0:3] = tcp_vec[0:3] + (unit_vector*dist_offset)

        return tcp_vec,unit_vector

    def get_Translation_and_Rotation_Matrix(self):
        posemat = vector_2_matrix(self.tcp_vec_rpy)
        Rotmat = posemat[0:3,0:3]
        translation = self.tcp_vec_rpy[0:3]
        return translation,Rotmat

    def grasp_position_endaxis(self,dist_offset,grasp_offset,constant_axis):
        # constant_axis can be either x,y,or z. 
        # For e.g., if x, then the pivot position has the same x co-ordinate as the position along the end effector normal
        # at distance dist_offset
        posemat = vector_2_matrix(self.tcp_vec_rpy)

        Rotmat = posemat[0:3,0:3]
        unit_vector = np.matmul(Rotmat,np.transpose([0,0,1]))

        if constant_axis == "x":

            curr_theta = np.arctan2(unit_vector[2],unit_vector[1])
            new_theta = curr_theta + (np.pi/2) 
            grasp_vector = np.array([0,np.cos(new_theta),np.sin(new_theta)])
        elif constant_axis == "y":
            curr_theta = np.arctan2(unit_vector[2],unit_vector[0])
            new_theta = curr_theta + (np.pi/2)
            grasp_vector = np.array([np.cos(new_theta),0,np.sin(new_theta)])
        elif constant_axis == "z":
            curr_theta = np.arctan2(unit_vector[1],unit_vector[0])
            new_theta = curr_theta + (np.pi/2)
            grasp_vector = np.array([np.cos(new_theta),np.sin(new_theta),0])

        
        grasp_pivot = (unit_vector*dist_offset) + (grasp_vector*grasp_offset)
        tcp_vec = copy(self.tcp_vec)

        tcp_vec[0:3] = tcp_vec[0:3] + grasp_pivot

        return tcp_vec,unit_vector



    # def optimize_rpy(self,rpy_new):


    # def sub_optimize(self,rpy_new):



    def angle_dist(self,theta1,theta2):
        return np.minimum((2 * np.pi) - abs(theta1 - theta2), abs(theta1 - theta2))


    def pose2joints(self):
        posemat = vector_2_matrix(self.tcp_vec_rpy)
        solved_joints = self.robot.ik(posemat)
        solved_joints
        return solved_joints


    def circular_motion(self,dist_offset,angle,axis):
        
        # Assuming self.tcp_vec_rpy is already available
        # This is simply circular motion along the z axis

        # axis can be "z", "y"

        # First compute normal direction along end effector
        # Then compute the new directions
        # Now compute the new roll and pitch values from these new directions (in radians!!) to get the new tcp_vec_rpy
        # Use the new RPY and the same previous XYZ to generate the new XYZ RxRyRz (tcp_vec) 
        # Find the new pivot position using the new tcp_vec_rpy
        # Return the new pivot_position and the new tcp_vec

        tcp_vec,unit_vector = self.position_along_endaxis(dist_offset)

        print("Old",unit_vector)

        unit_vector_new = np.double([0,0,0])
        
        

        if axis == "z":
            # theta = np.arctan(np.double(unit_vector[1]/unit_vector[0]))    
            V = copy(np.sqrt(np.power(unit_vector[0],2) + np.power(unit_vector[1],2)))
            # unit_vector_new[0] = np.double(V*np.cos(theta + np.deg2rad(angle)))
            # unit_vector_new[1] = np.double(V*np.sin(theta + np.deg2rad(angle)))
            # unit_vector_new[2] = np.double(unit_vector[2])

            
            unit_vector_new[2] = np.sin(np.deg2rad(angle) + np.arctan2(unit_vector[2],V))
            alpha = np.cos(np.deg2rad(angle) + np.arctan2(unit_vector[2],V))/(V)
            unit_vector_new[0] = unit_vector[0]*alpha
            unit_vector_new[1] = unit_vector[1]*alpha

            print("New norm:",np.linalg.norm(unit_vector_new))

        elif axis == "y":
            # theta = np.arctan(np.double(unit_vector[2]/unit_vector[0]))
            V = copy(np.sqrt(np.power(unit_vector[0],2) + np.power(unit_vector[2],2)))
            # unit_vector_new[0] = np.double(V*np.cos(theta + np.deg2rad(angle)))
            # unit_vector_new[1] = np.double(unit_vector[1])
            # unit_vector_new[2] = np.double(V*np.sin(theta + np.deg2rad(angle)))
            
            unit_vector_new[1] = V*np.tan(np.deg2rad(angle) + np.arctan2(unit_vector[1],V))
            alpha = np.sqrt(1-np.power(unit_vector_new[1],2))/np.sqrt(1-np.power(unit_vector[1],2))
            unit_vector_new[0] = unit_vector[0]*alpha
            unit_vector_new[2] = unit_vector[2]*alpha

            print("New norm:",np.linalg.norm(unit_vector_new))




        elif axis == "x":

            # theta = np.arctan(np.double(unit_vector[2]/unit_vector[1]))
            V = copy(np.sqrt(np.power(unit_vector[1],2) + np.power(unit_vector[2],2)))
            # unit_vector_new[0] = np.double(unit_vector[0])
            # unit_vector_new[1] = np.double(V*np.cos(theta + np.deg2rad(angle)))
            # unit_vector_new[2] = np.double(V*np.sin(theta + np.deg2rad(angle)))

            
            unit_vector_new[0] = V*np.tan(np.deg2rad(angle) + np.arctan2(unit_vector[0],V))
            alpha = np.sqrt(1-np.power(unit_vector_new[0],2))/np.sqrt(1-np.power(unit_vector[0],2))
            unit_vector_new[1] = unit_vector[1]*alpha
            unit_vector_new[2] = unit_vector[2]*alpha

            print("New norm:",np.linalg.norm(unit_vector_new))




        print("New",unit_vector_new)



        print("oldtcp",self.tcp_vec_rpy)

        # tcp_vec_rpy[3] is kept unchanged (assumption)

        x = copy(unit_vector_new[0])
        y = copy(unit_vector_new[1])
        z = copy(unit_vector_new[2])

        s1 = copy(np.sin(self.tcp_vec_rpy[3]))
        c1 = copy(np.cos(self.tcp_vec_rpy[3]))
        s3 = copy((x*s1) - (y*c1))

        # c3 = copy(np.sqrt(1-np.power(s3,2)))
        # c2 = copy(z/c3)
        # s2 = copy(np.sqrt(1-np.power(c2,2)))
        # copy(((x*c1) + (y*s1))/c3)
        
        tcp_vec_rpy_new = copy(self.tcp_vec_rpy)
        

        val = np.zeros((4))
        err = np.zeros((4))
        t3 = np.arcsin(s3)

        val = [t3 - 2*np.pi, (np.pi-t3),-(np.pi+t3), t3]


        for i in range(4):
            # err[i] = np.abs(self.tcp_vec_rpy[5] - val[i])
            err[i] = self.angle_dist(self.tcp_vec_rpy[5],val[i])

        ind = np.argmin(err)
      
        tcp_vec_rpy_new[5] = val[ind]

        c3 = np.cos(tcp_vec_rpy_new[5])
        c2 = copy(z/c3)
        s2 = ((x*c1)+ (y*s1))/c3

        val = np.zeros((4))
        err = np.zeros((4))
        t2 = np.arccos(c2)
        val = [2*np.pi - t2,-t2, t2 - 2*np.pi,t2]

        for i in range(4):
            # err[i] = np.abs(self.tcp_vec_rpy[4] - val[i])
            if np.abs(np.sin(val[i]) - s2)<0.001:
                print("ola")
                # err[i] = np.abs(self.tcp_vec_rpy[4] - val[i])
                err[i] = self.angle_dist(self.tcp_vec_rpy[4],val[i])
            else:
                err[i] = np.inf

        ind = np.argmin(err)
        print("index2",ind)

        tcp_vec_rpy_new[4] = val[ind]

        # # if self.angle_dist(np.arcsin(s2),self.tcp_vec_rpy[4])<self.angle_dist(np.arcsin(-s2),self.tcp_vec_rpy[4]):
        # #     print("here1")
        # #     tcp_vec_rpy_new[4] = copy(np.arcsin(s2))
        # # else:
        # #     print("here2")
        # #     tcp_vec_rpy_new[4] = copy(np.arcsin(-s2))

        

        # for i in range(4):
        #     # err[i] = np.abs(self.tcp_vec_rpy[5] - val[i])
        #     # if np.abs(np.cos(val[i])*np.cos(tcp_vec_rpy_new[4]) - z)<0.001:
        #     err[i] = self.angle_dist(self.tcp_vec_rpy[5],val[i])
            


        

        print("newc2c3",np.cos(tcp_vec_rpy_new[4])*np.cos(tcp_vec_rpy_new[5]))

        tcp_vec_new = copy(self.ur10_rpy_to_rxryrz(copy(tcp_vec_rpy_new)))
        print(tcp_vec_new)
        self.tcp_vec = copy(tcp_vec_new)
        self.tcp_vec_rpy = copy(tcp_vec_rpy_new)

        endaxis_position,unit_vector = self.position_along_endaxis(dist_offset)
        return endaxis_position


    def rpy_to_rxryrz(self,tcp_vec):
        roll = tcp_vec[3]
        pitch = tcp_vec[4]
        yaw = tcp_vec[5]

        yawMatrix = np.matrix([
        [math.cos(yaw), -math.sin(yaw), 0],
        [math.sin(yaw), math.cos(yaw), 0],
        [0, 0, 1]
        ])

        pitchMatrix = np.matrix([
        [math.cos(pitch), 0, math.sin(pitch)],
        [0, 1, 0],
        [-math.sin(pitch), 0, math.cos(pitch)]
        ])

        rollMatrix = np.matrix([
        [1, 0, 0],
        [0, math.cos(roll), -math.sin(roll)],
        [0, math.sin(roll), math.cos(roll)]
        ])

        R = yawMatrix * pitchMatrix * rollMatrix

        theta = math.acos(((R[0, 0] + R[1, 1] + R[2, 2]) - 1) / 2)
        multi = 1 / (2 * math.sin(theta))

        tcp_vec[3] = multi * (R[2, 1] - R[1, 2]) * theta
        tcp_vec[4] = multi * (R[0, 2] - R[2, 0]) * theta
        tcp_vec[5] = multi * (R[1, 0] - R[0, 1]) * theta

        return tcp_vec


if __name__ == '__main__':

    Sim = ur10_simulator()
    Sim.set_joints(joints)

        