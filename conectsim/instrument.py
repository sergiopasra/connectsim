
import logging
import math

import numpy as np
from scipy import interpolate, integrate
from scipy.ndimage.filters import convolve1d as image_convolve

from .pseudoslit import Slit
from .simulator_utils import create_interpolator
from .simulator_utils import apply_distortion
from .megara_object import MegaraObject
from .astrophysics_unit import ergscm2aaarcsec2photonsm2nmarcsec2
from .das import DataAdquisitionSystem
from .cover import C_Cover
from .device import Device
from .factory import MegaraImageFactory
from .shutter import MEGARA_Shutter
from .optelement import OpticalElement
from .calibration import CalibrationUnitSelector, LampCarrousel
from .optelement import Stop, Open, Filter

_logger = logging.getLogger('connectsim')

class GenericCOptics(OpticalElement):
    '''Generic MEGARA optics transmission. '''
    def __init__(self, transmission_file):
        self.transmission_interp = create_interpolator(transmission_file)
        super(GenericCOptics, self).__init__(self.transmission_interp, name="generic")


class C_Device(Device):
    ''' Class that handles all MEGARA components and operations. ''' 
    def __init__(self, fibers, optics, wheel, detector, telescope, pslit, focal_plane):

        super(C_Device, self).__init__(name='megara')

        # Devices in the light path
        self.telescope = telescope

        # Setup calibration unit
        # One open position
        openentry = Open(name='CUOFF')
        self.cuselector = CalibrationUnitSelector(parent=self)
        self.cuselector.put_in_pos(openentry, 0)
        # One calibration with continnum lamps
        cal_unit1 = LampCarrousel(capacity=3, name='a', parent=self.cuselector)
        cal_unit1.put_in_pos(Stop(name='LAMP0'), 0)
        cal_unit1.put_in_pos(Stop(name='LAMP1'), 1)

        self.cuselector.put_in_pos(cal_unit1, 1)
        # One calibration with arc lamps
        cal_unit2 = LampCarrousel(capacity=2, name='b', parent=self.cuselector)
        cal_unit2.put_in_pos(Stop(name='ARC0'), 0)
        cal_unit2.put_in_pos(Stop(name='ARC1'), 1)
        self.cuselector.put_in_pos(cal_unit2, 2)

        self.cover = C_Cover(parent=self) # Cover
        self.foc_plane = focal_plane # The focal plane
        self.fibers = fibers # Fibers
        self.pslit = pslit # Select the bundle that goes to the PseudoSlit
        self.pslit.set_parent(self)
        self.slit = Slit() # The PseudoSlit?
        self.optics = optics # Internal optics
        self.shutter = MEGARA_Shutter(parent=self) # Internal shutter
        self.wheel = wheel # VPH Wheel (+ VPHs)
        self.wheel.set_parent(self)
        self.detector = detector # Detector
        self.detector.set_parent(self)
        self.das = DataAdquisitionSystem(self.detector) # Detector control
        self.das.set_parent(self)

        # How do we create MEGARA images
        self.image_factory = MegaraImageFactory()

        # The selected VPH
        self.vph = self.wheel.current()
        # The selected fiber bundle (or else)
        self.layout = self.pslit.current()

        # Callbacks get called on predefined events on the devices
        # A callback to maintain self.vph updated
    	# whenever the wheel is moved
        def update_current_vph(_):
            self.vph = self.wheel.current()

        self.wheel.changed.connect(update_current_vph)

        # Operations whenever the fiber bundle feed into
    	# the pseudo slit changes
        def update_current_bundle(_):
            self.layout = self.pslit.current()
            if self.layout is not None:
                self.foc_plane.set_layout(self.layout)

        self.pslit.changed.connect(update_current_bundle)

        # Set an "order sorting filter" with the red vphs
        
        #def insert_order_sorting_filter(pos):
        #    c = self.wheel.current()
        #    if c.name in ['VPH890_LR']:
        #        _logger.debug('Inserting order sorting filter for %s', c.name)
        #        self.shutter.filter()
        #     
        #self.wheel.moved.connect(insert_order_sorting_filter)

        self.transmission_interp = None
        
        # Light path
        self.telescope.connect(openentry)

        self.cuselector.connect(self.cover)
        self.cover.connect(self.pslit)
        self.pslit.connect(self.shutter)
        #
        self.shutter.connect(self.optics)
        self.optics.connect(self.wheel)
        self.wheel.connect(detector)
        
    def config_info(self):
        '''Return the configuration information of MEGARA.'''
        info = {}
        for dev in self.children:
            info[dev.name] = dev.config_info()
        return info

    def _change_vph(self, name):
        _logger.debug('Changing VPH to %s', name)
        self.wheel.select(name)

    def _set_cover_state(self, state):
        _logger.debug('Changing cover to %s', state)
        self.cover.set(state)
        self.foc_plane.to_update = True

    def _change_layout(self, layout_name):
        _logger.debug('Changing fiber bundle to %s', layout_name)
        self.pslit.select(layout_name)

    def _change_cu(self, cu, lamp):
        self.cuselector.select('CUOFF')

    def factory(self, meta, finaldata):
        hdul = self.image_factory.create(meta, finaldata)
        return hdul

    def configure(self, profile):
        '''Configure MEGARA.'''
        _logger.debug('Configure MEGARA with profile %s', profile['description'])
        self.shutter.configure(profile['shutter'])
        self._set_cover_state(profile['cover'])
        self._change_layout(profile['bundle'])
        self._change_vph(profile['vph'])
        self._change_cu(1, 1)
        _logger.info('Path of the light %s', self.detector.trace())
        self.cuselector.print_from_the_begining()
        import sys
        sys.exit()

