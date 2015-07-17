
import traceback
import itertools

import basenodes

from .element import Element
from .signal import Signal


class Device(Element):
    def __init__(self, name=None, parent=None):
        self.parent = parent
        self.children = []

        if self.parent:
            self.parent.children.append(self)

        super(Device, self).__init__(name)

    def config_info(self):
        info = {}
        for dev in self.children:
            info[dev.name] = dev.config_info()
        info['name'] = self.name
        return info

    def configure(self, meta):
        for dev in self.children:
            key = dev.name
            if key in meta:
                dev.configure(meta[key])

    def set_parent(self, newparent):
        if self.parent:
            self.parent.children.remove(self)
        self.parent = newparent
        if self.parent:
            self.parent.children.append(self)


class ConnectableDevice(Device, basenodes.Node):
    def __init__(self, name=None, parent=None):
        Device.__init__(self, name=name, parent=parent)
        basenodes.Node.__init__(self)


class ContainerDevice(ConnectableDevice):

    def trace(self):

        c = self.current()
        d = self
        while isinstance(c, ContainerDevice):
            d = c
            c = c.current()

        if isinstance(c, basenodes.Source):
            return [c]

        if d.previousnode:
            return d.previousnode.trace() +  [c]
        return [c]


class Carrousel(ContainerDevice):
    def __init__(self, capacity, name=None, parent=None):
        super(Carrousel, self).__init__(name=name, parent=parent)
        # Container is empty
        self._container = [None] * capacity
        self._capacity = capacity
        self._pos = 0
        # object in the current position
        self._current = self._container[self._pos]

        # signals
        self.changed = Signal()
        self.moved = Signal()

    def current(self):
        return self._current

    def pos(self):
        return self._pos

    def put_in_pos(self, obj, pos):
        if pos >= self._capacity or pos < 0:
            raise ValueError('position greater than capacity or negative')

        self._container[pos] = obj
        self._current = self._container[self._pos]

    def move_to(self, pos):
        if pos >= self._capacity or pos < 0:
            raise ValueError('Position %d out of bounds' % pos)

        if pos != self._pos:
            self._pos = pos
            self._current = self._container[self._pos]
            self.changed.emit(self._pos)
        self.moved.emit(self._pos)

    def select(self, name):
        # find pos of object with name
        for idx, item in enumerate(self._container):
            if item:
                if isinstance(item, basestring):
                    if item == name:
                        return self.move_to(idx)
                elif item.name == name:
                    return self.move_to(idx)
                else:
                    pass
        else:
            raise ValueError('No object named %s' % name)

    def config_info(self):
        if self._current:
            if isinstance(self._current, basestring):
                label = self._current
            else:
                label = self._current.name
        else:
            label = 'Unknown'
        return {'name': self.name, 'position': self._pos,
                'label': label}

    def configure(self, meta):
        self.move_to(meta)


class Switch(ContainerDevice):
    def __init__(self, capacity, name=None, parent=None):
        super(Switch, self).__init__(name=name, parent=parent)
        # Container is empty
        self._container = [None] * capacity
        self._capacity = capacity
        self._pos = 0
        # object in the current position
        self._current = self._container[self._pos]

        # signals
        self.changed = Signal()
        self.moved = Signal()

    def current(self):
        return self._current

    def head(self):
        return self

    def pos(self):
        return self._pos

    def connect_to_pos(self, obj, pos):
        if pos >= self._capacity or pos < 0:
            raise ValueError('position greater than capacity or negative')

        obj.connect(self)

        self._container[pos] = obj

        self._current = self._container[self._pos]



    def move_to(self, pos):
        if pos >= self._capacity or pos < 0:
            raise ValueError('Position %d out of bounds' % pos)
        if pos != self._pos:
            self._pos = pos
            self._current = self._container[self._pos]
            self.changed.emit(self._pos)

        self._current.connect(self)
        self.moved.emit(self._pos)


    def select(self, name):
        # find pos of object with name
        for idx, item in enumerate(self._container):
            if item:
                if isinstance(item, basestring):
                    if item == name:
                        return self.move_to(idx)
                elif item.name == name:
                    return self.move_to(idx)
                else:
                    pass
        else:
            raise ValueError('No object named %s' % name)

    def config_info(self):
        if self._current:
            if isinstance(self._current, basestring):
                label = self._current
            else:
                label = self._current.name
        else:
            label = 'Unknown'
        return {'name': self.name, 'position': self._pos,
                'label': label}

    def configure(self, meta):
        self.move_to(meta)




class Wheel(Carrousel):
    def __init__(self, capacity, name=None, parent=None):
        super(Wheel, self).__init__(capacity, name=name, parent=parent)

    def turn(self):
        self._pos = (self._pos + 1) %  self._capacity
        self._current = self._container[self._pos]
        self.changed.emit(self._pos)

