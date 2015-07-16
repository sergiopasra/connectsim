
import logging
import math

import numpy as np
from scipy import integrate, interpolate, spatial

from .simulator_utils import create_interpolator
from .spectra_database import SpectraDatabase

_logger = logging.getLogger('megarasim.foc')

_TAN30 = math.tan(30.5 * math.pi /180.)

class TargetContainer(object):
    def __init__(self, target_list=[]):
        self.target_list = target_list
        self.spec_db = SpectraDatabase()
        for target in target_list:
            self.spec_db.add_spectrum(target.spectrum_file_name, target.obs_band)
    
    def add_target(self,target):
        self.target_list.append(target)
        self.spec_db.add_spectrum(target.spectrum_file_name, target.obs_band)
    
    def set_seeing(self,seeing):
        for target in self.target_list:
            target.convolve(seeing)
    
    def __iter__(self):
        return iter(self.target_list)
    
    def __getitem__(self,i):
        return self.target_list[i]

    def is_empty(self):
        return not bool(len(self.target_list))
    
class Target(object):
    def __init__(self,x,y, spectrum_file_name, obs_mag, band = 'b'):
        self.coor = np.array([x,y])
        self.layout_indexes = None
        self.spectrum_file_name = spectrum_file_name
        self.obs_mag = obs_mag
        self.obs_band = band 
        
    def convolve(self,seeing):
        pass

class GaussianTar(Target):
    def convolve(self,seeing):
        self.seeing = seeing
        self.sigma = seeing / 2.3548
        
    def set_layout_indexes(self,lay_indexes):
        self.layout_indexes = lay_indexes
        
    def profile_polar(self, r, phi, vol = 1):
        width_x = self.seeing / 2.3548
        width_y = width_x
        center_x=r*np.cos(phi*np.pi/180.)
        center_y=r*np.sin(phi*np.pi/180.);
        return lambda y,x: vol/(2*np.pi*width_x*width_y)*np.exp(-(((x-center_x)/width_x)**2+((y-center_y)/width_y)**2)/2)

    def profile_coor_inv(self, x, y, vol = 1):
        width_x = self.seeing / 2.3548
        width_y = width_x
        center_x = float(x)
        center_y = float(y)
        return lambda y,x: vol/(2*np.pi*width_x*width_y)*np.exp(-(((x-center_x)/width_x)**2+((y-center_y)/width_y)**2)/2)

    def profile(self, x, y, vol = 1):
        width_x = self.seeing / 2.3548
        width_y = width_x
        center_x = float(x)
        center_y = float(y)
        return lambda x,y: vol/(2*np.pi*width_x*width_y)*np.exp(-(((x-center_x)/width_x)**2+((y-center_y)/width_y)**2)/2)

