
import traceback

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

