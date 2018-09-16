def getReceiver(message):
    receiver = message[:message.find(".")]
    return receiver

def getCommand(message):
    command = message[message.find("."):]
    return command

class Script(object):
    def __init__(self,parent):
        self.parent = parent # parent is the Server class

    def start(self):
        pass

    def stop(self):
        pass

    def scriptSend(self,msg=None): # should have the same format as sendMessage in Server.py
        receiver = getReceiver(msg)
        command = getCommand(msg)
        if msg is not None:
            for server in self.parent.servers:
                if server.name == receiver:
                    if "self" not in msg:
                        new_msg = "self%s" % command
                    server.serverConnection.send(new_msg)
                    print("%s sent as %s" % (new_msg, msg))