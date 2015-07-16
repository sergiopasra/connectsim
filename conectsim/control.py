
from __future__ import division
from __future__ import print_function

import logging
import copy
from datetime import datetime

#from numina.treedict import TreeDict

_logger = logging.getLogger('control')

class ObservingBlock(object):
    _count = 1
    def __init__(self):
        self.id = self.__class__._count
        self.__class__._count += 1

def name_generator(name='r%05d.fits', start=1):
    idx = start
    while True:
        yield name % idx
        idx += 1

class ControlSystem(object):
    def __init__(self, destdir):
        self.ng = name_generator()
        self.destdir = destdir
        self.meta = {} #TreeDict()
        self.meta['ob'] = {'observer': 'SIMULATOR', 'object': 'FOCUS', 'mode': 'ENGINEERING'}
        self.meta['pointing'] = {'airmass': 1.0,  'dec': '10:01:04.000', 'ra': '04:05:00.40'}
        self.meta['proposal'] = {'id': 100,  'pi_id': 0}
        self.meta['control'] = { 'name': 'SIMULATOR', 'runid': 1, 'date': '0'}

        self._elements = {}

        self.current_obs_block = None

    def register(self, name, element):
        self._elements[name] = element

    def get(self, name):
        return self._elements[name]

    def create_ob(self, mode, target=''):
        oblock = ObservingBlock()
        oblock.observing_mode = mode
        #oblock.observer_id = user.id
        oblock.observer = 'SIMULATOR'
        oblock.object = target
                                
        #oblock.observing_tree = ores
        #oblock.obsrun = self.current_obs_run
        #self.session.add(oblock)
        #self.session.commit()        
        self.current_obs_block = oblock
        return oblock.id

    def start_ob(self):
        _logger.info('starting observing block %i', self.current_obs_block.id)
        oblock = self.current_obs_block
        oblock.start_time = datetime.utcnow()

    def end_ob(self):
        oblock = self.current_obs_block
        oblock.completion_time = datetime.utcnow()
        _logger.info('ending observing block')
        self.current_obs_block = None
        return oblock

    def set_ob_object(self, name):
        self.ob_object_name = name
        self.meta['ob.object'] = name

    def pre(self, instrument):
        #instrument.pre()
        pass

    def _run(self, instrument, exposure):
        names = []
        meta = copy.deepcopy(self.meta)
        meta[instrument.name] = instrument.config_info()
        ob = meta['ob']
        control = meta['control']
        #metavars = {'repeat': 1, 'template': meta['ob.object']}
        metavars = {'repeat': 1, 'template': ob['object']}
        for data in instrument.run(exposure):
            name = self.ng.next()
            names.append(name)
            # Update metadata    
            #meta['control.date'] = datetime.utcnow().isoformat()
            #meta['control.runid'] = self.current_obs_block.id
            #meta['ob.object'] = metavars['template'].format(**metavars)
            control['date'] = datetime.utcnow().isoformat()
            control['runid'] = 1 #FIXME, this was self.current_obs_block.id

            #meta['ob.object'] = metavars['template'].format(**metavars)
            ob['object'] = metavars['template'].format(**metavars)

            #_logger.info('runid=%s object=%r imagetype=%s obstype=%s readoutmode=%s' % (meta['control.runid'], meta['ob.object'], meta['emir.imagetype'], meta['emir.obstype'], instrument.das.mode.mode))
            #tslr = instrument.das.detector.time_since_last_reset()

            self.build_fits(name, instrument, meta, data)
            metavars['repeat'] += 1
        return names

    def build_fits(self, name, instrument, meta, data):
        hdul = instrument.factory(meta, data)
        hdul[0].scale('int16', bzero=32768)
        hdul.writeto(self.destdir + '/' + name, clobber=True)

    def post(self, instrument):
        #instrument.post()
        pass

    def mode_run(self, instrument, mode):
        self.pre(instrument)
        names = self._run(instrument, mode.exposure)
        self.post(instrument)
        return names

    def run(self, instrument, exposure):
        self.pre(instrument)
        names = self._run(instrument, exposure)
        self.post(instrument)
        return names

