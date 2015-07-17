import itertools

class Element(object):
    '''A generic device.'''

    _idx = itertools.count(0)

    def __init__(self, name=None):
        self._my_id = self._idx.next()

        if name is None:
            self.name = 'element%d' % self._my_id
        else:
            self.name = name

        super(Element, self).__init__()