class Connecttt(C_Device):
    ''' Class that handles all MEGARA components and operations. ''' 
    def __init__(self, fibers, optics, wheel, detector, telescope, pslit, focal_plane):
        # Not all here is a Device, actually
        super(Connecttt, self).__init__(fibers, optics, wheel, detector, telescope, pslit, focal_plane)

    
    def set_targets(self,target_container):
        self.foc_plane.set_target_list(target_container)
        #if self.foc_plane.observing_conditions is not None:
        #    self.foc_plane.target_list.set_seeing(self.foc_plane.observing_conditions.seeing)
        
    def set_observing_conditions(self, obs_conditions):
        self.foc_plane.set_observing_conditions(obs_conditions)
        
                       
    def create_wavelength_distortion_interpolator(self):
        self.vph.create_distortion_interpolator_ins(self.detector)
    
    def create_spatial_distortion_interpolator(self):
        self.vph.create_spatial_distortion_interpolator_ins(self.detector)
        
    def create_traces(self,trace,min_y_coor):
        ''' Computes the shape of the different spectra according to their position on the detector. '''
        fiber_positions_on_detector = self.layout.get_fiber_positions_on_detector(self.cover)
        fiber_separation = fiber_positions_on_detector[1] - fiber_positions_on_detector[0]
        logging.debug('VPH: Creating traces...')
        
        # Create an array to hold the spectra adding space for the projection
        max_y_coor = np.ceil(trace.max(axis = 1))
        
        def create_single_trace(i):
            ''' Function that creates a trace given the position over the detector.
                The function is used in the list comprehension below to increase speed x2'''
            spectra_y_dim = max_y_coor[i] - min_y_coor[i] + fiber_separation
            spectra=np.zeros([spectra_y_dim,self.detector.size_x])
            trace[i]=trace[i]-min_y_coor[i]-1 # Size of the projection=7
            # Introduce the trace in spectra array
            floor_trace=np.floor(trace[i]).tolist()
            ceil_trace=np.ceil(trace[i]).tolist()
            pixel_frac=trace[i] % 1.0 # FIXME: what is this operation?
            spectra[floor_trace, range(spectra.shape[1])] = 1 - pixel_frac
            spectra[ceil_trace, range(spectra.shape[1])] = pixel_frac 

            return spectra

        traces = [create_single_trace(i) for i in range(len(fiber_positions_on_detector))]
        logging.debug('VPH: Traces created.')
	return traces
        
    def run(self, exptime):
        ''' Take image of exptime seconds of current focal plane.'''
        
        _logger.info('Taking image. Exptime: %i seconds',exptime)
                       
        self.vph.create_distortion_interpolators(self.detector, self.slit)
        self.foc_plane.set_vph(self.vph)
        
        self.foc_plane.compute_layout_flux(self.cover)
        input = MegaraObject(self.foc_plane.focal_plane_flux,
                             self.foc_plane.target_list.spec_db.wl_sampled,
                             self.layout.name,
                             self.vph.resolution_interpolator(self.foc_plane.target_list.spec_db.wl_sampled[-1]
                                                              )
                             )
        
        trans_input = self.apply_transmission(input)
        distorted_input = self.apply_wavelength_distortion(trans_input)        
        photon_distorted_input = self.convert_to_photons(distorted_input)
        spatial_distorted_detector_image = self.apply_spatial_distortion(photon_distorted_input)
        detector_image = self.project_spatial_profile(spatial_distorted_detector_image)
        self.detector.set_input(detector_image)
        logging.debug('MEGARA: Spatial profile projected.')
        
        logging.debug('MEGARA: Exposing detector...')                
        #self.detector.expose(exptime)
        data = self.das.run(exptime)
        logging.debug('MEGARA: Detector exposed.')        
        # No post-processing
        logging.info('MEGARA:Image successfully taken.')
        yield list(data)
        

    def apply_transmission(self,input):
        logging.debug('MEGARA:Applying transmission...')
        if self.transmission_interp is None:
            self.create_total_transmission_interp()
        return MegaraObject(np.array([input.data[i,:]*self.transmission_interp(input.wavelength) for i in range(input.data.shape[0])]),input.wavelength,input.layout,input.resolution)
        
    def degrade_resolution(self,input):
        logging.debug('MEGARA:Degrading resolution...') 
        resolution_kernel=KernelGenerator2d(input.resolution,self.vph.resolution_interpolator,input.wavelength)
        return MegaraObject(np.array(diff_convolve_2d(input.data, resolution_kernel)),input.wavelength,input.layout,input.resolution)
    
    def apply_wavelength_distortion(self,input):
        logging.debug('MEGARA:Applying wavelength distortion...')
        if self.vph.wavelength_distortion_interpolator is None:
            logging.debug('VPH:Creating wavelength distortion interpolator...')
            self.create_wavelength_distortion_interpolator()
            logging.debug('VPH:Wavelength distortion interpolator finished.')
        fiber_pos_det = self.layout.get_fiber_positions_on_detector(self.cover)
        input_detector_resampled = np.zeros((len(fiber_pos_det), self.detector.size_x))
        wavelength_detector_resampled = np.zeros_like(input_detector_resampled)
        self.dispersion = np.zeros_like(input_detector_resampled)
        
        logging.debug('VPH: Distorting wavelengths...')        
        apply_distortion(fiber_pos_det, input.data, input.wavelength, self.vph.wavelength_distortion_interpolator, input_detector_resampled, wavelength_detector_resampled)
        logging.debug('VPH: Distorting wavelengths finished.')
        self.dispersion[:,:-1] = np.diff(wavelength_detector_resampled) / 10.0 # * aa2nm
        self.dispersion[:,-1] = self.dispersion[:,-2]
        return MegaraObject(input_detector_resampled,wavelength_detector_resampled,input.layout,input.resolution)
    
    def convert_to_photons(self, input):
        logging.debug('MEGARA:Converting input flux to photons...')
        spaxel_aperture = (0.5 * 3 * math.sqrt(3) * (0.5 * self.layout.size) ** 2)
        tel_area = math.pi * (self.telescope.diameter / 2.0 ) ** 2.0
        throughput = self.dispersion * tel_area
        for i in range(len(self.layout.get_fiber_positions_on_detector(self.cover))):
