
def connect(node1, node2):
    node1.connect(node2)


class BaseNode(object):
    '''Something that can be connected to something else.'''
    def __init__(self, nin, nout, id=None):
        self.nin = nin
        self.nout = nout
        self.nextnode = None
        self.previousnode = None
        self.id = id

    def connect(self, node):
        if self.nout != node.nin:
            raise ValueError('%r not compatible with %r' % (self, node))

        self.nextnode = node.head()
        self.nextnode.set_tail(self)

    def head(self):
        return self

    def set_tail(self, node):
        self.previousnode = node

    def receive(self, token):
        newdata = self.transform(token)
        
        if self.nextnode is not None:
            return self.nextnode.receive(newdata)
        return newdata

    def transform(self, data):
        raise NotImplementedError

    def print_from_the_begining(self, i=0):
        if self.previousnode is not None:
            self.previousnode.print_from_the_begining(i+1)
        print self, i

    def current(self):
        return self

    def trace(self):
        if self.previousnode:
            return self.previousnode.trace() +  [self.current()]
        return [self.current()]

    def visit(self):
        node = self
        while node.previousnode is not None:
            node = node.previousnode

        if isinstance(node, Source):
            token = node.create()
            if node.nextnode:
                final = node.nextnode.receive(token)
        else:
            final = None

        return final


class Node(BaseNode):
    def __init__(self, id=None):
        super(Node, self).__init__(1, 1, id=id)


class Source(BaseNode):

    def __init__(self, id=None):
        super(Source, self).__init__(0, 1, id=id)

    def create(self):
        raise NotImplementedError

    def emit(self):
        newdata = self.create()
        if self.nextnode is not None:
            self.nextnode.receive(newdata)

    def trace(self):
        return [self.current()]


class Sink(BaseNode):
    def __init__(self, id=None):
        super(Sink, self).__init__(1, 0, id=id)

    def transform(self, data):
        raise NotImplementedError
