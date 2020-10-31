from collections import deque
from typing import Iterable


# C Nodes

class BaseNode:
    pass


class IfNode(BaseNode):
    __slots__ = 'test', 'target'

    def __init__(self, test: str, target: 'BaseNode' = None):
        self.test = test
        self.target = target


class SwitchCase(BaseNode):
    __slots__ = 'tests', 'target'

    def __init__(self, tests: Iterable[str], target: 'BaseNode' = None):
        self.tests = tests
        self.target = target


class SwitchNode(BaseNode):
    __slots__ = 'value', 'cases'

    def __init__(self, value: str, cases: Iterable = None):
        self.value = value
        self.cases = deque() if cases is None else deque(cases)


class NormalNode(BaseNode):
    __slots__ = 'work', 'target'

    def __init__(self, work: str, target: 'BaseNode' = None):
        self.work = work
        self.target = target
