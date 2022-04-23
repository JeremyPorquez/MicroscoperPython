import unittest
from Devices.TTL_delay_stage import TTL_Delay_Stage
import time


class MyTestCase(unittest.TestCase):
    def test_move(self):
        stage = TTL_Delay_Stage("/dev1/port0/line0")
        for i in range(10):
            stage.toggle_move()
            time.sleep(1)


if __name__ == '__main__':
    unittest.main()
