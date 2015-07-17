from conectsim.devices.device import Carrousel


class Wheel(Carrousel):
    def __init__(self, capacity, name=None, parent=None):
        super(Wheel, self).__init__(capacity, name=name, parent=parent)

    def turn(self):
        self._pos = (self._pos + 1) %  self._capacity
        self._current = self._container[self._pos]
        self.changed.emit(self._pos)

