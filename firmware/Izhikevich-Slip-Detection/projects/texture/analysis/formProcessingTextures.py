# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
#-------------------------------------------------------------------------------
# Description: GUI to help analyzing data
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#PyQt libraries
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QFileDialog #file management
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
Ui_MainWindow, QMainWindow = loadUiType('formProcessingTextures_gui.ui')
#-------------------------------------------------------------------------------
class CONSTS():
    NOFILTER = 0
    HIGHPASS = 1
    LOWPASS = 2
    BANDPASS = 3
#-------------------------------------------------------------------------------
class FormProcessingTextures(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, type=0):
        super(FormProcessingTextures,self).__init__()
        self.setupUi(self)
        #initialize the graphical and interactive elements of the GUI
        self.initGUI()
        #variables
        self.dataFolder = []
#-------------------------------------------------------------------------------
    def initGUI(self):
        '''
        initialize the GUI
        '''
        #button events
        #find the path to the folder containing the tactile data
        self.btnDataFolder.clicked.connect(self.doFindDataFolder)
        #generate dataset
        self.btnGenerateDataset.clicked.connect(self.doGenerate)
        #populate the combobox
        self.cbFilter.addItems(['No Filter','High-pass','Low-pass','Band-pass'])
        self.cbFilter.currentIndexChanged.connect(self.doChangeFilter)
        self.doChangeFilter(CONSTS.NOFILTER)
        #checkbox events
        #normalization
        self.chNormalize.stateChanged.connect(self.checkedNormalize)
        self.checkedNormalize()
        #segmenting the signal
        self.chCut.stateChanged.connect(self.checkedCut)
        self.checkedCut()
#-------------------------------------------------------------------------------
    def showErrorMsgBox(self,strmsg):
        '''
        display an error message box with the specified text
        '''
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(strmsg)
        msg.setWindowTitle("Error")
        # msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
#-------------------------------------------------------------------------------
    def doChangeFilter(self,i):
        if i == CONSTS.NOFILTER:
            self.filterType = CONSTS.NOFILTER
            self.tbPoles.setDisabled(True)
            self.tbHighPass.setDisabled(True)
            self.tbLowPass.setDisabled(True)
        elif i == CONSTS.HIGHPASS:
            self.filterType = CONSTS.HIGHPASS
            self.tbPoles.setDisabled(False)
            self.tbHighPass.setDisabled(False)
            self.tbLowPass.setDisabled(True)
        elif i == CONSTS.LOWPASS:
            self.filterType = CONSTS.LOWPASS
            self.tbPoles.setDisabled(False)
            self.tbHighPass.setDisabled(True)
            self.tbLowPass.setDisabled(False)
        elif i == CONSTS.BANDPASS:
            self.filterType = CONSTS.BANDPASS
            self.tbPoles.setDisabled(False  )
            self.tbHighPass.setDisabled(False)
            self.tbLowPass.setDisabled(False)
#-------------------------------------------------------------------------------
    def doFindDataFolder(self):
        '''
        open a dialog to find the folder where the texture data is located
        '''
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.dataFolder = folder
            self.tbDataFolder.setText(self.dataFolder)
#-------------------------------------------------------------------------------
    def checkedNormalize(self):
        if self.chNormalize.isChecked():
            self.tbBaseline.setDisabled(False)
            self.tbVmin.setDisabled(False)
            self.tbVmax.setDisabled(False)
        else:
            self.tbBaseline.setDisabled(True)
            self.tbVmin.setDisabled(True)
            self.tbVmax.setDisabled(True)
#-------------------------------------------------------------------------------
    def checkedCut(self):
        if self.chCut.isChecked():
            self.tbTstart.setDisabled(False)
            self.tbTend.setDisabled(False)
        else:
            self.tbTstart.setDisabled(True)
            self.tbTend.setDisabled(True)
#-------------------------------------------------------------------------------
    def updateVariables(self):
        '''
        get parameters from the GUI
        '''
        self.npoles = self.tbPoles.text()
        self.highPassFc = self.tbHighPass.text()
        self.lowPassFc = self.tbLowPass.text()
        self.baselinePercentage = self.tbBaseline.text()
        self.vmin = self.tbVmin.text()
        self.vmax = self.tbVmax.text()
        self.tstart = self.tbTstart.text()
        self.tend = self.tbTend.text()
        self.a = self.tbIza.text()
        self.b = self.tbIzb.text()
        self.c = self.tbIzc.text()
        self.d = self.tbIzd.text()
        self.GF = self.tbGain.text()
        self.numIterations = self.tbIterations.text()
        self.numClasses = self.tbClasses.text()
        self.numNeighbors = self.tbNeighbors.text()
