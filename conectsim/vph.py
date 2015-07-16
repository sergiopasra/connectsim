
import os

import numpy as np
from scipy import interpolate

from .optelement import OpticalElement
from .simulator_utils import create_interpolator

import logging

_logger = logging.getLogger('megarasim.vph')


    
class VphInterpolators(object):
    def create_interpolators(self, vph, detector):
        pass

class VphSimpleInterpolator(VphInterpolators):
    def create_interpolators(self, vph, detector, slit):
        x = vph.fiber_initial_position
        y = vph.trace_horizontal_position
        z_sp = vph.trace_vertical_position
        z_wl = vph.wavelength_distortion
       
        #detector_size = detector.size
        pixel_size = detector.pixel_size
        #detector_half_size = detector_size / 2
        slit_pos = np.linspace(slit.pos_min, slit.pos_max,100)
        
        y = detector.size_x / 2 - y / pixel_size
        z_sp = detector.size_y / 2 - z_sp / pixel_size
        
        pixels = np.linspace(0,detector.size_x,100)
        dist_matrix_sp = np.zeros([100,len(x)])
        full_dist_matrix_sp = np.zeros([100,100])
        dist_matrix_wl = np.zeros([100,len(x)])
        full_dist_matrix_wl = np.zeros([100,100])
        
        _logger.debug('Interpolators: First loop')
        for i in range(len(x)):
            interp_sp = interpolate.UnivariateSpline(y[:,i],z_sp[:,i], k=3, s=0)
            interp_wl = interpolate.UnivariateSpline(y[:,i],z_wl, k=3, s=0)
            dist_matrix_sp[:,i] = interp_sp(pixels)
            dist_matrix_wl[:,i] = interp_wl(pixels)
            
        _logger.debug('Interpolators: Second loop')
        for i in range(100):
            interp_sp = interpolate.UnivariateSpline(x,dist_matrix_sp[i,:], k=3, s=0)
            interp_wl = interpolate.UnivariateSpline(x,dist_matrix_wl[i,:], k=3, s=0)
            full_dist_matrix_sp[:,i] = interp_sp(slit_pos)
            full_dist_matrix_wl[:,i] = interp_wl(slit_pos)
       
        _logger.debug('Interpolators: 2D Interpolation')
        pixels_aux_1,pixels_aux_2 = np.mgrid[slit.pos_min:slit.pos_max:100j,0:detector.size_x:100j]
        spatial_distortion_interpolator = lambda x,y: interpolate.griddata((pixels_aux_1.ravel(),pixels_aux_2.ravel()), full_dist_matrix_sp.ravel(), (y,x), method='cubic')
        wavelength_distortion_interpolator = lambda x,y: interpolate.griddata((pixels_aux_1.ravel(),pixels_aux_2.ravel()), full_dist_matrix_wl.ravel(), (y,x), method='cubic')
        
        _logger.debug('Interpolators: Interpolators finished.')
        return spatial_distortion_interpolator, wavelength_distortion_interpolator

def vph_builder(vph_conf):
    '''Create a VPHGrating object from the contents of the conf file.'''
    resolution_file = os.path.join(vph_conf['datadir'], vph_conf['resolution'])
    res_func = load_resolution(resolution_file)

    transmission_file = os.path.join(vph_conf['datadir'], vph_conf['transmission'])
    transmission=create_interpolator(transmission_file)

    distortion_file = os.path.join(vph_conf['datadir'], vph_conf['distortion'])
    distortion_data = load_distortion_data(distortion_file)
    name = vph_conf['name']

    _logger.debug('%s:initializing...',name)
    vph = VPHGrating(transmission, distortion_data, res_func, name)
    _logger.debug('%s:Successful initialization.',name)
    return vph

def load_distortion_data(distortion_file):
    _logger.debug('%s:Loading distortion data...', distortion_file)
    vph = np.loadtxt(distortion_file)
    wavelength_distortion = np.unique(vph[:,1])*10000
    fib = np.unique(vph[:,0])
    fiber_initial_position = np.hstack((-fib[:-len(fib):-1],fib))
    trace_v = vph[:,3].reshape(len(fib),len(wavelength_distortion)).transpose()
    trace_vertical_position = np.hstack((-trace_v[:,:-len(fib):-1],trace_v))
    trace_h = vph[:,2].reshape(len(fib),len(wavelength_distortion)).transpose()
    trace_horizontal_position = np.hstack((trace_h[:,:-len(fib):-1],trace_h))               
    _logger.debug('%s:Distortion data loaded.', distortion_file)
    
    # FIXME, ugly hack, return just a tuple FTM

    return wavelength_distortion, fiber_initial_position, trace_vertical_position, trace_horizontal_position
        

def load_resolution(resolution_file):
    ''' 
    Load the resolution dependence with the position on the detector
    '''
    _logger.debug('Loading spectral resolution data from %s', resolution_file)
    vph = np.loadtxt(resolution_file) 
    
    # FIXME: Change to cubic interpolation when the real data arrive
    # there are just three points per file
    #
    resolution_interpolator = interpolate.interp1d(vph[:,0], vph[:,1], 'linear', bounds_error= False, fill_value=vph[0,1])
    return resolution_interpolator

class VPHGrating(OpticalElement):
    '''Volume-Phase Holographic (VPH) Grating.'''
    def __init__(self, transmission, distortion_data, resolution, name):
        self.vph_interpolator = VphSimpleInterpolator()
        #self.name = name
        #self.wavelength_distortion_interpolator = None
        #self.spatial_distortion_interpolator = None

        # FIXME: really ugly hack
        # distortion_data is a structure
        self.wavelength_distortion, self.fiber_initial_position, self.trace_vertical_position, self.trace_horizontal_position = distortion_data

        # This is a function now
        self.resolution_interpolator = resolution

        super(VPHGrating, self).__init__(transmission, name=name)

    def __str__(self):
        return "VPHGrating(name='%s')" % self.name
    
    def __repr__(self):
        return "VPHGrating(name='%s')" % self.name
        
    def create_distortion_interpolators(self, detector, slit):
        '''
        temporary function to create the spatial distortion interpolator in 2D
        it returns a function f(x,y) being x the horizontal pixel in the detector and y the fiber podtion on the Slit
        '''
        self.spatial_distortion_interpolator, self.wavelength_distortion_interpolator = self.vph_interpolator.create_interpolators(self, detector, slit)

