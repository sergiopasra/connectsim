
from __future__ import print_function

import sys
import os
import logging
import argparse
import hashlib
import cPickle as pickle
import errno

import yaml

from .builder import instrument_builder
from .obscond import conditions_builder, Atmosphere
from .focal_plane import GaussianTar, TargetContainer
from .control import ControlSystem

_logger = logging.getLogger("conectsim")

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except (OSError, IOError) as exception:
        if exception.errno != errno.EEXIST:
            raise

def try_open(filename):
    if filename is None:
        return None
    try:
        with open(filename) as fd:
            _logger.debug('loading from %s', filename)
            conf = list(yaml.load_all(fd))
            return conf
    except IOError as error:
        print(error)
    return None

def md5_from_file(filename, block=4096):
    md5 = hashlib.md5()
    with open(filename, 'rb') as fd:
        while True:
            data = fd.read(block)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()
                

def save_megara_in_cache(cache_dir, jash, megara):
    make_sure_path_exists(cache_dir)
    with open(os.path.join(cache_dir, jash), 'w+') as fd:
        pickle.dump(megara, fd)

def restricted_float(x):
    x = float(x)
    if x < 0.0 or x > 36000.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 36000.0]"%(x,))
    return x

def main(args=None):
    '''Entry point for the conectsim CLI.'''

    parser = argparse.ArgumentParser(
        description='Command line interface of conectsim',
        prog='conectsim'
    )
    parser.add_argument('-i','--instrument', metavar="FILE",
                    help="FILE with instrument configuration")
    parser.add_argument('-c','--conditions', metavar="FILE",
                    help="FILE with observing conditions configuration")
    parser.add_argument('-p','--parameters', metavar="FILE",
                    help="FILE with observing parameters")
    parser.add_argument('-t','--targets', metavar="FILE",
                    help="FILE with target configuration")
    parser.add_argument('-e','--exposure', type=restricted_float,
                    help="Exposure time per image (in seconds) [0,36000]")
    parser.add_argument('-n','--nimages', metavar="INT", type=int, default=1,
                    help="Number of images to generate")
    parser.add_argument('-l','--loglevel', type=str, default='debug',
                    choices=['DEBUG','debug','INFO','info','ERROR','error','CRITICAL','critical'],
                    help="Logging level")
    parser.add_argument('--dest-dir', help="directory to write out put images",
        default=os.getcwd())
    parser.add_argument('-v','--version', action='version', version='%(prog)s 0.1', 
                    help="conectsim version")
    
    args = parser.parse_args(args)
    
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)

    #logging.basicConfig(format='%(asctime)s-%(levelname)s:%(message)s', level=numeric_level)
    logging.basicConfig(level=numeric_level)


    # Trying to separate the data from the code
    # Instrument data should not be installed in python dirs
    # so that it can be installed/updated independently

    home_dir = os.getenv('HOME', '/')
    # Cache dir
    cache_base = os.getenv('XDG_CACHE_HOME', os.path.join(home_dir, '.cache'))
    cache_dir = os.path.join(cache_base, 'conectsim')
    # Config dir
    config_base = os.getenv('XDG_CONFIG_HOME', os.path.join(home_dir, '.config'))
    config_dir = os.path.join(cache_base, 'conectsim')

    # destination dir
    args.dest_dir = os.path.abspath(args.dest_dir)

    # The data will be loaded from conf file
    conf = None
    # Try to read from the command line
    if args.instrument:
        data_file = args.instrument
        conf = try_open(args.instrument)
    # Read from a env variable
    if not conf:
        # Reading conectsim_DATA_DIR
        data_file = os.getenv('conectsim_DATA_DIR')
        conf = try_open(data_file)
    
    if not conf:
        # try to build something from the prefix
        data_file = os.path.join(sys.prefix, 'share/conectsim/data/conf.yaml')
        conf = try_open(data_file)

    if not conf:
        # we give up for the moment
        sys.exit(1)
    # We define data_dir as the file where the data_file is located
    data_dir = os.path.dirname(data_file)

    _logger.info('Starting CONNECT operations.')
    _logger.info('DATA dir is %s', data_dir)
    _logger.info('Destination for results is %s', args.dest_dir)
    try:
        meg = instrument_builder(conf, data_dir)
    except KeyError:
        sys.exit(1)

    # try to save conect in cache
    #_logger.debug('Save conect instance in cache')
    #jash = md5_from_file(data_file)
    # meg object still contains attributes that cannot be pickled
    #save_conect_in_cache(cache_dir, jash, meg)
        
    # Reading the observing conditions conf file
    # Try to read from the command line
    if args.conditions:
        occonf = try_open(args.conditions)[0]       
    else:
        _logger.error('No observing conditions configuration file provided')
        sys.exit(1)

    try:
        oc = conditions_builder(conf, occonf, data_dir)
    except KeyError as error:
        _logger.error('%s', error)
        sys.exit(1)

    # Reading the observing parameters conf file
    # Try to read from the command line
    if args.parameters:
        opconf = try_open(args.parameters)[0] 
    else:
        _logger.error('No observing parameter configuration file provided')
        sys.exit(1)

    # The targets are read from the targets file
    targetconf = try_open(args.targets)[0]
    if not targetconf['targets']:
        _logger.warn('No targets are provided')

    # Reading the targets file 
    target_list = []
    if targetconf['targets']:
        for key, target in targetconf['targets'].items():
            target_list.append(GaussianTar(target[0],
                        target[1],
                        os.path.join(data_dir, 'spectra',target[2]),
                    target[3],
                    target[4])
                    )
    target_list = TargetContainer(target_list)
    meg.set_targets(target_list)
    
    # Setting observing conditions
    meg.set_observing_conditions(oc)

    # FIXME: this is a hack
    atm = Atmosphere()
    atm.connect(meg.telescope)
    # done

    # STILL TO BE DONE - where are the other files for the vphs defined?
    # where are the transmission for the telescope, optics, and layout defined so they can be taken from the conf files? 
    # homogeneize the "change_layout" possibilities with the names for the "bundles" in the conf files
    # Most things have to be now changed in instrument.py
    # Change detector.py so it takes all CCD parameters from the conf file as in user.py (data/conf.yaml)

    cs = ControlSystem(destdir=args.dest_dir)
    cs.register('CONNECT', meg)
    # This would be a sequence
    for _ in range(args.nimages):
        instrument = cs.get('CONNECT')
        # configure instrument here...
        instrument.configure(opconf)
        # done
        # run exposure here
        cs.run(instrument, args.exposure)
        # done
        # FITS files are stored by CS

    _logger.info('CONNECT operations finished.')

if __name__ == '__main__':
    main()
