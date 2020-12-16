from collections import deque
from typing import Iterable, List, Callable

from library import quoted, single_quoted

Test = str


class Way:
    __slots__ = 'test', 'target'

    def __init__(self, test: Test, target: 'Node'):
        self.test = test
        self.target = target

    def __repr__(self):
        return f"Way({quoted(self.test)}, {self.target})"


class Node:
    __slots__ = 'name', 'ways', 'jobs'

    def __init__(self, name: str, ways: Iterable = None, jobs: Iterable = None):
        self.name = name
        self.ways = deque() if ways is None else deque(ways)
        self.jobs = deque() if jobs is None else deque(jobs)

    def __repr__(self):
        class_name = self.__class__.__name__
        return f'{class_name}({quoted(self.name)})'

    def connect(self, test: Test, node: 'Node'):
        self.ways.append(Way(test, node))

    def add_job(self, job):
        self.jobs.append(job)


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
start_node.connect('GOTO', start_node)

left_curly_bracket.connect('END', single_left_curly_bracket)
left_curly_bracket.connect('EQ {', double_left_curly_bracket)
left_curly_bracket.connect('IN $digits', digits_after_curly_bracket)
left_curly_bracket.connect('EQ :', colon_after_curly_bracket)

double_left_curly_bracket.add_job('DEC total')
double_left_curly_bracket.connect('GOTO', start_node)

right_curly_bracket.connect('END or NE {', single_right_curly_bracket)
right_curly_bracket.connect('GOTO', double_right_curly_bracket)

double_right_curly_bracket.add_job('DEC total')
double_right_curly_bracket.connect('GOTO', start_node)

# now generating the code

new_list = deque

root = start_node


class ParseError(Exception):
    pass


is_end = 'index == len'
check_char: Callable[[str], str] = \
    lambda char: f'fmt[index] == {single_quoted(char)}'


def parse_words(words: List[str]):
    words_iter = iter(words)
    expressions = deque()
    for word in words_iter:
        if word == 'END':
            expressions.append(is_end)
        elif word == 'EQ':
            char = next(words_iter)
            expressions.append(check_char(char))
        elif word != 'or':
            continue
        else:
            raise ParseError(f'unknown word: {word}')
    if len(expressions) == 0:
        raise ParseError('no word found')
    if len(expressions) == 1:
        return expressions[0]
    return ' && '.format(f'({exp})' for exp in expressions)


def parse_test(test: str):
    return parse_words(test.split(' '))


for way in root.ways:
    print(parse_test(way.test))
