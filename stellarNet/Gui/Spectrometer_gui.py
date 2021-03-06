# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Spectrometer_gui.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Spectrometer(object):
    def setupUi(self, Spectrometer):
        Spectrometer.setObjectName("Spectrometer")
        Spectrometer.resize(661, 492)
        self.centralwidget = QtWidgets.QWidget(Spectrometer)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem)
        self.saveButton = QtWidgets.QPushButton(self.centralwidget)
        self.saveButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.saveButton.sizePolicy().hasHeightForWidth())
        self.saveButton.setSizePolicy(sizePolicy)
        self.saveButton.setObjectName("saveButton")
        self.verticalLayout.addWidget(self.saveButton)
        self.saveContinuouslyButton = QtWidgets.QPushButton(self.centralwidget)
        self.saveContinuouslyButton.setObjectName("saveContinuouslyButton")
        self.verticalLayout.addWidget(self.saveContinuouslyButton)
        spacerItem1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)
        self.setScanButton = QtWidgets.QPushButton(self.centralwidget)
        self.setScanButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.setScanButton.sizePolicy().hasHeightForWidth())
        self.setScanButton.setSizePolicy(sizePolicy)
        self.setScanButton.setObjectName("setScanButton")
        self.verticalLayout.addWidget(self.setScanButton)
        spacerItem2 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem2)
        self.calibratedButton = QtWidgets.QPushButton(self.centralwidget)
        self.calibratedButton.setObjectName("calibratedButton")
        self.verticalLayout.addWidget(self.calibratedButton)
        self.acqbackgroundButton = QtWidgets.QPushButton(self.centralwidget)
        self.acqbackgroundButton.setObjectName("acqbackgroundButton")
        self.verticalLayout.addWidget(self.acqbackgroundButton)
        self.backgroundButton = QtWidgets.QPushButton(self.centralwidget)
        self.backgroundButton.setObjectName("backgroundButton")
        self.verticalLayout.addWidget(self.backgroundButton)
        spacerItem3 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem3)
        self.yScaleButton = QtWidgets.QPushButton(self.centralwidget)
        self.yScaleButton.setObjectName("yScaleButton")
        self.verticalLayout.addWidget(self.yScaleButton)
        self.autoscaleButton = QtWidgets.QPushButton(self.centralwidget)
        self.autoscaleButton.setObjectName("autoscaleButton")
        self.verticalLayout.addWidget(self.autoscaleButton)
        self.resetScaleButton = QtWidgets.QPushButton(self.centralwidget)
        self.resetScaleButton.setObjectName("resetScaleButton")
        self.verticalLayout.addWidget(self.resetScaleButton)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 2, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.ch2CheckBoxWidget = QtWidgets.QCheckBox(self.centralwidget)
        self.ch2CheckBoxWidget.setChecked(True)
        self.ch2CheckBoxWidget.setAutoExclusive(False)
        self.ch2CheckBoxWidget.setObjectName("ch2CheckBoxWidget")
        self.gridLayout.addWidget(self.ch2CheckBoxWidget, 1, 7, 1, 1)
        self.ch1CheckBoxWidget = QtWidgets.QCheckBox(self.centralwidget)
        self.ch1CheckBoxWidget.setChecked(True)
        self.ch1CheckBoxWidget.setAutoExclusive(False)
        self.ch1CheckBoxWidget.setObjectName("ch1CheckBoxWidget")
        self.gridLayout.addWidget(self.ch1CheckBoxWidget, 1, 6, 1, 1)
        self.ch3CheckBoxWidget = QtWidgets.QCheckBox(self.centralwidget)
        self.ch3CheckBoxWidget.setChecked(True)
        self.ch3CheckBoxWidget.setObjectName("ch3CheckBoxWidget")
        self.gridLayout.addWidget(self.ch3CheckBoxWidget, 1, 8, 1, 1)
        self.fitButton = QtWidgets.QPushButton(self.centralwidget)
        self.fitButton.setMaximumSize(QtCore.QSize(50, 23))
        self.fitButton.setObjectName("fitButton")
        self.gridLayout.addWidget(self.fitButton, 0, 4, 1, 1)
        self.showFitButton = QtWidgets.QPushButton(self.centralwidget)
        self.showFitButton.setEnabled(False)
        self.showFitButton.setMaximumSize(QtCore.QSize(55, 23))
        self.showFitButton.setObjectName("showFitButton")
        self.gridLayout.addWidget(self.showFitButton, 0, 5, 1, 1)
        self.plotNumberComboBox = QtWidgets.QComboBox(self.centralwidget)
        self.plotNumberComboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.plotNumberComboBox.setObjectName("plotNumberComboBox")
        self.gridLayout.addWidget(self.plotNumberComboBox, 1, 4, 1, 2)
        self.smoothing_spinbox = QtWidgets.QSpinBox(self.centralwidget)
        self.smoothing_spinbox.setMinimum(0)
        self.smoothing_spinbox.setMaximum(3)
        self.smoothing_spinbox.setProperty("value", 0)
        self.smoothing_spinbox.setObjectName("smoothing_spinbox")
        self.gridLayout.addWidget(self.smoothing_spinbox, 1, 3, 1, 1)
        self.integration_time_spinbox = QtWidgets.QSpinBox(self.centralwidget)
        self.integration_time_spinbox.setSuffix("")
        self.integration_time_spinbox.setMinimum(10)
        self.integration_time_spinbox.setMaximum(10000)
        self.integration_time_spinbox.setObjectName("integration_time_spinbox")
        self.gridLayout.addWidget(self.integration_time_spinbox, 1, 1, 1, 1)
        self.scans_to_average_label = QtWidgets.QLabel(self.centralwidget)
        self.scans_to_average_label.setObjectName("scans_to_average_label")
        self.gridLayout.addWidget(self.scans_to_average_label, 0, 2, 1, 1)
        self.scans_to_average_spinbox = QtWidgets.QSpinBox(self.centralwidget)
        self.scans_to_average_spinbox.setMinimum(1)
        self.scans_to_average_spinbox.setMaximum(10)
        self.scans_to_average_spinbox.setProperty("value", 1)
        self.scans_to_average_spinbox.setObjectName("scans_to_average_spinbox")
        self.gridLayout.addWidget(self.scans_to_average_spinbox, 1, 2, 1, 1)
        self.integration_time_label = QtWidgets.QLabel(self.centralwidget)
        self.integration_time_label.setObjectName("integration_time_label")
        self.gridLayout.addWidget(self.integration_time_label, 0, 1, 1, 1)
        self.smoothing_label = QtWidgets.QLabel(self.centralwidget)
        self.smoothing_label.setObjectName("smoothing_label")
        self.gridLayout.addWidget(self.smoothing_label, 0, 3, 1, 1)
        self.stitchWavelength_spinbox = QtWidgets.QSpinBox(self.centralwidget)
        self.stitchWavelength_spinbox.setSuffix("")
        self.stitchWavelength_spinbox.setMinimum(10)
        self.stitchWavelength_spinbox.setMaximum(10000)
        self.stitchWavelength_spinbox.setSingleStep(10)
        self.stitchWavelength_spinbox.setProperty("value", 900)
        self.stitchWavelength_spinbox.setObjectName("stitchWavelength_spinbox")
        self.gridLayout.addWidget(self.stitchWavelength_spinbox, 1, 9, 1, 1)
        self.stitchCheckBoxWidget = QtWidgets.QCheckBox(self.centralwidget)
        self.stitchCheckBoxWidget.setChecked(False)
        self.stitchCheckBoxWidget.setObjectName("stitchCheckBoxWidget")
        self.gridLayout.addWidget(self.stitchCheckBoxWidget, 0, 9, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 1, 1, 1)
        self.SpectrometerHandle = QtWidgets.QGridLayout()
        self.SpectrometerHandle.setObjectName("SpectrometerHandle")
        self.gridLayout_2.addLayout(self.SpectrometerHandle, 1, 1, 1, 1)
        self.gridLayout_2.setColumnStretch(1, 2)
        self.gridLayout_2.setRowStretch(1, 2)
        Spectrometer.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Spectrometer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 661, 21))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtWidgets.QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        self.menu_Help = QtWidgets.QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        self.menu_Setup = QtWidgets.QMenu(self.menubar)
        self.menu_Setup.setObjectName("menu_Setup")
        self.menuAcquisition = QtWidgets.QMenu(self.menubar)
        self.menuAcquisition.setObjectName("menuAcquisition")
        self.menuRemote = QtWidgets.QMenu(self.menubar)
        self.menuRemote.setObjectName("menuRemote")
        Spectrometer.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Spectrometer)
        self.statusbar.setObjectName("statusbar")
        Spectrometer.setStatusBar(self.statusbar)
        self.action_Quit = QtWidgets.QAction(Spectrometer)
        self.action_Quit.setObjectName("action_Quit")
        self.action_Save = QtWidgets.QAction(Spectrometer)
        self.action_Save.setObjectName("action_Save")
        self.action_About = QtWidgets.QAction(Spectrometer)
        self.action_About.setObjectName("action_About")
        self.action_ini_file = QtWidgets.QAction(Spectrometer)
        self.action_ini_file.setObjectName("action_ini_file")
        self.action_Load_Calibration_Files = QtWidgets.QAction(Spectrometer)
        self.action_Load_Calibration_Files.setObjectName("action_Load_Calibration_Files")
        self.actionRaman_mode = QtWidgets.QAction(Spectrometer)
        self.actionRaman_mode.setObjectName("actionRaman_mode")
        self.actionRaman_Mode = QtWidgets.QAction(Spectrometer)
        self.actionRaman_Mode.setObjectName("actionRaman_Mode")
        self.actionSpectrometer_Mode = QtWidgets.QAction(Spectrometer)
        self.actionSpectrometer_Mode.setObjectName("actionSpectrometer_Mode")
        self.actionConnect = QtWidgets.QAction(Spectrometer)
        self.actionConnect.setObjectName("actionConnect")
        self.actionDisconnect = QtWidgets.QAction(Spectrometer)
        self.actionDisconnect.setObjectName("actionDisconnect")
        self.action_Set_laser_wavelength = QtWidgets.QAction(Spectrometer)
        self.action_Set_laser_wavelength.setObjectName("action_Set_laser_wavelength")
        self.menu_File.addAction(self.action_Save)
        self.menu_File.addAction(self.action_Quit)
        self.menu_Help.addAction(self.action_About)
        self.menu_Setup.addAction(self.action_ini_file)
        self.menu_Setup.addAction(self.action_Load_Calibration_Files)
        self.menuAcquisition.addAction(self.actionSpectrometer_Mode)
        self.menuAcquisition.addAction(self.actionRaman_Mode)
        self.menuAcquisition.addAction(self.action_Set_laser_wavelength)
        self.menuRemote.addAction(self.actionConnect)
        self.menuRemote.addAction(self.actionDisconnect)
        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menuAcquisition.menuAction())
        self.menubar.addAction(self.menu_Setup.menuAction())
        self.menubar.addAction(self.menuRemote.menuAction())
        self.menubar.addAction(self.menu_Help.menuAction())

        self.retranslateUi(Spectrometer)
        QtCore.QMetaObject.connectSlotsByName(Spectrometer)

    def retranslateUi(self, Spectrometer):
        _translate = QtCore.QCoreApplication.translate
        Spectrometer.setWindowTitle(_translate("Spectrometer", "MainWindow"))
        self.saveButton.setText(_translate("Spectrometer", "Save"))
        self.saveContinuouslyButton.setText(_translate("Spectrometer", "Save Continuously"))
        self.setScanButton.setText(_translate("Spectrometer", "Start Scan"))
        self.calibratedButton.setText(_translate("Spectrometer", "Load Calibration"))
        self.acqbackgroundButton.setText(_translate("Spectrometer", "Acq Background"))
        self.backgroundButton.setText(_translate("Spectrometer", "Load background"))
        self.yScaleButton.setText(_translate("Spectrometer", "Y scale"))
        self.autoscaleButton.setText(_translate("Spectrometer", "Autoscale"))
        self.resetScaleButton.setText(_translate("Spectrometer", "Reset scale"))
        self.ch2CheckBoxWidget.setText(_translate("Spectrometer", "2"))
        self.ch1CheckBoxWidget.setText(_translate("Spectrometer", "1"))
        self.ch3CheckBoxWidget.setText(_translate("Spectrometer", "3"))
        self.fitButton.setText(_translate("Spectrometer", "Fit"))
        self.showFitButton.setText(_translate("Spectrometer", "Show Fit"))
        self.scans_to_average_label.setText(_translate("Spectrometer", "Frames to Average"))
        self.integration_time_label.setText(_translate("Spectrometer", "Integration Time (ms)"))
        self.smoothing_label.setText(_translate("Spectrometer", "Smoothing"))
        self.stitchCheckBoxWidget.setText(_translate("Spectrometer", "Stitch"))
        self.menu_File.setTitle(_translate("Spectrometer", "&File"))
        self.menu_Help.setTitle(_translate("Spectrometer", "&Help"))
        self.menu_Setup.setTitle(_translate("Spectrometer", "&Setup"))
        self.menuAcquisition.setTitle(_translate("Spectrometer", "Acquisition"))
        self.menuRemote.setTitle(_translate("Spectrometer", "&Remote"))
        self.action_Quit.setText(_translate("Spectrometer", "&Quit"))
        self.action_Save.setText(_translate("Spectrometer", "&Save"))
        self.action_About.setText(_translate("Spectrometer", "&About"))
        self.action_ini_file.setText(_translate("Spectrometer", "&.ini file"))
        self.action_Load_Calibration_Files.setText(_translate("Spectrometer", "&Load Calibration Files"))
        self.actionRaman_mode.setText(_translate("Spectrometer", "Raman mode"))
        self.actionRaman_Mode.setText(_translate("Spectrometer", "Raman Mode"))
        self.actionSpectrometer_Mode.setText(_translate("Spectrometer", "Spectrometer Mode"))
        self.actionConnect.setText(_translate("Spectrometer", "&Connect"))
        self.actionDisconnect.setText(_translate("Spectrometer", "&Disconnect"))
        self.action_Set_laser_wavelength.setText(_translate("Spectrometer", "&Set laser wavelength"))

