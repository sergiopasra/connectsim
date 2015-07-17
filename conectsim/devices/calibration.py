
from conectsim.devices.device import Carrousel


class CalibrationUnitSwitch(Carrousel):
    def __init__(self, parent=None):
        super(CalibrationUnitSwitch, self).__init__(3, name='cuselector', parent=parent)


class LampCarrousel(Carrousel):

    def transform(self, illumination):
        '''Transform the illumination passing through.'''
        return self._current.transform(illumination)

    def entrance(self):
        '''The entrance of the selected VPH'''
        return self._current

    def exit(self):
        '''The exit of the selected VPH'''
        return self._current
