cimport cython
cimport numpy as np
import numpy as np

@cython.boundscheck(False)
def average(array):
    cdef float total, value, average
    cdef int index
    total = 0
    for index,value in enumerate(array):
        total += value
    average = total / (index + 1)
    return average

def updateMultiChannelArray(array, newdata, int numberOfChannels, int samples_to_read_total_per_line, int samples_per_pixel, int x_pixels, int y_pixel_location, int startOffset):
    for channel in range(0,numberOfChannels):
        for x_pixel_location in range(0, x_pixels):
            offset = startOffset
            channel_offset = channel * samples_to_read_total_per_line
            start = x_pixel_location * samples_per_pixel + channel_offset + offset
            end = (x_pixel_location + 1) * samples_per_pixel + channel_offset + offset
            array[channel, y_pixel_location, x_pixel_location] = average(newdata[start:end])
    return array

@cython.boundscheck(False)
def updateArray(array, newdata, int samples_per_pixel, int x_pixels, int y_pixel_location):
    for x_pixel_location in range(x_pixels):
        start = x_pixel_location * samples_per_pixel
        end = (x_pixel_location + 1) * samples_per_pixel
        array[y_pixel_location, x_pixel_location] = average(newdata[start:end])
    return array

@cython.boundscheck(False)
def cupdateArray(np.ndarray[np.float64_t, ndim=2] array, np.ndarray[np.float64_t, ndim=1] newdata, int samples_per_pixel, int x_pixels, int y_pixel_location):
    cdef float total
    cdef int x_pixel_location

    for x_pixel_location in range(x_pixels):
        total = 0
        for value in newdata[x_pixel_location * samples_per_pixel:(x_pixel_location + 1) * samples_per_pixel]:
            total += value
        array[y_pixel_location, x_pixel_location] = total / samples_per_pixel
    return array

@cython.boundscheck(False)
def nupdateArray(np.ndarray[np.float64_t, ndim=2] array, np.ndarray[np.float64_t, ndim=1] newdata, int samples_per_pixel, int x_pixels, int y_pixel_location):
    array[frame, y_pixel_location] = np.mean(newdata.reshape(-1,samples_per_pixel),1)
    return array

@cython.boundscheck(False)
def nmeanArray(np.ndarray[np.float64_t, ndim=3] array):
    mean_array = np.mean(array,axis=0)
    return mean_array

# def calculateDisplay(buffer, int framesToAverage, int y_pixel_location, int *framesDisplayed, scanType, saveFile, lastFrame, reading, array, newdata, int numberOfChannels, int samples_to_read_total_per_line, int samples_per_pixel, int x_pixels, int startOffset):
#    while len(buffer) > 0:
#        data = buffer.pop(0)
#        for frame in range(0, framesToAverage):
#            updateArray(array,data,numberOfChannels,samples_to_read_total_per_line,samples_per_pixel,x_pixels,y_pixel_location,startOffset)

#            y_pixel_location += 1
#            if y_pixel_location >= x_pixels:
#                y_pixel_location = 0
#                saveFile()
#                framesDisplayed += 1

#                if 'Discrete' in scanType:
#                    lastFrame = True

#                if lastFrame:
#                    reading = False