import numpy as np

class _sync_parameters(object):
    def __init__(self, resolution=(50, 50), line_dwell_time=2, fill_fraction=0.5, max_timebase_frequency=20e6,
                 tolerance=0.1, divisorD=3, maxbuffer=8192, number_of_channels=1):
        self.x_pixels, self.y_pixels = resolution
        self.msline = line_dwell_time
        self.fill_fraction = fill_fraction
        self.max_timebase_frequency = max_timebase_frequency
        self.tolerance = tolerance
        self.divisorD = divisorD
        self.maxbuffer = maxbuffer
        self.number_of_channels = number_of_channels
        self.calculate()

    def calculate(self):
        ## NI PCI 6110  limitations : samples per tick is limited to 8192
        self.x_pixels_flyback = int(np.floor(self.x_pixels * self.fill_fraction))
        self.x_pixels_total = int(self.x_pixels + self.x_pixels_flyback)
        self.pixel_dwell_time = 1000 * (self.msline) / (self.x_pixels_total)
        self.frequency = (1000 / self.msline)  # np.floor(1000 / self.msline)  # lines_per_second
        self.pixel_read_rate = self.x_pixels_total * self.frequency
        self.divisorG = np.floor(self.max_timebase_frequency / self.pixel_read_rate)

        N = self.tolerance + 1
        while N > self.tolerance:
            self.divisorD += 1
            self.samples_per_pixel = self.divisorG / self.divisorD
            self.samples_to_read_per_channel_per_line = int(self.samples_per_pixel * self.x_pixels_total)
            self.samples_to_read_per_channel = int(self.samples_per_pixel * self.x_pixels_total)

            while self.samples_to_read_per_channel_per_line > self.maxbuffer:
                self.divisorD += 1
                self.samples_per_pixel = self.divisorG / self.divisorD
                self.samples_to_read_per_channel_per_line = int(self.samples_per_pixel * self.x_pixels_total)
                self.samples_to_read_per_channel = int(self.samples_per_pixel * self.x_pixels_total)
            self.samples_to_read_per_line_total = self.samples_to_read_per_channel_per_line*self.number_of_channels
            N = np.mod(self.samples_per_pixel, 1)
            self.read_clock_rate = (self.max_timebase_frequency / self.divisorD)
            self.write_clock_rate = (self.max_timebase_frequency / self.divisorG)

        self.samples_to_write_per_channel = self.x_pixels_total * self.y_pixels
        self.samples_per_pixel = int(self.samples_per_pixel)
        self.samples_trash = self.samples_per_pixel * self.x_pixels_flyback
        self.data_line = np.zeros((self.number_of_channels*self.samples_to_read_per_channel), dtype=np.float64)

class sync_parameters(object):
    def __init__(self, resolution=(50, 50), line_dwell_time=2, fill_fraction=0.5, max_timebase_frequency=20e6,
                 tolerance=0, divisorD=3, maxbuffer=8192, number_of_channels=1):
        self.x_pixels, self.y_pixels = resolution
        self.msline = line_dwell_time
        self.fill_fraction = fill_fraction
        self.max_timebase_frequency = float(max_timebase_frequency)
        self.tolerance = tolerance
        self.divisorD = divisorD
        self.maxbuffer = maxbuffer
        self.number_of_channels = number_of_channels
        self.calculate()

    def calculate(self):
        ## NI PCI 6110  limitations : samples per tick is limited to 8192
        self.x_pixels_flyback = int(np.floor(self.x_pixels * self.fill_fraction))
        Nfly = self.tolerance + 1
        # print("x pixels flyback before: ",self.x_pixels_flyback)
        while Nfly > self.tolerance :

            self.x_pixels_total = int(self.x_pixels + self.x_pixels_flyback)  # x pixels total would be modified
            self.pixel_dwell_time = 1000 * (self.msline) / (self.x_pixels_total)
            self.frequency = (1000 / self.msline)  # np.floor(1000 / self.msline)  # lines_per_second
            self.pixel_read_rate = self.x_pixels_total * self.frequency
            self.divisorG = (self.max_timebase_frequency / self.pixel_read_rate)
            self.pixel_read_rate = self.x_pixels_total * self.frequency
            Nfly = np.mod(self.divisorG, 1)
            if Nfly > self.tolerance :
                self.x_pixels_flyback += 1
        # print("x pixels flyback after: ",self.x_pixels_flyback)
        Nsync = self.tolerance + 1
        ## test
        # self.x_pixels_flyback = 100
        # self.x_pixels_total = 300
        ## ---

        while Nsync > self.tolerance:
            self.divisorD += 1
            self.samples_per_pixel = self.divisorG / self.divisorD
            self.samples_to_read_per_channel_per_line = int(self.samples_per_pixel * self.x_pixels_total)
            self.samples_to_read_per_channel = int(self.samples_per_pixel * self.x_pixels_total)

            while self.samples_to_read_per_channel_per_line > self.maxbuffer:
                self.divisorD += 1
                self.samples_per_pixel = self.divisorG / self.divisorD
                self.samples_to_read_per_channel_per_line = int(self.samples_per_pixel * self.x_pixels_total)
                self.samples_to_read_per_channel = int(self.samples_per_pixel * self.x_pixels_total)
            self.samples_to_read_per_line_total = self.samples_to_read_per_channel_per_line*self.number_of_channels
            Nsync = np.mod(self.samples_per_pixel, 1)
            self.read_clock_rate = (self.max_timebase_frequency / self.divisorD)
            self.write_clock_rate = (self.max_timebase_frequency / self.divisorG)
        # print(self.divisorG,self.read_clock_rate,self.write_clock_rate)

        self.samples_to_write_per_channel = self.x_pixels_total * self.y_pixels
        self.samples_per_pixel = int(self.samples_per_pixel)

        self.samples_trash = self.samples_per_pixel * self.x_pixels_flyback
        self.data_line = np.zeros((self.number_of_channels*self.samples_to_read_per_channel), dtype=np.float64)

        ## test
        # self.x_pixels_flyback = 100
        # self.samples_trash = self.samples_per_pixel * self.x_pixels_flyback
        # self.x_pixels_total = 300
        ## ---



if __name__ == "__main__":
    x = 256
    msline = 2
    ff = 0.5
    maxTimebaseFrequency = 20e6
    hwbuffer = 8192
    numberOfChannels= 2
    parameters = sync_parameters(resolution=(x,x),
                                 line_dwell_time=msline,
                                 fill_fraction=ff,
                                 max_timebase_frequency=maxTimebaseFrequency,
                                 maxbuffer=hwbuffer,
                                 number_of_channels=numberOfChannels)
    print('stuff')