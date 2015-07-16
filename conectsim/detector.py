'''Module to handle the detector.'''

import logging
from glob import glob

import numpy as np
from scipy.stats import norm as norm_dist

import basenodes

from .device import Device
#from .simulator_utils import create_interpolator

_logger = logging.getLogger('megarasim.detector')

class Rectangle(object):
    def __init__(self,corner_low_left,corner_high_right):
        self.corner_low_left = corner_low_left
        self.corner_high_right = corner_high_right
        self.height = corner_high_right[0] - corner_low_left[0]
        self.width = corner_high_right[1] - corner_low_left[1]

class VirtualDetector(object):
    '''Virtual Detector.'''
    def __init__(self,physical_detector_mapping, bias=1000, gain=1.0 ,read_noise = 2, overscan=['left','right']):
        self.bias = bias
        self.read_noise = read_noise    #virtual detector readout noise in e/px
        self.dark_noise = 0.02/3600.  #detector dark current noise in e/px/s
        self.dark_current = 3/3600. #detector dark current in e/px/s
        self.gain= 1.0
        self.physical_detector_mapping = physical_detector_mapping
        self.overscan = overscan
        self.detector_pos = [0,0]
        self.virtual_size = self.get_overscan_dim()
        self.exposure = np.zeros(self.virtual_size)
    
    def get_overscan_dim(self):
        width = self.physical_detector_mapping.width
        height = self.physical_detector_mapping.height
        if 'bottom' in self.overscan:
            height += 50
            self.detector_pos[0] += 50
        if 'left' in self.overscan:
            width += 50
            self.detector_pos[1] += 50
        if 'right' in self.overscan:
            width += 50
        if 'up' in self.overscan:
            height += 50

        return [height,width]
    
    def read_detector(self,image, exptime):
        '''Readout the detector

        :param image: Image

        '''
        noise = np.sqrt(self.read_noise ** 2 + (self.dark_noise * exptime) ** 2)
        self.exposure = np.random.normal(self.bias + self.dark_current * exptime, noise, self.virtual_size)
        
        virt_x_min = self.detector_pos[0]
        virt_x_max = virt_x_min + self.physical_detector_mapping.height
        virt_y_min = self.detector_pos[1]
        virt_y_max = virt_y_min + self.physical_detector_mapping.width
        image_x_min = self.physical_detector_mapping.corner_low_left[0]
        image_x_max = self.physical_detector_mapping.corner_high_right[0]
        image_y_min = self.physical_detector_mapping.corner_low_left[1]
        image_y_max = self.physical_detector_mapping.corner_high_right[1]
        self.exposure[virt_x_min:virt_x_max,virt_y_min:virt_y_max] += self.gain * image[image_x_min:image_x_max,image_y_min:image_y_max]
    
class VirtualDetectorComposite(object):
    def __init__(self, detectors_array):
        self.detector_array = detectors_array

    def read_detector(self,image,exptime):
        ''' read of all detectors'''
        for detector in self.detector_array.ravel():
            detector.read_detector(image,exptime)
        #(detector.read_detector(image,exptime) for detector in self.detector_array.ravel())
        # concatenate all detectors in single one
        self.exposure = np.concatenate([np.concatenate(np.array([grid.exposure for grid in self.detector_array[i]])) for i in range(self.detector_array.shape[0])],1)


class CDetector(basenodes.Sink, Device):
    def __init__(self, size_x, size_y, pixel_size, qe):
        basenodes.Sink.__init__(self)
        Device.__init__(self, name='detector')
        self.size_x = size_x
        self.size_y = size_y
        self.pixel_size = pixel_size # pixel size in milimeters

        self.det_arr = VirtualDetectorComposite(np.array([[VirtualDetector(Rectangle([0,0],[self.size_y / 2 , self.size_x]), bias = 1005, gain = 1.0, read_noise = 2, overscan=['left','right','up'])
                             ,VirtualDetector(Rectangle([self.size_y / 2, 0],[self.size_y, self.size_x]), bias = 1000, gain = 1.0, read_noise = 2, overscan=['left','right','bottom'])]]))
        self.save_index = 0
        self.transmission_interp = qe
        self.qe = qe

    def set_input(self, input_image):
        self.input_image = input_image

    def expose(self, exptime):
        _logger.debug('Generating poisson noise')
        input_image = np.random.poisson(self.input_image * exptime, self.input_image.shape)
        _logger.debug('Poisson noise generated')
        
        _logger.debug('Reading detector array')
        self.det_arr.read_detector(input_image, exptime)
        _logger.debug('Detector array read')
        _logger.debug('Saturation start.')
        #self.detector_image = self.det_arr.exposure #self.saturation(self.det_arr.exposure)
        self.detector_image = self.saturation(self.det_arr.exposure)
        _logger.debug('Saturation end')
#        _logger.debug('Store image')
#        self.store_image()
#        _logger.debug('Store image')
        return self.detector_image


    def saturation(self, input_image):
        f = lambda x: x - 2*(x - 45000)*(x - 45000)/45000 * (x.astype(int)/45000 - x.astype(int)/55000)
        input_image = f(input_image)
        input_image[input_image>52000] = 52000
        return input_image
