import time

class Responder(object):
    '''A subclass of clientObject'''


    def __init__(self,parent=None):
        self.parent = parent

    def askedForResponse(self, sender=None, question=None, target=None, verbose=True):
        sender = None if sender == 'None' else sender
        question = None if question == 'None' else question
        target = None if target == 'None' else target

        if sender is not None:
            while self.connectionIsBusy:
                time.sleep(0.1)

            if (question is not None) & (target is not None):
                if 'self.' in target :
                    target = target[target.find('.')+1:]
                answer = eval(question) ## check if this works
                response = "%s.%s = %s"%(sender,target,answer)
                self.sendConnectionMessage(response)
                while self.connectionIsBusy:
                    time.sleep(0.1)

            message = "%s.connection.receiveResponse()" % sender
            self.sendConnectionMessage(message)
            if verbose:
                print('Response sent')

    def askForResponse(self, receiver=None, sender=None, question=None, target=None, wait=True, timeout=5, verbose=True):
        hasTimedOut = False
        self.connectionIsWaitingForReponse = wait
        time_initial = time.time()

        # message = "%s.askedForResponse(sender='%s')" % (receiver, sender)
        message = "%s.connection.askedForResponse(sender='%s',question='%s',target='%s')" % (receiver, sender, question, target)
        if verbose:
            print(message)
        self.sendConnectionMessage(message)
        if verbose:
            print('Asking for response from %s' % receiver)
        if (receiver is not None) & (sender is not None):
            while self.connectionIsWaitingForReponse:
                time.sleep(0.1)
                time_elapsed = time.time() - time_initial
                if time_elapsed > timeout:
                    if verbose:
                        print('Asking for response timeout %i seconds' % timeout)
                    hasTimedOut = True
                    break
        if not hasTimedOut:
            if verbose:
                print('Response received from %s' % receiver)

    def receiveResponse(self):
        self.connectionIsWaitingForReponse = False