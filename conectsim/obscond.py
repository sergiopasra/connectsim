#

'''Observing conditions.'''

import os
import logging
import math

from .simulator_utils import create_interpolator
from .dar import DARFromLUT
from .optelement import OpticalElement

_logger = logging.getLogger('megarasim.obscond')

class Atmosphere(OpticalElement):
    def __init__(self):
        super(Atmosphere, self).__init__(None, name='atmosphere')

class ObservingConditions(object):
    def __init__(self, brigthfile, extfile, darcorrection, seeing=1.0, 
      elevation=90.0, sky_brightness=29.0, 
      obs_band='v_johnsonbessel', transmission=1.0):
        self.seeing = float(seeing)
        self.transmission = float(transmission)
        self.sky_file_name = brigthfile
        self.sky_brightness = sky_brightness
        self.obs_band = obs_band
        self.elevation = elevation
        self.airmass = 1.0 / math.cos(math.pi/180.0*(90.0-elevation))

        self.sky_ext_file = extfile
        self.transmission_interp = create_interpolator(self.sky_ext_file)
        
        self.dar_corr = darcorrection

    def dar(self, wl):
        '''DAR correction from current conditions.'''
        return self.dar_corr.value(self.airmass, wl)
        
def conditions_builder(allconf, occonf, data_dir):

    ins_conf, db_conf = allconf

    # Reading the list of devices available
    # named observatory
    observatory_name = ins_conf['observatory']

    # Reading the list of observing conditions
    ocdesc = occonf['description']
    seeing = occonf['seeing']
    elevation = occonf['elevation']
    sky_brig = occonf['sky']['brightness']
    sky_band = occonf['sky']['band']

    observatory_name = occonf.get('observatory', observatory_name)
    _logger.debug('Using %s observatory', observatory_name)

    # Reading the observatory sky conditions
    # raises KeyError if not present...
    my_obs_data = db_conf['observatories'][observatory_name]
    sky_spec = os.path.join(data_dir, my_obs_data['spectrum'])
    sky_extc = os.path.join(data_dir, my_obs_data['extcurve'])

    # Create a DAR correction from table
    sky_dar_file = os.path.join(data_dir, my_obs_data['dar'])
    dar_corr = DARFromLUT(sky_dar_file)

    # Setting observing conditions
    _logger.debug('Create Observing Conditions')
    oc = ObservingConditions(brigthfile=sky_spec, 
                    extfile=sky_extc,
                    darcorrection=dar_corr,
                    seeing=seeing,
                    elevation=elevation,
                    sky_brightness=sky_brig,
                    obs_band=sky_band)
    _logger.debug('done')
    _logger.info('Observing at elevation: %.1f degrees.', elevation)

    return oc

