import time

def detectScanStatus(currentPosition, endPosition, scanInterrupt=False):
    scanInterrupt = False

    def stageContinuousUntilEnds():
        if self.scanStage == "LinearStage":
            self.LinearStage.SetStartScan()
        elif self.scanStage == "zStage":
            self.zStage.SetStartScan()
        while ((abs(self.LinearStage.currentPosition - self.LinearStage.endScanPosition) > 1e-4) and (
        not scanInterrupt)) \
                or (self.LinearStage.currentPosition < self.LinearStage.endScanPosition):
            time.sleep(0.1)
        else:
            self.acquire_stop()
            self.setStage()

    def stageDiscreteUntilEnds():
        while (self.LinearStage.currentPosition < self.LinearStage.endScanPosition) and (
        not scanInterrupt):
            if not self.ai.reading:
                self.acquire_soft_stop()
                self.LinearStage.MoveAbs(self.LinearStage.currentPosition + self.LinearStage.MoveDef.value())
                while not self.LinearStage.positionStageOK:
                    time.sleep(0.1)
                time.sleep(1)
                self.acquire_soft_start()
            time.sleep(0.1)
        self.acquire_stop()
        self.setStage()
        self.set_connection_not_busy()

    def zDiscreteUntilEnds():
        while (self.zStage.currentPosition < self.zStage.endScanPosition) and (not scanInterrupt):
            if not self.ai.reading:
                self.acquire_soft_stop()
                targetPosition = self.ui.ZStageStart.value() + self.stageMoveIndex * self.zStage.MoveDef.value()
                self.stageMoveIndex += 1
                self.zStage.MoveAbs(targetPosition)
                while self.zStage.moving:
                    time.sleep(0.1)
                time.sleep(1)
                self.acquire_soft_start()
            time.sleep(0.1)
        else:
            self.acquire_stop()
            self.set_connection_not_busy()

    def grab():
        while True:
            time.sleep(0.1)
            if not self.ai.reading:
                self.acquire_stop()
                self.set_connection_not_busy()
                break

    def stageDefault():
        self.connection.connectionIsBusy = False

    if self.scan_move_type == "None": stageDefault()
    if self.scan_move_type == "Continuous": stageContinuousUntilEnds()
    if self.scan_move_type == "Discrete":
        self.stageStartPosition = self.ui.LStageStart.value()
        self.stageMoveIndex = 1
        if self.scanStage == "LinearStage": stageDiscreteUntilEnds()
        if self.scanStage == "zStage": zDiscreteUntilEnds()
    if self.scan_move_type == "Grab":
        grab()