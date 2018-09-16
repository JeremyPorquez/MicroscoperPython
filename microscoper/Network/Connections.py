from .Response import Responder
from multiprocessing.connection import Client, Listener
from threading import Thread
from PyQt5 import QtWidgets, QtCore
import time

class clientObject(Responder):

    class ConnectionSignal(QtCore.QObject):
        connectionLost = QtCore.pyqtSignal()

    def __init__(self,parent=None):
        self.parent = parent
        self.connection = None
        self.isConnected = False
        self.verbose = True
        self.clientConnection = None
        self.autoConnectEnabled = False
        self.connectionIsBusy = False
        self.connectionSignal = self.ConnectionSignal()

    def autoConnect(self,connectionPort=None):
        self.autoConnectEnabled = True
        if connectionPort is not None:
            self.clientConnectionPort = int(connectionPort)
        def connect():
            print("Connecting to address 127.0.0.1:%s" % (self.clientConnectionPort))
            while self.autoConnectEnabled:
                if not self.isConnected:
                    try:
                        if not self.isConnected:
                            self.startClient()
                            self.verbose = True
                            break
                    except Exception as e:
                        if self.verbose :
                            if not self.isConnected:
                                print("Error in clientObject.autoConnect.connect : {0}".format(e))
                                self.verbose = False

                    time.sleep(0.1)
        ## todo : fix errors in stoping and starting server

        connectThread = Thread(target=connect)
        connectThread.daemon = True
        connectThread.start()

    def getReceiver(self,message):
        receiver = message[:message.find(".")]
        return receiver

    def getCommand(self,message):
        command = message[message.find("."):]
        return command

    def listener(self):
        while self.isConnected:
            try:
                self.recvMessage = self.clientConnection.recv()
                print(r'Remote executing %s' % self.recvMessage)
                try:
                    if self.parent is not None:
                        exec('self.parent%s'%self.getCommand(self.recvMessage))
                    else:
                        exec(self.recvMessage)

                except Exception as e:
                    print('Unable to execute %s. Error : %s' % (self.recvMessage, e))
            except:
                print('Listener connection lost')
                self.isConnected = False
                self.connectionSignal.connectionLost.emit()
                self.autoConnect(self.clientConnectionPort)

    def sendConnectionMessage(self,message=None):
        '''Send the message'''
        if self.clientConnection is not None:
            try : self.clientConnection.send(message)
            except ConnectionError as e : print('Connection error : %s'%e)
            except OSError as e : print(e)
        else :
            print('Client connection not initiated.')

    def startClient(self,connectionPort=None):
        if connectionPort is not None:
            self.clientConnectionPort = connectionPort
        address = ("127.0.0.1",int(self.clientConnectionPort))
        self.clientConnection = Client(address, authkey=b"mICROSC0PER")
        print('Connected to address : ', address)
        self.isConnected = True
        Thread(target=self.listener).start()

    def startClientConnection(self,start=False):
        port, accept = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                        'Enter port :')
        if accept :
            self.clientConnectionPort = port
        if start :
            self.startClient()
        return port

    def stopClientConnection(self):
        self.isConnected = False
        self.autoConnectEnabled = False
        if self.clientConnection is not None :
            self.clientConnection.close()