#        for i,_ in enumerate(self.layout.get_fiber_positions_on_detector()):
            input.data[i,:]=ergscm2aaarcsec2photonsm2nmarcsec2(input.wavelength[i,:], input.data[i,:]) 
        return MegaraObject(input.data * throughput, input.wavelength, input.layout, input.resolution)
    
    def apply_spatial_distortion(self, input):
        logging.debug('MEGARA:Applying spatial distortion...')

        detector_spatial_distorted=np.zeros([self.detector.size_y,self.detector.size_x])
#        detector_spatial_distorted += 100
        fiber_positions_on_detector = self.layout.get_fiber_positions_on_detector(self.cover)

        fiber_separation = np.diff(self.vph.spatial_distortion_interpolator(0, fiber_positions_on_detector))
        fiber_separation = np.append(fiber_separation, fiber_separation[-1])
        fiber_separation = np.ceil(fiber_separation)
        
        
        fiber_positions_on_detector.shape = (fiber_positions_on_detector.shape[0],1)
        trace = self.vph.spatial_distortion_interpolator(range(self.detector.size_x),fiber_positions_on_detector)
        min_y_coor=np.floor(trace.min(axis=1))-fiber_separation
        
        #if self.used_traces[self.vph.vph_name] is None:
        traces = self.create_traces(trace, min_y_coor)
            
        for i,_ in enumerate(fiber_positions_on_detector[:,0]):
            detector_spatial_distorted[min_y_coor[i]:min_y_coor[i]+traces[i].shape[0]] = detector_spatial_distorted[min_y_coor[i]:min_y_coor[i]+traces[i].shape[0]] + traces[i]*input.data[i,:]
        
        return detector_spatial_distorted
    
    def project_spatial_profile(self,input):
        logging.debug('MEGARA:Projecting spatial profile...')
        return image_convolve(input, self.layout.projection_kernel, axis=0, mode='constant', cval=0.0)
            
    def create_total_transmission_interp(self):
        wave = np.linspace(3600.00, 9800.00, 6200)
        trans = self.optics.transmission_interp(wave) * self.fibers.transmission_interp(wave) * self.detector.transmission_interp(wave) * self.vph.transmission_interp(wave) * self.telescope.transmission_interp(wave)
        trans[trans<0] = 0.0
        interp = interpolate.interp1d(wave, trans, 'linear', bounds_error=False, fill_value=0.)
        self.transmission_interp = interp
