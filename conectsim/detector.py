'''Module to handle the detector.'''

import logging

from .basenodes import Sink
from .device import Device

_logger = logging.getLogger('connectsim.detector')


class CDetector(Sink, Device):
    def __init__(self, size_x, size_y, pixel_size, qe):
        Sink.__init__(self)
        Device.__init__(self, name='detector')
        self.size_x = size_x
        self.size_y = size_y
        self.pixel_size = pixel_size # pixel size in microns
        self.qe = qe

    def set_input(self, input_image):
        self.input_image = input_image

    def expose(self, exptime):
        _logger.debug('Generating poisson noise')

        _logger.debug('Poisson noise generated')
        
        _logger.debug('Reading detector array')
        _logger.debug('Detector array read')
        _logger.debug('Saturation start.')
        _logger.debug('Saturation end')
        return 0.0