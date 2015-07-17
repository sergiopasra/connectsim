
from conectsim.optics.optelement import OpticalElement

class FiberBundle(OpticalElement):
    def __init__(self, name):
       super(FiberBundle, self).__init__(transmission=1.0, name=name)

    def __repr__(self):
        return "FiberBundle(name='%s')" % self.name
