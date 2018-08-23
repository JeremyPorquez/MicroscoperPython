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
        self.microscopeReady()
        self.zaberReady()
        self.startScan()
        self.endScan()

    def microscopeReady(self):
        self.scriptSend('main.ui.scanTypeWidget.setCurrentIndex(1)')
        self.parent.connection.askForResponse(receiver="main", sender="server", timeout=5)

    def startScan(self):
        self.running = True
        for deg in np.arange(0,181,4):
                if not self.running : break
                filename = f'{deg} deg'
                self.scriptSend(f"main.ui.FilenameText.setText('{filename}')")
                self.zaberMove(deg)
                time.sleep(1)
                self.scriptSend('main.signal.scanStartAcquire.emit()')
                self.scriptSend('main.setConnectionIsBusy()')
                time.sleep(1)
                self.parent.connection.askForResponse(receiver="main", sender="server", timeout=9999)

    def endScan(self):
        self.zaberMove(0)
        self.scriptSend("server.endScript()")

    def stop(self):
        self.running = False

    def zaberReady(self):
        self.scriptSend('zaber.move_abs(0)')
        time.sleep(1)
        self.parent.connection.askForResponse(receiver="zaber", sender="server", timeout=5)

    def zaberMove(self,deg):
        self.scriptSend('zaber.move_abs(%.2f)'%deg)
        self.parent.connection.askForResponse(receiver="zaber", sender="server", timeout=5)