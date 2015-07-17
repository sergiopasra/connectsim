
from __future__ import division

import logging
from datetime import datetime

from conectsim.devices.device import Device


class DataAdquisitionSystem(Device):
    def __init__(self, detector):
        super(DataAdquisitionSystem, self).__init__(name='das')
        self.detector = detector
        self.meta = {}
    #    f1 = self.detector.readout
    #    f2 = self.detector.reset
    #    self.ops = {'read': f1, 'reset': f2}
        
        now = datetime.now()
        self.meta['dateobs'] = now.isoformat()
        #self.meta['mjdobs'] = datetime_to_mjd(now)
        self.meta['elapsed'] = 0
        self.meta['darktime'] = 0
        
    def config_info(self):
        return self.meta

    def pre(self):
        pass

    def post(self):
        pass
    
    def run(self, exposure):
        now = datetime.now()
        self.meta['dateobs'] = now.isoformat()
        data = self.detector.expose(exposure)
        #    _logger.info('at %s %s %s', time, self.detector.time_since_last_reset(), op)
        #    self.meta['elapsed'] = self.detector.time_since_last_reset()
        #    self.meta['darktime'] = self.detector.time_since_last_reset()
        yield data

