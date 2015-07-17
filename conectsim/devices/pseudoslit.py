
from conectsim.devices.device import Carrousel

class Slit(object):
    def __init__(self):
        self.pos_max = 65
        self.pos_min = -65

class PseudoSlitSelector(Carrousel):
    def __init__(self, capacity, parent=None):
        super(PseudoSlitSelector, self).__init__(capacity, name='pselector', parent=parent)
