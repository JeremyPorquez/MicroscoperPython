# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Server_gui.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ServerGui(object):
    def setupUi(self, ServerGui):
        ServerGui.setObjectName("ServerGui")
        ServerGui.resize(375, 300)
        ServerGui.setMaximumSize(QtCore.QSize(375, 300))
        self.centralwidget = QtWidgets.QWidget(ServerGui)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 371, 274))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.localAddressTextWidget = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.localAddressTextWidget.sizePolicy().hasHeightForWidth())
        self.localAddressTextWidget.setSizePolicy(sizePolicy)
        self.localAddressTextWidget.setMinimumSize(QtCore.QSize(10, 25))
        self.localAddressTextWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.localAddressTextWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.localAddressTextWidget.setObjectName("localAddressTextWidget")
        self.gridLayout.addWidget(self.localAddressTextWidget, 0, 1, 1, 2)
        self.spectrometerPortTextWidget = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        self.spectrometerPortTextWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.spectrometerPortTextWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.spectrometerPortTextWidget.setObjectName("spectrometerPortTextWidget")
        self.gridLayout.addWidget(self.spectrometerPortTextWidget, 3, 1, 1, 1)
        self.startButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.startButtonWidget.setEnabled(False)
        self.startButtonWidget.setObjectName("startButtonWidget")
        self.gridLayout.addWidget(self.startButtonWidget, 6, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 2, 1, 1)
        self.spectrometerPortTextWidgetSend = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spectrometerPortTextWidgetSend.sizePolicy().hasHeightForWidth())
        self.spectrometerPortTextWidgetSend.setSizePolicy(sizePolicy)
        self.spectrometerPortTextWidgetSend.setMinimumSize(QtCore.QSize(10, 25))
        self.spectrometerPortTextWidgetSend.setMaximumSize(QtCore.QSize(16777215, 25))
        self.spectrometerPortTextWidgetSend.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.spectrometerPortTextWidgetSend.setPlainText("")
        self.spectrometerPortTextWidgetSend.setObjectName("spectrometerPortTextWidgetSend")
        self.gridLayout.addWidget(self.spectrometerPortTextWidgetSend, 3, 2, 1, 1)
        self.rotationStageSendButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.rotationStageSendButtonWidget.setObjectName("rotationStageSendButtonWidget")
        self.gridLayout.addWidget(self.rotationStageSendButtonWidget, 4, 3, 1, 1)
        self.mainPortTextWidgetSend = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainPortTextWidgetSend.sizePolicy().hasHeightForWidth())
        self.mainPortTextWidgetSend.setSizePolicy(sizePolicy)
        self.mainPortTextWidgetSend.setMinimumSize(QtCore.QSize(10, 25))
        self.mainPortTextWidgetSend.setMaximumSize(QtCore.QSize(16777215, 25))
        self.mainPortTextWidgetSend.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.mainPortTextWidgetSend.setPlainText("")
        self.mainPortTextWidgetSend.setObjectName("mainPortTextWidgetSend")
        self.gridLayout.addWidget(self.mainPortTextWidgetSend, 2, 2, 1, 1)
        self.spectrometerSendButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.spectrometerSendButtonWidget.setObjectName("spectrometerSendButtonWidget")
        self.gridLayout.addWidget(self.spectrometerSendButtonWidget, 3, 3, 1, 1)
        self.rotationStageTextWidget = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        self.rotationStageTextWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.rotationStageTextWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rotationStageTextWidget.setObjectName("rotationStageTextWidget")
        self.gridLayout.addWidget(self.rotationStageTextWidget, 4, 1, 1, 1)
        self.mainSendButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.mainSendButtonWidget.setObjectName("mainSendButtonWidget")
        self.gridLayout.addWidget(self.mainSendButtonWidget, 2, 3, 1, 1)
        self.runScriptButtonWidget2 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.runScriptButtonWidget2.setObjectName("runScriptButtonWidget2")
        self.gridLayout.addWidget(self.runScriptButtonWidget2, 7, 3, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.stopButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.stopButtonWidget.setEnabled(False)
        self.stopButtonWidget.setObjectName("stopButtonWidget")
        self.gridLayout.addWidget(self.stopButtonWidget, 7, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 1, 1, 1, 1)
        self.mainPortTextWidget = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainPortTextWidget.sizePolicy().hasHeightForWidth())
        self.mainPortTextWidget.setSizePolicy(sizePolicy)
        self.mainPortTextWidget.setMinimumSize(QtCore.QSize(10, 25))
        self.mainPortTextWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.mainPortTextWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.mainPortTextWidget.setObjectName("mainPortTextWidget")
        self.gridLayout.addWidget(self.mainPortTextWidget, 2, 1, 1, 1)
        self.loadScriptButtonWidget2 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.loadScriptButtonWidget2.setObjectName("loadScriptButtonWidget2")
        self.gridLayout.addWidget(self.loadScriptButtonWidget2, 7, 1, 1, 2)
        self.runScriptButtonWidget1 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.runScriptButtonWidget1.setObjectName("runScriptButtonWidget1")
        self.gridLayout.addWidget(self.runScriptButtonWidget1, 6, 3, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.loadScriptButtonWidget1 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.loadScriptButtonWidget1.setObjectName("loadScriptButtonWidget1")
        self.gridLayout.addWidget(self.loadScriptButtonWidget1, 6, 1, 1, 2)
        self.statusLabel = QtWidgets.QLabel(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(7)
        self.statusLabel.setFont(font)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.gridLayout.addWidget(self.statusLabel, 9, 1, 1, 3)
        self.rotationStageTextWidgetSend = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rotationStageTextWidgetSend.sizePolicy().hasHeightForWidth())
        self.rotationStageTextWidgetSend.setSizePolicy(sizePolicy)
        self.rotationStageTextWidgetSend.setMinimumSize(QtCore.QSize(10, 25))
        self.rotationStageTextWidgetSend.setMaximumSize(QtCore.QSize(16777215, 25))
        self.rotationStageTextWidgetSend.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rotationStageTextWidgetSend.setPlainText("")
        self.rotationStageTextWidgetSend.setObjectName("rotationStageTextWidgetSend")
        self.gridLayout.addWidget(self.rotationStageTextWidgetSend, 4, 2, 1, 1)
        self.runScriptButtonWidget3 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.runScriptButtonWidget3.setObjectName("runScriptButtonWidget3")
        self.gridLayout.addWidget(self.runScriptButtonWidget3, 8, 3, 1, 1)
        self.loadScriptButtonWidget3 = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.loadScriptButtonWidget3.setObjectName("loadScriptButtonWidget3")
        self.gridLayout.addWidget(self.loadScriptButtonWidget3, 8, 1, 1, 2)
        self.extraPortTextWidget = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        self.extraPortTextWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.extraPortTextWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.extraPortTextWidget.setObjectName("extraPortTextWidget")
        self.gridLayout.addWidget(self.extraPortTextWidget, 5, 1, 1, 1)
        self.extraPortTextWidgetSend = QtWidgets.QPlainTextEdit(self.gridLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.extraPortTextWidgetSend.sizePolicy().hasHeightForWidth())
        self.extraPortTextWidgetSend.setSizePolicy(sizePolicy)
        self.extraPortTextWidgetSend.setMinimumSize(QtCore.QSize(10, 25))
        self.extraPortTextWidgetSend.setMaximumSize(QtCore.QSize(16777215, 25))
        self.extraPortTextWidgetSend.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.extraPortTextWidgetSend.setPlainText("")
        self.extraPortTextWidgetSend.setObjectName("extraPortTextWidgetSend")
        self.gridLayout.addWidget(self.extraPortTextWidgetSend, 5, 2, 1, 1)
        self.extraPortSendButtonWidget = QtWidgets.QPushButton(self.gridLayoutWidget)
        self.extraPortSendButtonWidget.setObjectName("extraPortSendButtonWidget")
        self.gridLayout.addWidget(self.extraPortSendButtonWidget, 5, 3, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 5, 0, 1, 1)
        ServerGui.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(ServerGui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 375, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuServer = QtWidgets.QMenu(self.menubar)
        self.menuServer.setObjectName("menuServer")
        ServerGui.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(ServerGui)
        self.statusbar.setObjectName("statusbar")
        ServerGui.setStatusBar(self.statusbar)
        self.action_Quit = QtWidgets.QAction(ServerGui)
        self.action_Quit.setObjectName("action_Quit")
        self.actionStart = QtWidgets.QAction(ServerGui)
        self.actionStart.setEnabled(False)
        self.actionStart.setObjectName("actionStart")
        self.actionStop = QtWidgets.QAction(ServerGui)
        self.actionStop.setEnabled(False)
        self.actionStop.setObjectName("actionStop")
        self.menuFile.addAction(self.action_Quit)
        self.menuServer.addAction(self.actionStart)
        self.menuServer.addAction(self.actionStop)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuServer.menuAction())

        self.retranslateUi(ServerGui)
        QtCore.QMetaObject.connectSlotsByName(ServerGui)

    def retranslateUi(self, ServerGui):
        _translate = QtCore.QCoreApplication.translate
        ServerGui.setWindowTitle(_translate("ServerGui", "MainWindow"))
        self.localAddressTextWidget.setPlainText(_translate("ServerGui", "127.0.0.1"))
        self.spectrometerPortTextWidget.setPlainText(_translate("ServerGui", "10121"))
        self.startButtonWidget.setText(_translate("ServerGui", "Start"))
        self.label.setText(_translate("ServerGui", "Main"))
        self.label_2.setText(_translate("ServerGui", "Spectrometer"))
        self.label_6.setText(_translate("ServerGui", "Message"))
        self.rotationStageSendButtonWidget.setText(_translate("ServerGui", "Send"))
        self.spectrometerSendButtonWidget.setText(_translate("ServerGui", "Send"))
        self.rotationStageTextWidget.setPlainText(_translate("ServerGui", "10123"))
        self.mainSendButtonWidget.setText(_translate("ServerGui", "Send"))
        self.runScriptButtonWidget2.setText(_translate("ServerGui", "Run script"))
        self.label_5.setText(_translate("ServerGui", "Local address"))
        self.stopButtonWidget.setText(_translate("ServerGui", "Stop"))
        self.label_4.setText(_translate("ServerGui", "Port"))
        self.mainPortTextWidget.setPlainText(_translate("ServerGui", "10120"))
        self.loadScriptButtonWidget2.setText(_translate("ServerGui", "Load Script"))
        self.runScriptButtonWidget1.setText(_translate("ServerGui", "Run script"))
        self.label_3.setText(_translate("ServerGui", "RotationStage"))
        self.loadScriptButtonWidget1.setText(_translate("ServerGui", "Load Script"))
        self.runScriptButtonWidget3.setText(_translate("ServerGui", "Run script"))
        self.loadScriptButtonWidget3.setText(_translate("ServerGui", "Load Script"))
        self.extraPortTextWidget.setPlainText(_translate("ServerGui", "10124"))
        self.extraPortSendButtonWidget.setText(_translate("ServerGui", "Send"))
        self.label_7.setText(_translate("ServerGui", "Extra port"))
        self.menuFile.setTitle(_translate("ServerGui", "File"))
        self.menuServer.setTitle(_translate("ServerGui", "Server"))
        self.action_Quit.setText(_translate("ServerGui", "&Quit"))
        self.actionStart.setText(_translate("ServerGui", "&Start"))
        self.actionStop.setText(_translate("ServerGui", "&Stop"))
