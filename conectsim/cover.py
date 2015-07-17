
import numpy as np

from .device import ConnectableDevice, Signal

class HemiCover(ConnectableDevice):
    STATES = [0,1]
    NAMES = {'OPEN': 1,
             'CLOSED': 0}
    def __init__(self, name=None, parent=None):
        self._pos = 0 # Closed
        super(HemiCover, self).__init__(name=name, parent=parent)

        self.changed = Signal()
        self.opened = Signal()
        self.closed = Signal()

    def set(self, pos):
        if pos not in self.STATES:
            raise ValueError('%d is not a valid state' % pos)
        if pos != self._pos: # We have to move
            self.flip()

    def open(self):
        if self._pos == 0:
            self._pos = 1
            self.changed.emit(self._pos)
            self.opened.emit()

    def close(self):
        if self._pos == 1:
            self._pos = 0
            self.changed.emit(self._pos)
            self.closed.emit()

    def flip(self):
        self._pos += 1
        self._pos %= 2
        self.changed.emit(self._pos)
        if self._pos == 1:
            self.opened.emit()
        else:
            self.closed.emit()
            
    def pos(self):
        return self._pos
    
    def config_info(self):
        return {'name': self.name, 'position': self._pos, 
                'label': self.NAMES[self._pos]}

class FullCover(ConnectableDevice):
    # STATES = 00, 01, 10, 11 
    # FULL CLOSED, CLOSED LEFT, CLOSED RIGHT, FULL OPEN
    STATES = [0,1,2,3]
    def __init__(self, name=None, parent=None):
        super(FullCover, self).__init__(name, parent=parent)
        self.left = HemiCover(parent=self)
        self.right = HemiCover(parent=self)

        self.changed_left = self.left.changed
        self.opened_left = self.left.opened
        self.closed_left = self.left.closed

        self.changed_right = self.right.changed
        self.opened_right = self.right.opened
        self.closed_right = self.right.closed

    def flip(self):
        self.left.flip()
        self.right.flip()
        
    def open(self):
        self.left.open()
        self.right.open()
        
    def close(self):
        self.left.close()
        self.right.close()
        
    def close(self):
        self.left.close()
        self.right.close()
        
    def set(self, pos):
        if pos not in self.STATES:
            raise ValueError('%d is not a valid state' % pos)

        l_pos = pos // 2
        r_pos = pos % 2
        self.left.set(l_pos)
        self.right.set(r_pos)

    def pos(self):
        return 2 * self.left.pos() + self.right.pos()
     
    def config_info(self):
        return {'name': self.name, 'position': self.pos()}   


class C_Cover(FullCover):
    ''' MEGARA Cover'''
    NAMES = {'UNSET': 3,
              'LEFT': 2,
              'RIGHT': 1,
               'SET': 0}
  
    VALS = {3: lambda pos: np.ones(pos[:,0].shape, dtype='bool'),
             2: lambda pos: pos[:,0]<-0.7,
             1: lambda pos: pos[:,0]>0.7,
             0: lambda pos: np.zeros(pos[:,0].shape, dtype='bool')}

    def __init__(self, parent=None):
        self.mode = 'SET'
        super(C_Cover, self).__init__(name='cover', parent=parent)
        self.set(self.mode)

    def set(self, mode):
        if mode in self.NAMES.keys():
            pos = self.NAMES[mode]
            super(C_Cover, self).set(pos)
    
    def config_info(self):
        res = super(C_Cover, self).config_info()

        my_pos = res['position']

        for name, pos in self.NAMES.items():
            if pos == my_pos:
                res['label'] = name
                break
        else:
            res['label'] = 'UNKNOWN'
            
        return res
    
    def __call__(self, fiber_positions):
        return self.VALS[self.pos()](fiber_positions)

    def __repr__(self):
        return "Cover(mode='%s')" % self.mode
