from numba import njit
import numpy as np


@njit('(f8[::1,::1], f8[::1], i8, i8, i8)', fastmath=True, cache=True)
def updateArray(array, newdata, samples_per_pixel, x_pixels, y_pixel_location):
    for x_pixel_location in range(x_pixels):
        start = x_pixel_location * samples_per_pixel
        end = (x_pixel_location + 1) * samples_per_pixel
        array[y_pixel_location, x_pixel_location] = np.mean(newdata[start:end])
    return array


@njit('(f8[::1, ::1], f8[::1], i8, i8, i8)', fastmath=True, cache=True)
def cupdateArray(array, newdata, samples_per_pixel, x_pixels, y_pixel_location):
    for x_pixel_location in range(x_pixels):
        total = 0
        for value in newdata[x_pixel_location * samples_per_pixel:(x_pixel_location + 1) * samples_per_pixel]:
            total += value
        array[y_pixel_location, x_pixel_location] = total / samples_per_pixel
    return array


# @njit('(f8[::1, ::1], f8[::1], i8, i8, i8)', fastmath=True, cache=True)
def nupdateArray(array, newdata, samples_per_pixel, x_pixels, y_pixel_location):
    array[y_pixel_location] = np.mean(newdata.reshape(-1, samples_per_pixel), 1)
    return array


# @njit('(f8[::1, ::1, ::1])', fastmath=True, cache=True)
def nmeanArray(array):
    mean_array = np.mean(array, axis=0)
    return mean_array
