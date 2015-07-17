
from conectsim.optelement import OpticalElement


class VPHGrating(OpticalElement):
    '''Volume-Phase Holographic (VPH) Grating.'''
    def __init__(self, name):
        transmission = 1.0
        super(VPHGrating, self).__init__(transmission, name=name)

    def __str__(self):
        return "VPHGrating(name='%s')" % self.name
    
    def __repr__(self):
        return "VPHGrating(name='%s')" % self.name
