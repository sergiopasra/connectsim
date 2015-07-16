
import numpy as np
from scipy import interpolate, integrate
#from scipy.ndimage.filters import convolve1d as image_convolve

from .simulator_utils import Hex

class FiberBundle(object):
    '''Class representing the MEGARA observing Layout: SCL, LCB or MOS. '''
    
    def __init__(self, name, positions_on_space, positions_on_detector, size, fwhm):
        ''' Layout initialization.
        
        Creates the projection kernel and initializes the Cover. 
        '''
        self.name = name
        self.size = size
        self.fwhm = fwhm
        
        # these values are sampled, not interpolated
        self.positions_on_space = positions_on_space
        self.positions_on_detector = positions_on_detector

        self.shape = Hex(self.size)
        kernel_seed = lambda x: np.exp(-(x**2)/(2*(self.fwhm/2.3548)**2))

        def kernel_seed(x):
            return np.exp(-(x**2)/(2*(self.fwhm/2.3548)**2))

        self.projection_kernel=np.array([integrate.quad(kernel_seed,i,i+1)[0]/integrate.quad(kernel_seed,-10,10)[0] for i in range(-5,6)])
         
    def get_fiber_positions_on_space(self, cover):
        ''' Return the array of fiber positions on space taking into account the Cover state '''
        return self.positions_on_space[cover(self.positions_on_space)]
    
    def get_fiber_positions_on_detector(self, cover):
        ''' Return the array of fiber positions on the detector taking into account the Cover state '''
        return self.positions_on_detector[cover(self.positions_on_space)]
    
    def __repr__(self):
        return "FiberBundle(name='%s')" % self.name
