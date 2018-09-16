import os
import ctypes
import sys
import tifffile as tf

if sys.maxsize > 2 ** 32:
    def imsave(filename, data, pages=1):
        y, x = data.shape
        return tf.imsave(filename, data, append=True, bigtiff=True)
else :
    def imsave(filename, data):
        return tf.imsave(filename, data, append=True)

    #def addtag(code, dtype, count, value, writeonce=False):