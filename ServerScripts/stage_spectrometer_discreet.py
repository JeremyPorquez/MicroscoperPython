from . import Script

class script(Script.Script):
    def __init__(self,parent):
        self.parent = parent

    def start(self):
        # print('test')
        self.setScanType()
        self.setAcquire()

    def setScanType(self):
        self.send('main',"self.setScanType('grab wait')")

    def setAcquire(self):
        self.send('main','self.acquireSet()')



