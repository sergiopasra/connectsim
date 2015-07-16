
from numpy import array,convolve
import numpy as np
from scipy import interpolate,integrate, spatial, append
from scipy.signal import convolve2d

def create_interpolator(file_name):
    ''' Reads a file with columns x,y and creates an interpolator object '''
    data = np.loadtxt(file_name)
    return interpolate.UnivariateSpline(data[:,0], data[:,1], k=3, s=0)

class KernelGenerator(object):
    tmp = 2. * np.sqrt(2 * np.log(2))
    def __init__(self,res_ini,res_end_interp,wavelength):
        self.kernel=[]
        delta_lambda=wavelength[1]-wavelength[0]
        for wave in wavelength:
            sig_ini = wave / (kernel_generator.tmp * res_ini)
            res_end = res_end_interp(wave)
            sig_end = wave / (kernel_generator.tmp * res_end)
            sigma = np.sqrt(sig_end ** 2 - sig_ini ** 2)
            if sigma < 1e-5:
                self.kernel.append(np.array([1]))
                continue
            num=np.ceil(10*sigma/delta_lambda)
            if (num % 2) == 0:
                num=num+1
            x=np.linspace(-5 * sigma, 5 * sigma, num)
            g = np.exp(-(x ** 2) / (2 * sigma ** 2))
            self.kernel.append(g / g.sum() ) #np.trapz(g,x))
    
    def __call__(self,i):
        return self.kernel[i]

class KernelGenerator2d(object):
    tmp = 2. * np.sqrt(2 * np.log(2))
    def __init__(self,res_ini,res_end_interp,wavelength):
        self.kernel=[]
        delta_lambda=wavelength[1]-wavelength[0]
        for i in xrange(len(wavelength)):
            wave = wavelength[i]
            sig_ini = wave / (KernelGenerator.tmp * res_ini)
            res_end = res_end_interp(wave)
            sig_end = wave / (KernelGenerator.tmp * res_end)
            sigma = np.sqrt(sig_end ** 2 - sig_ini ** 2)
            if sigma < 1e-5:
                self.kernel.append(np.array([1]))
                continue
            
            num=np.ceil(10*sigma/delta_lambda)
            if (num % 2) == 0:
                num=num+1
            x=np.linspace(-5 * sigma, 5 * sigma, num )
            g = np.exp(-(x ** 2) / (2 * sigma ** 2))
            self.kernel.append(g / g.sum() ) #np.trapz(g,x))
    
    def __call__(self,i):
        size = len(self.kernel[i])
        kernel_2d=np.zeros([1,size])
        kernel_2d[0,:] = self.kernel[i]
        return kernel_2d

def single_kernel_generator(res_ini,res_end,wave,delta_lambda):
    tmp = 2. * np.sqrt(2 * np.log(2))
    sig_ini = wave / (tmp * res_ini)
    sig_end = wave / (tmp * res_end)
    sigma = np.sqrt(sig_end ** 2 - sig_ini ** 2)
    if sigma < 1e-5:
        return np.array([1])
            
    num=np.ceil(10*sigma/delta_lambda)
    if (num % 2) == 0:
        num=num+1
    x=np.linspace(-5 * sigma, 5 * sigma, num )
    g = np.exp(-(x ** 2) / (2 * sigma ** 2))
    return g / g.sum() #np.trapz(g,x)

def diff_convolve(input_array, KernelGenerator):
    '''
    kernel_function: function that returns a kernel for each element in input_array. Kernel must be normalized and length must be odd.
    '''
    return array([np.convolve(input_array[max(0,i-KernelGenerator(i).shape[0]/2):min(input_array.shape[0],i+KernelGenerator(i).shape[0]/2)],KernelGenerator(i),'valid')[0] for i in range(input_array.shape[0])])

def diff_convolve_2d(input_array, KernelGenerator):
    '''
    kernel_function: function that returns a kernel for each element in input_array. Kernel must be normalized and length must be odd.
    '''
    output_array = np.zeros_like(input_array)
    wave_size = input_array.shape[1]
    for i in range(input_array.shape[1]):
        kernel = KernelGenerator(i)
        size = kernel.shape[1]
        min_x = max(0, i - size / 2)
        max_x = min(input_array.shape[1], i + size / 2 + 1)
        min_ker_x = -min( 0 , i - size / 2 )
        max_ker_x = min(size , wave_size - i + size / 2 )
        #print i, kernel.shape[1], min_ker_x, max_ker_x, min_x, max_x
        kernel = kernel[:, min_ker_x : max_ker_x ] 
        output_array[:,i] = convolve2d(input_array[:,min_x:max_x],kernel,'valid').ravel()
    return output_array

    
def apply_distortion(fiber_position,spectrum,wavelength,dist_interp, input_detector_resampled, wavelength_detector_resampled):
    fiber_position.shape = (fiber_position.shape[0],1)
    wavelength_detector_resampled[:,:] = dist_interp(range(4096),fiber_position)[:,:]
    
    fiber_position.shape = (fiber_position.shape[0],)
    for i in range(len(fiber_position)):
        sp = interpolate.interp1d(wavelength,spectrum[i,:])
        input_detector_resampled[i,:] = sp(wavelength_detector_resampled[i,:])
     
# Function to compute kernels in steps of 0.1 pixels
def initialize_spatial_kernels(kernel_seed):
    kernels=np.zeros([101,11])
    for j in range(101):
        pixel_frac=(j-50)/100.0
        kernels[j,:]=np.array([integrate.quad(kernel_seed,i+pixel_frac,i+pixel_frac+1)[0]/integrate.quad(kernel_seed,-10,10)[0] for i in range(-5,6)])
    return kernels
 
