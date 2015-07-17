__author__ = 'spr'

import conectsim
import conectsim.detector
import conectsim.devices.shutter
import conectsim.devices.wheel
from conectsim.devices.device import ConnectableDevice
from conectsim.optics.vph import VPHGrating
from conectsim.optics.optelement import Stop, Open
from conectsim.devices.pseudoslit import PseudoSlitSelector
from conectsim.optics.fiberlayout import FiberBundle
from conectsim.devices.calibration import LampCarrousel
from conectsim.devices.device import Switch
from conectsim.telescope import Telescope
from conectsim.optics.obscond import Atmosphere

class Spectrograph(ConnectableDevice):
    def __init__(self):
        super(Spectrograph, self).__init__(name='spec')
        self.shutter = conectsim.devices.shutter.Shutter(parent=self)
        self.wheel = conectsim.devices.wheel.Wheel(4, name='wheel', parent=self)
        for idx in range(self.wheel._capacity):
            self.wheel.put_in_pos(VPHGrating('VPH%d'% idx), idx)


        self.detector = conectsim.detector.CDetector(2048, 2048, 24.0, 1.0)
        self.detector.set_parent(self)

        self.shutter.connect(self.wheel)
        assert self.shutter.nextnode is self.wheel
        assert self.wheel.previousnode is self.shutter

        self.wheel.connect(self.detector)

        self.last = self.detector

    def trace(self):
        return self.last.trace()

    def head(self):
        return self.shutter


class MyInstrument(ConnectableDevice):
    def __init__(self):
        super(MyInstrument, self).__init__(name='my')

        my = Spectrograph()
        my.configure({'shutter': 1, 'wheel': 2})

        pslit = PseudoSlitSelector(4)
        pslit.put_in_pos(Open(name='pslit open'), 0)
        pslit.put_in_pos(Stop(name='pslit stop'), 1)
        pslit.put_in_pos(FiberBundle(name='LCB'), 2)
        pslit.put_in_pos(FiberBundle(name='MOS'), 3)

        pslit.configure(2)

        pslit.connect(my)

        cswitch = Switch(3, "c")

        self.open1 = Open(name='pslit open')
        cswitch.connect_to_pos(self.open1, 0)

        lampc1 = LampCarrousel(2, name='lamps1')
        lampc1.put_in_pos("HAL1", 0)
        lampc1.put_in_pos("HAL2", 1)

        cswitch.connect_to_pos(lampc1, 1)


        lampc2 = LampCarrousel(2, name='lamps1')
        lampc2.put_in_pos("ARC1", 0)
        lampc2.put_in_pos("ARC2", 1)

        cswitch.connect_to_pos(lampc2, 2)

        cswitch.connect(pslit)

        cswitch.configure(2)


        self.last = my

    def trace(self):
        return self.last.trace()

    def head(self):
        return self.open1


my = MyInstrument()

telescope = Telescope(10, 1)

telescope.connect(my)

atmosphere = Atmosphere()

atmosphere.connect(telescope)

print my.trace()