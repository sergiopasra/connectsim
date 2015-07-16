
import basenodes
from .device import Wheel

class VPHWheel(Wheel):
    def __init__(self, capacity, parent=None):
        Wheel.__init__(self, capacity, name='wheel', parent=parent)

    def transform(self, illumination):
        '''Transform the illumination passing through.'''
        return self._current.transform(illumination)

    def entrance(self):
        '''The entrance of the selected VPH'''
        return self._current

    def exit(self):
        '''The exit of the selected VPH'''
        return self._current 
