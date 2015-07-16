
from .optelement import OpticalElement
from .device import ConnectableDevice

class Telescope(OpticalElement, ConnectableDevice):
    '''A Telescope.'''
    def __init__(self, diameter, transmission):
        ConnectableDevice.__init__(self)
        OpticalElement.__init__(self, transmission)
        self.diameter = diameter
