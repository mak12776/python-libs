from collections import deque
from string import digits
from typing import Iterable

# classes
from library.fmt import single_quoted


class Test:
    __slots__ = 'test', 'target'

    def __init__(self, test: str, target: 'Node'):
        self.test = test
        self.target = target

    def __repr__(self):
        return f'Test({single_quoted(self.test), self.target})'


class Node:
    __slots__ = 'target', 'name', 'works', 'tests'

    def __init__(self, name: str, works: Iterable[str] = None,
                 tests: Iterable[Test] = None, target: 'Node' = None):
        self.name = name
        self.works = deque() if works is None else deque(works)
        self.tests = deque() if tests is None else deque(tests)
        self.target = target

    def add_work(self, work: str):
        self.works.append(work)

    def connect(self, test: str, node: 'Node'):
        self.tests.append(Test(test, node))

    def set_target(self, target: 'Node'):
        self.target = target

    def __repr__(self):
        return f'Node({single_quoted(self.name)})'


class ErrorNode(Node):
    pass


# nodes

start_node = Node('start')
return_total = Node("return total")

left_curly_bracket = Node('left curly bracket')
double_left_curly_bracket = Node('double left curly bracket')

right_curly_bracket = Node('right curly bracket')
double_right_curly_bracket = Node('double right curly bracket')

digits_after_curly_bracket = Node('digits after left curly bracket')

single_left_curly_bracket = ErrorNode('single left curly bracket')
single_right_curly_bracket = ErrorNode('single right curly bracket')

colon_after_curly_bracket = Node('colon node')

# connections

start_node.connect('END', return_total)
start_node.connect('EQ {', left_curly_bracket)
start_node.connect('EQ }', right_curly_bracket)
start_node.set_target(start_node)

left_curly_bracket.connect('END', single_left_curly_bracket)
left_curly_bracket.connect('EQ {', double_left_curly_bracket)
left_curly_bracket.connect(f'IN {digits}', digits_after_curly_bracket)
left_curly_bracket.connect('EQ :', colon_after_curly_bracket)

double_left_curly_bracket.add_work('DEC total')
double_left_curly_bracket.set_target(start_node)

right_curly_bracket.connect('END or NE {', single_right_curly_bracket)
right_curly_bracket.set_target(double_right_curly_bracket)

double_right_curly_bracket.add_work('DEC total')
double_right_curly_bracket.set_target(start_node)
