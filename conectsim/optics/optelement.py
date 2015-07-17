
from conectsim.element import ConnectableElement, Element
import basenodes

class OpticalElement(ConnectableElement):
    '''A generic optical element.'''
    def __init__(self, transmission, name=None):
        self.transmission_interp = transmission
        super(OpticalElement, self).__init__(name=name)

    def transform(self, illumination):
        '''Transform the illumination passing through.'''
        return illumination

    def entrance(self):
        return self

    def exit(self):
        return self


class Filter(OpticalElement):
    '''A filter.'''
    def __init__(self, transmission, name=None):
        super(Filter, self).__init__(transmission=transmission, name=name)


class Open(OpticalElement):
    def __init__(self, name=None):
        super(Open, self).__init__(transmission=None, name=name)


class Stop(Element, basenodes.Source):
    pass

