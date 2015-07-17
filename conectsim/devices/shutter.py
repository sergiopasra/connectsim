
from conectsim.devices.wheel import Wheel
from conectsim.optics.optelement import Stop, Open, Filter

class Shutter(Wheel):
    def __init__(self, parent=None):
        super(Shutter, self).__init__(capacity=3, name='shutter',
        parent=parent)
        self.put_in_pos(Stop(name='shutter closed'), 0) # FIXME
        self.put_in_pos(Open(name='shutter open'), 1) # FIXME
        # sorting order filter
        self.put_in_pos(Filter(transmission=None, name='filter'), 2) # FIXME
        self.move_to(1) # Open by default

    def configure(self, value):
        # Let's see what is value:
        # a string
        if isinstance(value, basestring):
            val = value.lower()
            if val == 'open':
                val = 1
            elif val == 'closed':
                val = 0
            elif val == 'filter':
                val = 2
            else:
                raise ValueError('Not allowed value %s', value)
        elif isinstance(value, (int, long)):
            val = value
        else:
            raise TypeError('Not allowed type %s', type(value))

        # Move to value
        self.move_to(val)

    def open(self):
        self.move_to(1)

    def filter(self):
        self.move_to(2)

    def close(self):
        self.move_to(0)

    def trace(self):
        if self.pos() == 0: # FIXME
            return [self.current()]

        if self.previousnode:
            return self.previousnode.trace() +  [self.current()]
        return [self.current()]


