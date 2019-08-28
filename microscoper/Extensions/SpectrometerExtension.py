import time

class Spectrometer:
    '''Contains message protocols that connect to the Spectrometer class and its subclasses.'''
    def __init__(self,parent=None):
        self.parent = parent
        self.waitingForResponse = False
        pass

    def scan(self):
        time.sleep(1)
        self.parent.connection.sendConnectionMessage("spectrometer.spectrometer.scan(background_subtract=False)")
        self.parent.connection.sendConnectionMessage("spectrometer.spectrometer.plot()")
        time.sleep(0.5)

    def save(self, fileName=None, xAxis=None):
        if xAxis is None :
            xAxis = lambda : None
        if fileName is not '':
            self.parent.connection.sendConnectionMessage(
                "spectrometer.save(filename=r'%s',label='%.3f',append=True)"
                % (fileName, xAxis[0]()))
        # time.sleep(self.spectrometer.device_count * self.spectrometer.integration_time / 1000)
        time.sleep(0.1)

    def endScan(self):
        if self.parent is not None :
            if self.parent.scanDetector == "Spectrometer":
                self.parent.connection.sendConnectionMessage('spectrometer.fileLoaded = False')
        else :
            raise ValueError('self.parent must be set')