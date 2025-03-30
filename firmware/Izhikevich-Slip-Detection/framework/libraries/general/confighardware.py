# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
# ONR Presentation: June 13th, 2018
#-------------------------------------------------------------------------------
# Description:
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
class FileHardwareHandler():
    def __init__(self):
        self.fileHandler = None
        self.UR10 = None
        self.iLimb = None
        self.tactileBoards = None

    def getParameters(self):
        return self.UR10, self.iLimb, self.tactileBoards

    #loads the parameters stored in the file
    def load(self):
        #open the file stream for reading
        self.fileHandler = open('hardware.cfg','r')
        #read all the lines
        lines = self.fileHandler.readlines()
        #print(lines) #debugging
        urs = lines[0].split('\n')[0].split(' ')
        self.UR10 = [urs[0], urs[1]]

        hands = lines[1].split('\n')[0].split(' ')
        self.iLimb = [hands[0],hands[1]]

        boards = lines[2].split('\n')[0].split(' ')
        self.tactileBoards = [boards[0],boards[1]]

    #generates a new file containing the hardware configuration parameters
    #ur10: ip addresses for left and right arm (UR10)
    #ilimb: com ports for left and right hands (iLimb)
    #tactile: com ports for left and right hands (tactile boards)
    def save(self,ur10,ilimb,tactile):
        #open the file stream for writing
        self.fileHandler = open('hardware.cfg','w')
        self.fileHandler.write(str(ur10[0]) + ' ' + str(ur10[1]) + '\n')
        self.fileHandler.write(str(ilimb[0]) + ' ' + str(ilimb[1]) + '\n')
        self.fileHandler.write(str(tactile[0]) + ' ' + str(tactile[1]) + '\n')
        self.fileHandler.close()
#-------------------------------------------------------------------------------
