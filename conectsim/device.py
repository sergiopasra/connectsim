
import traceback
import itertools

import basenodes

from .element import Element

class Signal(object):
    '''Signal used for callbacks.'''
    def __init__(self):
        self.callbacks = []
    
    def connect(self, callback):
        self.callbacks.append(callback)
        return len(self.callbacks) - 1

    def delete(self, idx):
        self.callbacks.pop(idx)

    def emit(self, *args, **kwds):
        for c in self.callbacks:
            try:
                res = c(*args, **kwds)
                # we can use the result value
                # to disable this callback...
                # not yet implemented
            except TypeError:
                traceback.print_exc()

class Device(Element):
    def __init__(self, name=None, parent=None):

        self.parent = parent
        self.children = []

        if self.parent:
            self.parent.children.append(self)

        super(Device, self).__init__(name)

    def config_info(self):
        return {'name': self.name}

    def configure(self, meta):
        pass

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


class Carrousel(ConnectableDevice):
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

    def trace(self):

        c = self.current()
        print c, c.name
        if isinstance(c, basenodes.Source):
            return [c]

        if self.previousnode:
            return self.previousnode.trace() +  [c]
        return [c]


class Wheel(Carrousel):
    def __init__(self, capacity, name=None, parent=None):
        super(Wheel, self).__init__(capacity, name=name, parent=parent)

    def turn(self):
        self._pos = (self._pos + 1) %  self._capacity
        self._current = self._container[self._pos]
        self.changed.emit(self._pos)

