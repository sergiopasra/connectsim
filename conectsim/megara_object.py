
import numpy

class MegaraObject(object):
    def __init__(self,data,wavelength,layout='large_compact_bundle',resolution=30000):
        self.data = numpy.asarray(data)
        self.wavelength = wavelength
        self.layout = layout
        self.resolution = resolution

