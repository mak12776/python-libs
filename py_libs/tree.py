class Node:
    pass


class DataNode(Node):
    __slots__ = 'data'

    def __init__(self, data):
        self.data = data


class PairNode(Node):
    __slots__ = 'nodes'

    def __iter__(self, *nodes: Node):
        self.nodes = tuple(nodes)


class FixedTree:
    __slots__ = 'root', 'width'

    def __init__(self, width: int, root: Node):
        self.width = width
        self.root = root