#-------------------------------------------------------------------------------
    def doGenerate(self):
        '''
        generate a text file with all the details for processing the tactile
        data for texture recognition
        '''
        self.texture = self.teTexture.toPlainText().split('\n')
        self.force = self.teForce.toPlainText().split('\n')
        self.palpation = self.tePalpation.toPlainText().split('\n')
        print(self.texture,self.force,self.palpation)

        if self.texture == [''] or self.force == [''] or self.palpation == ['']:
            self.showErrorMsgBox('Please, select the parameters for the files')
            return False

        #retrieve the parameters chosen
        self.updateVariables()

        #1) pre-processing parameters
        #2) izhikevich model parameters
        #3) dataset description - which files should be included
        #4) classification parameters
        #   - for now, there is only one possibility which is to use
        #   a k-NN based classifier, extracting two features with a
        #   leave-one-out cross validation metric

        stext = '' #string to be written in the file
        stext += '-------------------------------------------------------\n'
        stext += 'SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE\n'
        stext += 'Neuromorphic Engineering and Robotics Group - NER\n'
        stext += '-------------------------------------------------------\n'
        stext += 'Header file for texture recognition\n'
        stext += '-------------------------------------------------------\n'
        #1)
        stext += 'Pre-processing\n'
        stext += 'Filter type: ' + str(self.filterType) + '\n'
        stext += 'Number of Poles: ' + str(self.npoles) + '\n'
        stext += 'Cut-off: ' + str(self.highPassFc) + ' ' + str(self.lowPassFc) + '\n'
        stext += '-------------------------------------------------------\n'
        stext += 'Normalization\n'
        stext += 'Normalize: ' + str(self.chNormalize.isChecked()) + '\n'
        stext += '% of baseline: ' + str(self.baselinePercentage) + '\n'
        stext += 'Vmin: ' + str(self.vmin) + '\n'
        stext += 'Vmax: ' + str(self.vmax) + '\n'
        stext += '-------------------------------------------------------\n'
        stext += 'Segmenting the tactile signal\n'
        stext += 'Segmentation: ' + str(self.chCut.isChecked()) + '\n'
        stext += 'tstart: ' + str(self.tstart) + '\n'
        stext += 'tstop: ' + str(self.tend) + '\n'
        stext += '-------------------------------------------------------\n'
        #2)
        stext += 'Izhikevich model\n'
        stext += 'a: ' + str(self.a) + '\n'
        stext += 'b: ' + str(self.b) + '\n'
        stext += 'c: ' + str(self.c) + '\n'
        stext += 'd: ' + str(self.d) + '\n'
        stext += 'Gain: ' + str(self.GF) + '\n'
        stext += '-------------------------------------------------------\n'
        #3)
        if self.dataFolder == []:
            self.showErrorMsgBox('Please, select a folder')
            return False
        stext += 'Dataset\n'
        stext += 'Path to data folder: ' + self.dataFolder + '\n'
        stext += 'Texture: '
        for t in self.texture:
            stext += (t + ' ')
        stext +=  '\n'
        stext += 'Force: '
        for f in self.force:
            stext += (f + ' ')
        stext +=  '\n'
        stext += 'Palpation: '
        for p in self.palpation:
            stext += (p + ' ')
        stext +=  '\n'
        stext += 'Number of Iterations: ' +  self.numIterations + '\n'
        stext += '-------------------------------------------------------\n'
        #4)
        stext += 'Classification\n'
        stext += 'Number of classes: ' + str(self.numClasses) + '\n'
        stext += 'Number of neighbors: ' + str(self.numNeighbors) + '\n'
        stext += '-------------------------------------------------------\n'

        #saving the file
        #open a save file dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        #open the dialog and receives the filename
        diag = QFileDialog()
        filename,_ = diag.getSaveFileName(None,'Title','','Texture Processing Header (*.txt)')
        #saves the poses
        #if clicked 'Cancel', then string will be False
        if filename:
            print('file to be loaded: ' + filename)
            f = open(filename,'w')
            f.write(stext)
            f.close()
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormProcessingTextures()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
