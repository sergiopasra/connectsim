#

from conectsim.optelement import OpticalElement

class Atmosphere(OpticalElement):
    def __init__(self):
        super(Atmosphere, self).__init__(None, name='atmosphere')
