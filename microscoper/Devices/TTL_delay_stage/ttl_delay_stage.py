from Devices.AnalogDigitalOut import Digital_output
import time


class TTL_Delay_Stage:
    def __init__(self, path="/dev1/port0/line0"):
        self.dev = Digital_output(path)

    def toggle_move(self):
        self.dev.high()
        time.sleep(0.1)
        self.dev.low()

    def close(self):
        self.dev.close()
