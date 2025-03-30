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
Ui_MainWindow, QMainWindow = loadUiType('formInputs_gui.ui')
#-------------------------------------------------------------------------------
class FormInputs(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, type=0):
        super(FormInputs,self).__init__()
        self.setupUi(self)
        self.btnOk.clicked.connect(self.doSelect)
        self.parent = parent
        self.type = type
    def doSelect(self):
        inputs = self.tbInputs.toPlainText()
        # print(inputs)
        if self.type == 0:
            self.parent.texture = inputs
            print(self.parent.texture)
        elif self.type == 1:
            self.parent.force = inputs
        elif self.type == 2:
            self.parent.palpation = inputs
#-------------------------------------------------------------------------------
#Run the app
if __name__ == '__main__':
    import sys
    from PyQt5 import QtCore, QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = FormInputs()
    main.show()
    sys.exit(app.exec_())
#-------------------------------------------------------------------------------
