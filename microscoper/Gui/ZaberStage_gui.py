# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ZaberStage_gui.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Zaber(object):
    def setupUi(self, Zaber):
        Zaber.setObjectName("Zaber")
        Zaber.resize(280, 300)
        Zaber.setMaximumSize(QtCore.QSize(280, 300))
        self.centralwidget = QtWidgets.QWidget(Zaber)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 281, 288))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 8, 0, 1, 3)
        self.moveSpinbox3 = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget)
        self.moveSpinbox3.setDecimals(4)
        self.moveSpinbox3.setMinimum(-400.0)
        self.moveSpinbox3.setMaximum(400.0)
        self.moveSpinbox3.setObjectName("moveSpinbox3")
        self.gridLayout.addWidget(self.moveSpinbox3, 6, 1, 1, 1)
        self.syncButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.syncButton.setObjectName("syncButton")
        self.gridLayout.addWidget(self.syncButton, 7, 0, 1, 1)
        self.lcdNumber = QtWidgets.QLCDNumber(self.gridLayoutWidget)
        self.lcdNumber.setDigitCount(10)
        self.lcdNumber.setObjectName("lcdNumber")
        self.gridLayout.addWidget(self.lcdNumber, 2, 0, 1, 3)
        self.exitButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.exitButton.setObjectName("exitButton")
        self.gridLayout.addWidget(self.exitButton, 9, 0, 1, 1)
        self.homeButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.homeButton.setObjectName("homeButton")
        self.gridLayout.addWidget(self.homeButton, 3, 0, 1, 1)
        self.moveButton2 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.moveButton2.setObjectName("moveButton2")
        self.gridLayout.addWidget(self.moveButton2, 5, 0, 1, 1)
        self.moveSpinbox1 = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget)
        self.moveSpinbox1.setDecimals(4)
        self.moveSpinbox1.setMinimum(-400.0)
        self.moveSpinbox1.setMaximum(400.0)
        self.moveSpinbox1.setObjectName("moveSpinbox1")
        self.gridLayout.addWidget(self.moveSpinbox1, 4, 1, 1, 1)
        self.moveButton1 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.moveButton1.setObjectName("moveButton1")
        self.gridLayout.addWidget(self.moveButton1, 4, 0, 1, 1)
        self.setHomeOffsetButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.setHomeOffsetButton.setObjectName("setHomeOffsetButton")
        self.gridLayout.addWidget(self.setHomeOffsetButton, 3, 2, 1, 1)
        self.moveSpinbox2 = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget)
        self.moveSpinbox2.setDecimals(4)
        self.moveSpinbox2.setMinimum(-400.0)
        self.moveSpinbox2.setMaximum(400.0)
        self.moveSpinbox2.setObjectName("moveSpinbox2")
        self.gridLayout.addWidget(self.moveSpinbox2, 5, 1, 1, 1)
        self.moveButton3 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.moveButton3.setObjectName("moveButton3")
        self.gridLayout.addWidget(self.moveButton3, 6, 0, 1, 1)
        self.upButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.upButton.setObjectName("upButton")
        self.gridLayout.addWidget(self.upButton, 6, 2, 1, 1)
        self.downButton = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.downButton.setObjectName("downButton")
        self.gridLayout.addWidget(self.downButton, 7, 2, 1, 1)
        self.homeOffsetSpinbox = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget)
        self.homeOffsetSpinbox.setDecimals(4)
        self.homeOffsetSpinbox.setMinimum(-180.0)
        self.homeOffsetSpinbox.setMaximum(180.0)
        self.homeOffsetSpinbox.setSingleStep(0.01)
        self.homeOffsetSpinbox.setObjectName("homeOffsetSpinbox")
        self.gridLayout.addWidget(self.homeOffsetSpinbox, 4, 2, 1, 1)
        self.incSpinbox = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget)
        self.incSpinbox.setDecimals(4)
        self.incSpinbox.setSingleStep(0.1)
        self.incSpinbox.setObjectName("incSpinbox")
        self.gridLayout.addWidget(self.incSpinbox, 5, 2, 1, 1)
        self.lineEditComport = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEditComport.setObjectName("lineEditComport")
        self.gridLayout.addWidget(self.lineEditComport, 0, 1, 1, 1)
        self.labelComport = QtWidgets.QLabel(self.gridLayoutWidget)
        self.labelComport.setObjectName("labelComport")
        self.gridLayout.addWidget(self.labelComport, 0, 0, 1, 1)
        self.labelComport_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.labelComport_2.setObjectName("labelComport_2")
        self.gridLayout.addWidget(self.labelComport_2, 1, 0, 1, 1)
        self.lineEditConnport = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEditConnport.setObjectName("lineEditConnport")
        self.gridLayout.addWidget(self.lineEditConnport, 1, 1, 1, 1)
        self.buttonSetPorts = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.buttonSetPorts.setObjectName("buttonSetPorts")
        self.gridLayout.addWidget(self.buttonSetPorts, 0, 2, 2, 1)
        Zaber.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Zaber)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 280, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuRemote = QtWidgets.QMenu(self.menubar)
        self.menuRemote.setObjectName("menuRemote")
        Zaber.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Zaber)
        self.statusbar.setObjectName("statusbar")
        Zaber.setStatusBar(self.statusbar)
        self.action_Connect = QtWidgets.QAction(Zaber)
        self.action_Connect.setObjectName("action_Connect")
        self.action_Quit = QtWidgets.QAction(Zaber)
        self.action_Quit.setObjectName("action_Quit")
        self.action_Disconnect = QtWidgets.QAction(Zaber)
        self.action_Disconnect.setObjectName("action_Disconnect")
        self.menuFile.addAction(self.action_Quit)
        self.menuRemote.addAction(self.action_Connect)
        self.menuRemote.addAction(self.action_Disconnect)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuRemote.menuAction())

        self.retranslateUi(Zaber)
        QtCore.QMetaObject.connectSlotsByName(Zaber)

    def retranslateUi(self, Zaber):
        _translate = QtCore.QCoreApplication.translate
        Zaber.setWindowTitle(_translate("Zaber", "MainWindow"))
        self.syncButton.setText(_translate("Zaber", "Sync"))
        self.exitButton.setText(_translate("Zaber", "Exit"))
        self.homeButton.setText(_translate("Zaber", "Home"))
        self.moveButton2.setText(_translate("Zaber", "Move"))
        self.moveButton1.setText(_translate("Zaber", "Move"))
        self.setHomeOffsetButton.setText(_translate("Zaber", "Set Home Offset"))
        self.moveButton3.setText(_translate("Zaber", "Move"))
        self.upButton.setText(_translate("Zaber", "Up"))
        self.downButton.setText(_translate("Zaber", "Down"))
        self.lineEditComport.setText(_translate("Zaber", "COM4"))
        self.labelComport.setText(_translate("Zaber", "COM PORT"))
        self.labelComport_2.setText(_translate("Zaber", "Connection PORT"))
        self.lineEditConnport.setText(_translate("Zaber", "10122"))
        self.buttonSetPorts.setText(_translate("Zaber", "Set"))
        self.menuFile.setTitle(_translate("Zaber", "File"))
        self.menuRemote.setTitle(_translate("Zaber", "&Remote"))
        self.action_Connect.setText(_translate("Zaber", "&Connect"))
        self.action_Quit.setText(_translate("Zaber", "&Quit"))
        self.action_Disconnect.setText(_translate("Zaber", "&Disconnect"))
