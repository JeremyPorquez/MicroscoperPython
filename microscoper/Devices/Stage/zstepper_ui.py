# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'zstepper_ui.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_zstepper(object):
    def setupUi(self, zstepper):
        zstepper.setObjectName("zstepper")
        zstepper.resize(151, 201)
        self.centralwidget = QtWidgets.QWidget(zstepper)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(40, 10, 47, 13))
        self.label.setObjectName("label")
        self.positionLabelWidget = QtWidgets.QLabel(self.centralwidget)
        self.positionLabelWidget.setGeometry(QtCore.QRect(40, 30, 47, 13))
        self.positionLabelWidget.setObjectName("positionLabelWidget")
        self.zPositionSpinBoxWidget = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.zPositionSpinBoxWidget.setGeometry(QtCore.QRect(40, 90, 91, 22))
        self.zPositionSpinBoxWidget.setDecimals(7)
        self.zPositionSpinBoxWidget.setMinimum(-1000.0)
        self.zPositionSpinBoxWidget.setMaximum(1000.0)
        self.zPositionSpinBoxWidget.setSingleStep(1.0)
        self.zPositionSpinBoxWidget.setObjectName("zPositionSpinBoxWidget")
        self.zSlider = QtWidgets.QSlider(self.centralwidget)
        self.zSlider.setGeometry(QtCore.QRect(10, 0, 22, 160))
        self.zSlider.setMinimum(-1000)
        self.zSlider.setMaximum(1000)
        self.zSlider.setOrientation(QtCore.Qt.Vertical)
        self.zSlider.setObjectName("zSlider")
        zstepper.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(zstepper)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 151, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuConnection = QtWidgets.QMenu(self.menubar)
        self.menuConnection.setObjectName("menuConnection")
        zstepper.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(zstepper)
        self.statusbar.setObjectName("statusbar")
        zstepper.setStatusBar(self.statusbar)
        self.action_Quit = QtWidgets.QAction(zstepper)
        self.action_Quit.setObjectName("action_Quit")
        self.action_Connect = QtWidgets.QAction(zstepper)
        self.action_Connect.setObjectName("action_Connect")
        self.menuFile.addAction(self.action_Quit)
        self.menuConnection.addAction(self.action_Connect)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuConnection.menuAction())

        self.retranslateUi(zstepper)
        QtCore.QMetaObject.connectSlotsByName(zstepper)

    def retranslateUi(self, zstepper):
        _translate = QtCore.QCoreApplication.translate
        zstepper.setWindowTitle(_translate("zstepper", "MainWindow"))
        self.label.setText(_translate("zstepper", "Position"))
        self.positionLabelWidget.setText(_translate("zstepper", "0"))
        self.menuFile.setTitle(_translate("zstepper", "File"))
        self.menuConnection.setTitle(_translate("zstepper", "Connection"))
        self.action_Quit.setText(_translate("zstepper", "&Quit"))
        self.action_Connect.setText(_translate("zstepper", "&Connect"))

