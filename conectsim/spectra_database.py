
from astropy.io import fits 
import numpy as np
from scipy import interpolate, integrate

#from astrophysics_unit import *
from astrophysics_unit import flambda2fnu
from simulator_utils import *

class SpectraDatabase(object):
    ''' FlyWeight??'''
    sampling_factor = 9.0
    def __init__(self):
        self.spectra_dict = {}
        self.mag_integrals = {}
        self.filters = {}
        self.sky_spectrum_file_name = None
        #self.add_spectrum(self.sky_spectrum_file_name)
        self.selected_vph = None
        self.to_update = True
        self.updated = False
        
    def set_vph(self, vph, filters_dir):
        self.updated = False
        if self.selected_vph is None or self.selected_vph.name is not vph.name or self.to_update:
            self.selected_vph = vph
            wl_ini = self.selected_vph.wavelength_distortion_interpolator(0,55) - 25
            wl_max = self.selected_vph.wavelength_distortion_interpolator(4096,0) + 25
            self.wl_sampled = np.arange(wl_ini, wl_max, wl_max / self.selected_vph.resolution_interpolator(wl_max) / SpectraDatabase.sampling_factor)
            self.create_spectra_array(filters_dir)
            #self.read_sky_spectrum()
            self.to_update = False
            self.updated = True
        
    
    def get_spectrum(self,spectrum_file_name):
        return self.spectra_array[self.spectra_dict[spectrum_file_name][0]]
    
    def get_sky_spectrum(self):
        return self.spectra_array[self.spectra_dict[self.sky_spectrum_file_name][0]]
    
    def create_spectra_array(self, filters_dir):
        '''reads all different spectra and degrades the resolution to that of the VPH'''
        temp_spectra_array = np.zeros([len(self.spectra_dict) + 1,len(self.wl_sampled)])
        i=0
        for spectrum_file_name in self.spectra_dict.keys():
            temp_spectra_array[i,:] = self.read_spectrum(spectrum_file_name, self.wl_sampled[0], self.wl_sampled[-1], filters_dir)
            self.spectra_dict[spectrum_file_name][0] = i
            i=i+1
        '''Generates the resolution kernel to degrade reolution'''
        resolution_kernel = KernelGenerator2d(self.selected_vph.resolution_interpolator(self.wl_sampled[-1]), self.selected_vph.resolution_interpolator, self.wl_sampled)
        '''Degrades the spectra resolution to that of the selected VPH ( resolution change with wavelength)'''
        self.spectra_array = np.array(diff_convolve_2d(temp_spectra_array, resolution_kernel))
        

    def add_spectrum(self,spectrum_file_name, band = 'v_johnsonbessel'):
        if not self.spectra_dict.has_key(spectrum_file_name):
            ''' First argument in tuple is position in spectra_array. Second is number of objects with it.'''
            self.spectra_dict[spectrum_file_name] = [None,1]
            self.mag_integrals[spectrum_file_name] = {band: None}
            self.to_update = True
        else:
            self.spectra_dict[spectrum_file_name][1] += 1
            if band not in self.mag_integrals[spectrum_file_name].keys():
                self.mag_integrals[spectrum_file_name][band] = None
    
    def add_sky_spectrum(self,spectrum_file_name, band = 'v_johnsonbessel'):
        self.sky_spectrum_file_name = spectrum_file_name
        self.add_spectrum(spectrum_file_name, band)
        
        
    def remove_spectrum(self, spectrum_file_name):    
        if not self.spectra_dict.has_key(spectrum_file_name):
            return
        else:
            self.spectra_dict[spectrum_file_name][1] -= 1
            if self.spectra_dict[spectrum_file_name][1] == 0:
                self.spectra_dict.pop(spectrum_file_name)
                self.mag_integrals.pop(spectrum_file_name)
    

    def read_spectrum(self, spectrum_file_name, wl_min, wl_max, filters_dir):
        spectrum = fits.open(spectrum_file_name)
        
        large_shift = 5.0
        
        ''' REMOVE: We add resolution info in the header '''
        if spectrum_file_name.find("sky") < 0: 
            spectrum[1].header.update("R",80000)
            header = spectrum[1].header
            total_wl =  spectrum[1].data.field(0)
            total_flux = spectrum[1].data.field(1)
        else:
            spectrum[0].header.update("R",44000)
            header = spectrum[0].header
            total_flux = spectrum[0].data
            crval1 = header['crval1']
            crpix1 = header['crpix1']
            cd1_1 = header['cd1_1']
            total_wl = np.array([ crval1 + (i + 1 - crpix1) * cd1_1 for i in range(total_flux.shape[0])])
        ''' REMOVE '''
                 
        ''' WE COMPUTE FLUXES IN FILTERS HERE '''
        for band in self.mag_integrals[spectrum_file_name].keys():
            if band not in self.filters.keys():
                self.filters[band] = FilterInterp(band, filters_dir)
            filter = self.filters[band]
            filter_index = (total_wl > filter.wl_sampled[0]) * (total_wl < filter. wl_sampled[-1])
            integrate_wl =  total_wl[filter_index]
            integrate_flux = total_flux[filter_index]
            filter_resampling = filter.interp(total_wl[filter_index])
            flux_lambda = integrate.trapz(integrate_flux * filter_resampling, integrate_wl) / integrate.trapz(filter_resampling, integrate_wl)
            mean_wave = np.trapz(integrate_wl * filter_resampling, integrate_wl) / np.trapz(filter_resampling, integrate_wl)
            self.mag_integrals[spectrum_file_name][band] = -48.60 - 2.5 * np.log10(flambda2fnu( mean_wave, flux_lambda))
        resolution = header["R"]
        spec_index = (total_wl > self.wl_sampled[0] - large_shift) * (total_wl < self. wl_sampled[-1] + large_shift)
        wl = total_wl[spec_index]
        flux = total_flux[spec_index]
        flux[flux<0] = 0.0
        
        wl_linear = np.arange(wl[0],wl[-1],np.min(abs(np.diff(wl))))
        flux_interp = interpolate.interp1d(wl, flux)
        flux_linear = flux_interp(wl_linear)
        resolution_kernel = single_kernel_generator(resolution,self.selected_vph.resolution_interpolator(self.wl_sampled[-1]), wl_linear[-1], wl_linear[1] - wl_linear[0])
        self.res_ker = resolution_kernel
        flux_conv = np.convolve(flux_linear,resolution_kernel,'same')
        flux_interp = interpolate.interp1d(wl_linear, flux_conv)
        return flux_interp(self.wl_sampled)
        
class FilterInterp(object):
    def __init__(self,band, filters_dir):
        sfile = filters_dir + '/' + band + ".dat"
        data = np.loadtxt(sfile)
        self.wl_sampled = data[:,0]
        self.interp = interpolate.interp1d(self.wl_sampled,data[:,1],'linear')
            
