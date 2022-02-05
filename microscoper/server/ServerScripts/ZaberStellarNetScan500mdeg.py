from . import Script
import time
import numpy as np
from PyQt5 import QtWidgets
import os

class script(Script.Script):
    def __init__(self,parent):
        # self is Script.Script
        # parent is Server class
        self.parent = parent

    def start(self):
        self.setFilename()
        self.spectrometerReady()
        self.zaberReady()
        self.startScan()
        self.endScan()

    def setFilename(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        cwd = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        cwd = os.path.join(cwd,'Spectro')
        if not os.path.exists(cwd):
            os.mkdir(cwd)
        # self.filename = os.path.join(cwd,)
        # self.parent.loadFilename()
        # self.filename = self.parent.filename
        # self.filename
        # self.fileName = '%s'%time.time()
        self.filename = os.path.join(cwd,'%s'%(time.time()))
        # self.fileName = ''

    def spectrometerReady(self):
        # self.scriptSend('spectrometer.spectrometer.hideFit()')
        self.scriptSend('spectrometer.spectrometer.setSpectrometerMode()')
        # self.scriptSend('spectrometer.scanning = False')
        # self.scriptSend('spectrometer.realTimeFit = False')
        self.scriptSend('spectrometer.stopFit()')
        self.scriptSend('spectrometer.stopContinuousScan()')

        self.parent.connection.askForResponse(receiver="spectrometer", sender="server", timeout=5)

    def zaberReady(self):
        self.scriptSend('zaber.move_abs(0)')
        time.sleep(1)
        self.parent.connection.askForResponse(receiver="zaber", sender="server", timeout=5)

    def startScan(self):
        self.running = True
        for deg in np.arange(0,45.1,0.5):
                if not self.running : break
                self.index = deg
                self.spectrometerScan()
                self.spectrometerSave()
                self.zaberMove(deg)
                time.sleep(0.1)

    def spectrometerScan(self):
        self.scriptSend('spectrometer.spectrometer.scan(background_subtract=True)')
        self.scriptSend('spectrometer.spectrometer.plot()')
        self.parent.connection.askForResponse(receiver="spectrometer", sender="server", timeout=5)

    def spectrometerSave(self):
        if self.filename is not '':
            self.scriptSend(
                "spectrometer.save(filename=r'%s',label='%.3f',append=True)"
                % (self.filename, self.index))
        self.parent.connection.askForResponse(receiver="spectrometer", sender="server", timeout=5)

    def zaberMove(self,deg):
        self.scriptSend('zaber.move_abs(%.2f)'%deg)
        self.parent.connection.askForResponse(receiver="zaber", sender="server", timeout=5)

    def endScan(self):
        self.zaberMove(0)
        self.scriptSend("spectrometer.endScript()")
        self.scriptSend("server.endScript()")

    def stop(self):
        self.running = False
