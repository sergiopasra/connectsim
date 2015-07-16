
import os
import logging


import numpy as np

from .calibration import CalibrationUnitSelector
from .telescope import Telescope
from .fiberlayout import FiberBundle
from .pseudoslit import PseudoSlitSelector
from .pseudoslit import Slit
from .fiber import Fibers
from .simulator_utils import create_interpolator
from .focal_plane import FocalPlane, TargetContainer
from .vph import vph_builder
from .wheel import VPHWheel
from .detector import CDetector
from .optelement import Stop, Open, Filter
from .instrument import GenericCOptics, Connecttt

_logger = logging.getLogger('megarasim.builder')

def wheel_builder(wheel_conf, vphs_conf, datadir):
    wheel = VPHWheel(len(wheel_conf))
    for idx, name in enumerate(wheel_conf):
        _logger.info('VPH key is %s', name)
        try:
            this_vph_conf = vphs_conf[name]
            this_vph_conf['datadir'] = datadir
            this_vph_conf['name'] = name
            vph = vph_builder(this_vph_conf)
            wheel.put_in_pos(vph, idx)
            _logger.info('VHP %s in position %d', name, idx)
        except KeyError:
            _logger.error('VHP %s does not exist', name)
    return wheel

def pseudo_slit_builder(bundle_conf, bundles_conf, datadir):
    # Add two holders more, one for block, on for empty
    offset = 2
    pslit = PseudoSlitSelector(len(bundle_conf) + offset)

    pslit.put_in_pos(Open(name='pslit open'), 0)
    _logger.info('Position 0 is empty')
    pslit.put_in_pos(Stop(name='pslit stop'), 1)
    _logger.info('Position 1 is closed')
    for idx, name in enumerate(bundle_conf, offset):
        _logger.info('Fiber Bundle is %s', name)
        try:
            tb_conf = bundles_conf[name]
            size = tb_conf['size']
            fwhm = tb_conf['fwhm']
            spatial_positions_file = os.path.join(datadir, tb_conf['layout'])
            # FIXME: The format of this file is not described anywere
            layout_data = np.loadtxt(spatial_positions_file)
            pos_on_space = layout_data[:,:2]
            pos_on_detector = layout_data[:,2]

            _logger.debug('Initializing %s', name)
            layout = FiberBundle(name, pos_on_space, pos_on_detector, size, fwhm)
            _logger.debug('done')
            pslit.put_in_pos(layout, idx)
            _logger.info('Layout %s in position %d', name, idx)
        except KeyError:
            _logger.error('Layout %s does not exist', name)
    return pslit

def calibration_unit_selector_builder():
    # Add two holders more, one for block, on for empty
    cuselector = CalibrationUnitSelector(2)

    cuselector.put_in_pos(Open(name='CUOFF'), 0)
    _logger.info('Position 0 is open')
    cuselector.put_in_pos(Stop(name='CUON'), 1)
    _logger.info('Position 1 is closed')

    return cuslector

def detector_builder(conf, tf):
    size_x = conf['sizex']
    size_y = conf['sizey']
    pixel_size = conf['psize']
    # QE from file
    quantum_eff = create_interpolator(tf)
    _logger.debug('Initializing detector')
    detector = CDetector(size_x, size_y, pixel_size, qe=quantum_eff)
    _logger.debug('Successful initialization.')
    return detector

def telescope_builder(telescope_conf, datadir):
    telescope_tf = os.path.join(datadir, telescope_conf['transmission'])
    diam = telescope_conf['diameter']
    telescope_trans = create_interpolator(telescope_tf)
    telescope = Telescope(diameter=diam, transmission=telescope_trans)
    return telescope

def instrument_builder(conf, datadir):
    '''Create an instance of Megara from the contents of a conf file.'''

    ins_conf, db_conf = conf
    #
    optics_conf = db_conf['optics']
    optics_tf = os.path.join(datadir, optics_conf['efficiency'])
    _logger.debug('Initializing generic optics')
    optics = GenericCOptics(transmission_file=optics_tf)
    _logger.debug('done')
    vphs_conf = db_conf['vphs']
    #
    ins_layout = ins_conf['layout']
    #
    # bundles
    bundle_conf = ins_layout['bundle']
    bundles_conf = db_conf['bundles']
    pslit = pseudo_slit_builder(bundle_conf, bundles_conf, datadir)
    # wheel
    wheel_conf = ins_layout['wheel']
    wheel = wheel_builder(wheel_conf, vphs_conf, datadir)

    # detector
    detector_key = ins_layout['detector']
    _logger.info('detector key is %s', detector_key)
    detectors_db = db_conf['detectors']
    try:
        detector_conf = detectors_db[detector_key]
    except KeyError:
        _logger.error('detector key %s does not exist', detector_key)
        raise
    detector_tf = os.path.join(datadir, detector_conf['efficiency'])
    detector = detector_builder(detector_conf, detector_tf)
    #
    fibers_conf = db_conf['fibers']
    fibers_tf = os.path.join(datadir, fibers_conf['global-transmission'])
    _logger.debug('Initializing fibers...')
    fibers_trans = create_interpolator(fibers_tf)
    # the length is not used, AFAIK
    fibers = Fibers(transmission=fibers_trans, length=20.0)
    _logger.debug('done')
    #
    telescope_key = ins_conf['telescope']
    _logger.info('telescope key is %s', telescope_key)
    telescopes_db = db_conf['telescopes']
    try:
        telescope_conf = telescopes_db[telescope_key]
    except KeyError:
        _logger.error('telescope key %s does not exist', detector_key)
        raise

    _logger.debug('Initializing telescope')
    telescope = telescope_builder(telescope_conf, datadir)
    _logger.debug('done')
    
    #
    # Filters
    filters_conf = db_conf['filters']
    filters_dir = os.path.join(datadir, filters_conf['dirpath'])
    #
    focal_plane = FocalPlane(TargetContainer(), pslit.current(), None, filters_dir)
    _logger.debug('Initializing MEGARA')
    meg = Connecttt(fibers=fibers, optics=optics, wheel=wheel, detector=detector,
        telescope=telescope, pslit=pslit, focal_plane=focal_plane)
    _logger.debug('MEGARA initialized')
    return meg







