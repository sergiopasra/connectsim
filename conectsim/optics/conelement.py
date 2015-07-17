
from conectsim.devices.element import Element
from conectsim.optics import basenodes


class ConnectableElement(Element, basenodes.Node):
    def __init__(self, name=None):
        Element.__init__(self, name=name)
        basenodes.Node.__init__(self)
