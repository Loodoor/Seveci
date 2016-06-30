import re
from enum import Enum
from utils import *


class TokenSpecification(Enum):
    def __init__(self, pattern):
        self.regex = pattern

    CALL = r'<<'  # priorité la plus haute au tokenizing
    CALL_FROM = r'::'

    OP = r'(\+|-|\*|/|%|\*\*|@@|@|@=|@~)'
    BINARYOP = r'(\&|\^|\|rshift|lshift)'
    COND = r'(<|>|==|<=|>=|!=|!)'

    NUMBER = r'\d+(\.\d*)?'
    STRING = r'"[^"]*?"'
    BOOL = r'(true|false)'

    ASSIGN = r'='
    LCURLY, RCURLY = r'{', r'}'
    BLOC_START, BLOC_END = r'\(', r'\)'
    ARRAY_START, ARRAY_END = r'\[', r'\]'

    COMMENT = r'#.*'

    ID = r'[A-Za-z_$][A-Za-z0-9_\?-]*'

    # CONTINUATION = r'\\'
    NEWLINE = r'(\n|\r|\r\n)'
    SKIP = r'[ \t]+'
    MISMATCH = r'.'  # priorité la plus basse au parsing


def tokenize(code):
    tok_regex = '|'.join('(?P<%s>%s)' % (str(name)[19:], name.regex) for name in TokenSpecification)
    line_start = 0
    continuation = False

    for line_num, line in enumerate(code):
        tokenized_line = [Token('BLOC_START', '(', line_num, 0)] if not continuation else tokenized_line
        continuation = False

        for mo in re.finditer(tok_regex, line):
            kind = mo.lastgroup
            value = mo.group(kind)

            if kind == 'MISMATCH':
                raise RuntimeError('%r unexpected on line %i, %s' % (value, line_num + 1, line))
            elif kind == 'NEWLINE':
                line_start = mo.end()
            elif kind == 'SKIP' or kind == 'COMMENT':
                pass
            elif kind == 'CONTINUATION':
                continuation = True
            else:
                if kind == 'ID' and value in keywords:
                    kind = 'kwtype'
                if kind == 'STRING':
                    value = value[1:-1]

                column = mo.start() - line_start
                tokenized_line.append(Token(kind, value, line_num + 1, column))

        if not continuation:
            tokenized_line.append(Token('BLOC_END', ')', line_num, 0))
            yield tokenized_line
