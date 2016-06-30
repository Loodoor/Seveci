from collections import namedtuple
import math
import time
import operator as op


Token = collections.namedtuple('Token', ['typ', 'value', 'line', 'column'])
keywords = (
    "function", "if", "while", "alias"
)


class ParseError(Exception):
    pass


class Env(dict):
    def __init__(self, parms=(), args=(), outer=None):
        super().__init__(self)
        self.update(zip(parms, args))
        self.outer = outer

    def __xor__(self, other):
        new = Env()
        for key in other:
            if key not in self:
                new[key] = other[key]
        return new

    def __and__(self, other):
        new = Env()
        for key in other:
            if key in self and key in other:
                new[key] = self[key]
        return new

    def __getitem__(self, var):
        return dict.__getitem__(self, var) if var in self else None

    def find(self, var):
        if var in self:
            return self[var]
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            return None


def standard_env():
    _env = Env()
    _env.update(vars(math))
    _env.update({
        # maths
        '+': op.add, '-': op.sub,
        '*': op.mul, '/': op.truediv,
        '//': op.floordiv, '%': op.mod,
        '**': lambda a, b: a ** b,

        # binaires
        '^': op.xor, '|': op.or_,
        '~': lambda a: ~a, '&': op.and_,
        'rshift': lambda a, b: a >> b, 'lshift': lambda a, b: a << b,

        # Conditions
        '>': op.gt, '<': op.lt, '>=': op.ge,
        '<=': op.le, '!=': op.ne, '==': op.eq,
        '!': lambda a: not a,

        # listes
        '@': op.getitem, '@=': op.setitem, '@~': op.delitem, 'length': len,
        'list': lambda *x: list(x), 'list?': lambda x: isinstance(x, list),
        '@@': lambda *x: x[1:], 'count': lambda x, y: x.count(y),
        'cons': lambda x, y: [x] + y if not isinstance(x, list) and isinstance(y, list) else x + [y],

        # strings
        'split': lambda x, y: x.split(y),

        # autres
        'time': time.time, 'round': round, 'abs': abs, 'zip': lambda *x: list(zip(*x)),
        'map': lambda *x: list(map(*x)), 'max': max, 'min': min,
        'print': lambda *x: print(mtoa(*x)), 'input': input,
        'include': lambda x: _env.update({x: __import__(x)}),
        'load': lambda x: (_env.update(load(x)), None)[1],

        # fichiers
        'open-input-file': open, 'open-output-file': lambda f: open(f, 'w'), 'close-file': lambda f: f.close(),
        'read-file': lambda f: f.read(), 'write-in-file': lambda f, s: f.write(s),

        # types
        'int': lambda x: int(x), 'float': lambda x: float(x), 'number?': lambda x: isinstance(x, (int, float)),
        'bool': lambda x: bool(x), 'bool?': lambda x: isinstance(x, bool),
        'str': lambda x: str(x), 'str?': lambda x: isinstance(x, str),
        'list?': lambda x: isinstance(x, list),

        # constantes
        '$10': "\n", "$13": "\r", "$9": "\t",

        # alias
        "alias": {"$": "load"}
    })
    return _env


def load(path):
    with open(path) as sr:
        code = sr.readlines()

    _env = standard_env()
    for line in code:
        if line.count(start_token) == line.count(end_token) and line.strip()[:2] != comment:
            parsed = parse(line)
            eval_code(parsed, _env)
    del code
    return _env


def atom(tok):
    if tok.value == 'true':
        value = True
    elif tok.value == 'false':
        value = False
    try:
        value = int(tok.value)
    except ValueError:
        try:
            value = float(tok.value)
        except ValueError:
            try:
                value = complex(tok.value.replace('i', 'j', 1))
            except ValueError:
                value = str(tok.value)
    return Token(tok.typ, value, tok.line, tok.column)


def mtoa(*tokens):
    work = ""
    for tok in tokens:
        if tok == True and isinstance(tok, bool):
            work += 'true'
        elif tok == False and isinstance(tok, bool):
            work += 'true'
        elif isinstance(tok, list):
            work += '(' + ' '.join(map(mtoa, tok)) + ')'
        elif isinstance(tok, complex):
            work += tok.replace('j', 'i')
        else:
            work += str(tok)
    return work


def print_r(array, i=0):
    for elem in array:
        if not isinstance(elem, list):
            print("\t" * i + str(elem))
        else:
            print("\t" * i, "-" * 4, i)
            print_r(elem, i + 1)


def is_ok(obj):
    if obj is not None and obj != []:
        return True
    return False


def require(cond, error):
    if not cond:
        raise error