def add_spectra_old(fiber_position, spectrum,detector,kernels,spatial_distortion_interp):
#    print "Adding spectra",fiber_number
    fiber_separation=6 #Change to a file containing the positions of the fibers
    # Interpolate the trace
    trace=spatial_distortion_interp(range(detector.shape[1]),fiber_position)
    
    # Create an array to hold the spectra adding space for the projection
    min_y_coor=np.floor(min(trace))-fiber_separation
    spectra_y_dim=np.ceil(max(trace))-min_y_coor+fiber_separation
    spectra=np.zeros([spectra_y_dim,detector.shape[1]])  
    trace=trace-min_y_coor-1 # Size of the projection=7
    
    # Introduce the trace in spectra array
    for i in range(spectra.shape[1]):
        spectra[np.round(trace[i]),i]=1
    spectra=spectra*spectrum

    #Convolving each row with kernel
    pixel_frac=-(trace-np.round(trace))
    for i in range(spectra.shape[1]):
        # WARNING: There seems to be an offset when selecting the kernel. CHECK!!! 
        spectra[:,i]=np.convolve(spectra[:,i],kernels[50+round(pixel_frac[i]*100),:],'same') 
    # Add spectra to detector
    detector[min_y_coor:min_y_coor+spectra.shape[0]]=detector[min_y_coor:min_y_coor+spectra.shape[0]]+spectra


def angle_reduction(phi):
    return np.sort(np.array([phi, np.pi/3. - phi, phi - np.pi/3.0]),0)[1]    

class Hex(object):
    def __init__(self,size):
        self.size = size
    
    def upper_bound(self,x):
        l = self.size                                                       
        if x < -l:
            return 0;
        elif x < -l/2.0 :
            return np.tan(60.*np.pi/180.) * (x + (l + 2. * l * np.cos(60. * np.pi / 180.))/2.0)
        elif x < l/2.0 :
            return l * np.sin(60*np.pi/180.)
        elif x<=l:
            return - np.tan(60*np.pi/180.) * (x - (l + 2. * l * np.cos(60 * np.pi / 180.))/2.0)
        else:
            return 0

    def lower_bound(self,x):
        return -self.upper_bound(x)
    
    def get_integ_grid(self):
        grid=[]
        size = self.size
        step = self.size / 25.0
        for i in np.arange(-size + step/2.0 , size + step/2.0  , step):
            for j in np.arange(self.lower_bound(i) + step/2.0, self.upper_bound(i) - step/2.0, step):
                grid.append([i,j])
        inner_points = np.array(grid, dtype = np.float64)
        points = np.zeros([50*4,2])
        x = np.linspace(-size, size, 50 )
        k=0
        for x0 in x:
            points[k,:] = [x0, self.upper_bound(x0)]
            points[k+1,:] = [x0, self.upper_bound(x0) - 1e-5]
            points[k+2,:] = [x0, self.lower_bound(x0)]
            points[k+3,:] = [x0, self.lower_bound(x0) + 1e-5]
            k=k+4
        dual_points = append(inner_points,points,axis=0)
        dela = spatial.Delaunay(dual_points)
        ver_points = dela.points[dela.vertices]
        centers_ex = ver_points[:,:,:].sum(1)/3.0
        tri_areas = np.abs(ver_points[:,0,0]*(ver_points[:,1,1]-ver_points[:,2,1])+ver_points[:,1,0]*(ver_points[:,2,1]-ver_points[:,0,1])+ver_points[:,2,0]*(ver_points[:,0,1]-ver_points[:,1,1]))/2.0
        return centers_ex,tri_areas
        
    def get_border_grid(self):
        points = np.zeros([50*4,2])
        #x = np.linspace(-self.size-0.01, self.size+0.01, 50 )
        x = np.linspace(-self.size, self.size, 50 )
        k=0
        for x0 in x:
            points[k,:] = [x0, self.upper_bound(x0)]
            #points[k+1,:] = [x0, self.upper_bound(x0) + 1e-5]
            points[k+1,:] = [x0, self.upper_bound(x0) - 1e-5]
            points[k+2,:] = [x0, self.lower_bound(x0)]
            points[k+3,:] = [x0, self.lower_bound(x0) + 1e-5]
            #points[k+5,:] = [x0, self.lower_bound(x0) - 1e-5]
            k=k+4
        return points
    
def update_header_with_observatory(header):
    header.update('OBSERVAT','ORM','Name of observatory')                            
    header.update('SLATEL','LP10.0','Telescope name known to SLALIB')              
    header.update('TELESCOP','GTC','Telescope id.')                                  
    header.update('LATITUDE',28.762,'[deg] Telescope latitude, +28:45:53.2')          
    header.update('LONGITUD',17.877639,'[deg] Telescope longitude, +17:52:39.5')         
    header.update('HEIGHT',2348,'[m] Height above sea level')                     
    header.update('OBSGEOZ',969439.1412,'[m] Observation Z-position')                    
    header.update('OBSGEOX',5753296.428,'[m] Observation X-position')                     
    header.update('OBSGEOY',3005451.209,'[m] Observation Y-position')

def update_header_with_instrument(header):
    header.update('INSTRUME','MEGARA','Name of the Instrument')                         
    header.update('FSTATION','FCASS','Focal station of observation')                   
    header.update('SPECUNIT','A','Spectrograph unit')                              
    header.update('SPECSOUR','MOS','Spectrograph light source')                      
    header.update('PLATESCA',1.502645,'[d/m] Platescale 5.41 arcsec/mm')               