class FocalPlane(object):
    def __init__(self, target_list, layout, observing_conditions, filters_dir):
        _logger.debug('Initializing...')
        self.target_list = target_list
        self.layout = layout
        self.observing_conditions = observing_conditions
        self.to_update = True
        self.filters_dir = filters_dir
        _logger.debug('Initialized.')
        
    def set_vph(self,vph):
        _logger.debug('Setting VPH...')
        self.target_list.spec_db.set_vph(vph, self.filters_dir)
        self.to_update = self.to_update or self.target_list.spec_db.updated
        _logger.debug('VPH set.')
        
    
    def set_layout(self,layout):
        if self.layout is not layout:
            self.layout = layout
            self.to_update = True

    def set_observing_conditions(self, obscond):
        self.observing_conditions = obscond
        self.target_list.set_seeing(obscond.seeing)
        self.target_list.spec_db.add_sky_spectrum(obscond.sky_file_name, obscond.obs_band)
    
    def set_target_list(self,target_list):
        self.target_list = target_list
        if self.observing_conditions is not None:
            self.set_observing_conditions(self.observing_conditions)
        
    def compute_layout_flux(self, cover):
        if self.to_update is True:
            self.focal_plane_flux = np.zeros([len(self.layout.get_fiber_positions_on_detector(cover)),len(self.target_list.spec_db.wl_sampled)])    
            if not self.target_list.is_empty():
                _logger.debug('Starting flux computations.')
                _logger.debug('Starting Integrations...')
                interp = self.compute_interpolator()
                self.compute_target_on_spaxel(cover)
                dar_coors = self.modify_coor_DAR()
                po,phi = self.compute_reduced_coordinates(dar_coors)
                target_flux_on_hex = np.array(interp(po, phi))
                _logger.debug('Integrations finished.')
                # FIXME: Change this hardcoded stone....
                num = 100
                target_flux_on_hex.shape = (target_flux_on_hex.shape[0]/num, num)
                wl = np.linspace(self.target_list.spec_db.wl_sampled[0], self.target_list.spec_db.wl_sampled[-1], num)
                _logger.debug('Creating DAR Interpolator...')
                interp_dar = interpolate.interp1d(wl, target_flux_on_hex, 'cubic',1, bounds_error=False,fill_value=-1e3)
                _logger.debug('DAR Interpolator created.')
                _logger.debug('Fine interpolation started...')
                flux_dar_spax = interp_dar(self.target_list.spec_db.wl_sampled)
                _logger.debug('Fine interpolation finished')
            
                _logger.debug('Assigning Target flux to fibers...')
                flux_dar_spax[flux_dar_spax<1e-17] = 0        
                for Target in self.targets_with_flux:
                    Target.spectrum_factor = 10 ** ( -0.4 * (Target.obs_mag - self.target_list.spec_db.mag_integrals[Target.spectrum_file_name][Target.obs_band]))
                    self.focal_plane_flux[Target.layout_indexes] += Target.spectrum_factor * self.target_list.spec_db.get_spectrum(Target.spectrum_file_name) * flux_dar_spax[:len(Target.layout_indexes)]
                    flux_dar_spax = flux_dar_spax[len(Target.layout_indexes):]
                    
                self.focal_plane_flux *= 10**(-0.4*(self.observing_conditions.airmass * self.observing_conditions.transmission_interp(self.target_list.spec_db.wl_sampled)))
                _logger.debug('Target flux assignment finished.')

            _logger.debug('Assigning sky flux to fibers...')
            spectrum_factor = 10 ** ( -0.4 * (self.observing_conditions.sky_brightness - self.target_list.spec_db.mag_integrals[self.observing_conditions.sky_file_name][self.observing_conditions.obs_band]))
            hex_area =  3 * math.sqrt(3) / 2.0 * self.layout.size ** 2
            self.focal_plane_flux +=  hex_area * spectrum_factor * self.target_list.spec_db.get_sky_spectrum()
            _logger.debug('Flux assignment finished.')
            _logger.debug('Flux computations finished.')
            self.to_update = False
        
    def compute_target_on_spaxel(self, cover):
        self.targets_on_spaxel = {}
        self.target_relative_coors = []
        self.targets_with_flux = []

        # This is fixed during the execution
        fiberpos_on_space = self.layout.get_fiber_positions_on_space(cover)

        all_indexes = np.array(range(len(fiberpos_on_space)))
        sampling_pos = None
        wl_min = np.float(self.target_list.spec_db.selected_vph.wavelength_distortion_interpolator(0,55))
        wl_max = np.float(self.target_list.spec_db.selected_vph.wavelength_distortion_interpolator(4096,0))
        wl_central = (wl_min + wl_max) / 2.0
        max_dis = self.observing_conditions.seeing + self.layout.size * 2.0    
        for Target in self.target_list:
            if sampling_pos is None:
                res = self.observing_conditions.dar([wl_min, wl_central, wl_max])
                pos_min = np.asarray([[0.0, res[0,0] - res[0,1]]])
                pos_max = np.asarray([[0.0, res[0,2] - res[0,1]]])
                dif_vec = pos_max - pos_min
                dis_rec = np.linalg.norm(dif_vec)
                sampling_pos = []
                n_points = 2 + int(dis_rec*2./max_dis)
                for i in range(n_points):
                    sampling_pos.append(pos_min+dif_vec*i/float(n_points-1))
            hex_index = np.array([], dtype = np.uint8)
            for pos in sampling_pos:              
                coor_diff = Target.coor + pos - fiberpos_on_space
                dis = np.sqrt(np.sum(coor_diff*coor_diff,axis=1))
                hex_index = np.hstack((hex_index,all_indexes[dis < max_dis]))
            hex_index = np.unique(hex_index)
            if hex_index is not []:
                self.targets_with_flux.append(Target)
                Target.set_layout_indexes(hex_index)
                self.targets_on_spaxel[Target] = [hex_index,coor_diff[hex_index]]
                self.target_relative_coors.append(coor_diff[hex_index])
        self.target_relative_coors = np.vstack(self.target_relative_coors)

    def compute_reduced_coordinates(self, coors):
        coor_red = np.abs(coors)
        phi = np.arctan2(coor_red[:,1],coor_red[:,0])
        phi = np.sort(np.array([phi, np.pi/3. - phi, phi - np.pi/3.0]),0)[1]/np.pi*180.
        po = np.sqrt(coor_red[:,0]*coor_red[:,0] + coor_red[:,1]*coor_red[:,1])
        #coord_polar = np.array(zip(po,phi))
        #return coord_polar
        return po,phi
    
    def modify_coor_DAR(self):
        wl_samp = np.linspace(self.target_list.spec_db.wl_sampled[0], self.target_list.spec_db.wl_sampled[-1], 100)
        number = len(wl_samp)
        #
        res = self.observing_conditions.dar(wl_samp)
        dar_shift = np.zeros((wl_samp.shape[0], 2))
        dar_shift[:,1] = res.T[:,0]
        #
        dar_coor = np.zeros([number*len(self.target_relative_coors),2])
        i=0
        for coor in self.target_relative_coors:
            dar_coor[0+i*number:(1+i)*number,:] = coor + dar_shift
            i = i + 1
        return dar_coor
        
             
    def compute_interpolator(self):
        Target=self.target_list[0]
        #Target.convolve(self.observing_conditions.seeing)
        hex = self.layout.shape
        interp_points=[]
        interp_points.append([0,0])
        for i in np.arange(0 , hex.size * 4.0, 0.01):
            for j in np.arange(0 , i * _TAN30 , 0.01):
                interp_points.append([i,j])
        
        grid,areas = hex.get_integ_grid()
        points = np.array(interp_points,dtype = np.float16)
        results = np.zeros([len(points),1],dtype = np.float16)
        k = 0
        for k in range(len(points)):
            prof = Target.profile(points[k,0],points[k,1],1);
            results[k] = (prof(grid[:,0], grid[:,1])*areas).sum()
            k=k+1
        coverage_interp = lambda r,phi: interpolate.griddata(points, results, (r*np.cos(phi*np.pi/180.0),r*np.sin(phi*np.pi/180.0)), method='linear', fill_value = 0)
        return coverage_interp
