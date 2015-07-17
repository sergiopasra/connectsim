
from conectsim.optelement import OpticalElement

class Fibers(OpticalElement):
    ''' Class encapsulating FIBER data. '''
    def __init__(self, transmission, length):
        self.length = length # Unused
        super(Fibers, self).__init__(transmission)
