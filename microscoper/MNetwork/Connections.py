from .Response import Responder
from multiprocessing.connection import Client, Listener
from threading import Thread
from PyQt5 import QtWidgets, QtCore
import time

class ClientObject(Responder):

    errorPrinted = False

    class ConnectionSignal(QtCore.QObject):
        connectionLost = QtCore.pyqtSignal()

    def __init__(self,parent=None, verbose=False):
        self.parent = parent
        self.connection = self                          # avoids ambiguity in parent, connection heirarchy
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
                try :
                    self.startClient()                  # try to start client
                    self.errorPrinted = False           # restart error message
                except Exception as e:                  # if client fails to start, try again
                    if not self.errorPrinted:           # prints an error message why it failed to start
                        self.errorPrinted = True
                        print(e)

                time.sleep(0.1)

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
                self.recvMessage = self.clientConnection.recv()     # Waits to receive something.
                if not self.recvMessage:                            # Receive nothing? client closed connection,
                    break
                print(r'Remote executing %s' % self.recvMessage)    # Prints received message

                try:                                                # Tries to execute received message
                    recvMessage = self.recvMessage
                    if self.parent is not None:                          # Fix command inheritance
                        if "self.parent" not in recvMessage:
                            indexSelf = recvMessage.find("self.")
                            if indexSelf == -1: # no self found
                                recvMessage = "self.%s" % recvMessage
                            indexParent = recvMessage.find("parent.")
                            if indexParent == -1: # no parent found
                                recvMessage = "self.parent.%s"%recvMessage[len("self."):]
                    exec(recvMessage)
                except Exception as e:
                    print('Unable to execute %s. Error : %s' % (self.recvMessage, e))
            except Exception as e:
                if not self.errorPrinted:
                    print(e)
                    self.errorPrinted = True

        print('Listener connection lost')
        self.clientConnection.close()
        self.isConnected = False
        self.connectionSignal.connectionLost.emit()

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