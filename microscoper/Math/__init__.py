import numpy as np

def gaussianFunction(x,A=1,x0=0,sigma=1):
    y = A*np.exp(-((x-x0)**2)/(2*sigma**2))
    return y

def sawtooth(pixels=50,repeat_per_point=1):
    dx = 1 / (pixels - 1)
    result = []
    for i in range(0,pixels):
        for j in range(0,repeat_per_point):
            result.append(i * dx)
    result = np.array(result)
    return result

def generateRasterScan(amplitude=16,x_pixels=256,y_pixels=256,x_flyback=128,offset=[0,0]):
    x_pixels_total = x_pixels + x_flyback
    x_axis_raw = generateAxisScan(amplitude,x_pixels,offset[0])
    x_axis_flyback = generateFlyback(amplitude,x_pixels,x_flyback,offset[0])
    data_x = np.tile(np.concatenate((x_axis_flyback,x_axis_raw)),y_pixels)
    data_y = - amplitude * sawtooth(y_pixels, repeat_per_point=x_pixels_total) + amplitude/2 + offset[1]
    data_x[data_x < -10] = -10
    data_x[data_x > 10] = 10
    data_y[data_y < -10] = -10
    data_y[data_y > 10] = 10
    print('X xcanning from %.2f to %.2f' % (np.min(data_x), np.max(data_x)))
    print('Y xcanning from %.2f to %.2f' % (np.min(data_y), np.max(data_y)))
    return np.array([data_x,data_y])

def generateAxisScan(amplitude=16,pixels=256,offset=0):
    delta = amplitude/(pixels - 1)
    min = offset - amplitude / 2.
    fastArray = np.array([i * delta + min for i in range(pixels)])
    return fastArray

def generateFlyback(amplitude=16,pixels=256,flyback=128,offset=0):
    delta = amplitude/(pixels - 1)
    min = offset - amplitude/2.
    max = offset + amplitude/2.
    flybackArray = np.array([min + (i - flyback) * delta for i in range(flyback)])
    flybackArray[flybackArray < min - 2] = min - 2
    flybackArray[flybackArray > max + 2] = max + 2
    return flybackArray


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    x_pixels = 256
    y_pixels = 256
    repeats = 3
    # x_raster = np.tile(sawtooth(x_pixels,repeat_per_point=repeats),y_pixels)
    # y_raster = -sawtooth(y_pixels,repeat_per_point=x_pixels*repeats) + 1
    # plt.plot(x_raster,'.')
    # plt.plot(y_raster,'x')

    # flyback = generateFlyback()
    # x_scan = generateAxisScan()
    # y_scan = - 16 * sawtooth(y_pixels, repeat_per_point=x_pixels+128) + 16/2
    # plt.plot(np.tile(np.concatenate((flyback,x_scan)),256))
    # plt.plot(y_scan)

    x,y = generateRasterScan()
    plt.plot(x)
    plt.plot(y)

    plt.show()