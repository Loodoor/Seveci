from collections import namedtuple
import math
import time
import operator as op


Token = namedtuple('Token', ['typ', 'value', 'line', 'column'])
keywords = (
    "function", "struct", "if", "else", "while"
)
types = ('NUMBER', 'STRING', 'BOOL', 'ARRAY', 'DICT')
postfix_int = ('++', '--')
postfix_others = ('@@', ':~')
POSTFIX = postfix_int + postfix_others
ASSIGNERS = ('=', ':=')


class T:
    def __init__(self):
        pass

    def meth(self):
        pass

t = T()


class ParseError(Exception):
    pass


class TokenizingError(Exception):
    pass


class StructConstructionError(Exception):
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
        '&&': lambda a, b: a and b,

        # listes
        '@': op.getitem, '@=': lambda lst, v: op.setitem(lst, v[0], v[1]), '@~': op.delitem, 'length': len,
        '@@': lambda x: x[1:], 'count': lambda x, y: x.count(y),
        'cons': lambda x, y: [x] + y if not isinstance(x, list) and isinstance(y, list) else x + [y],
        'setitem': op.setitem,

        # strings
        'split': lambda x, y: x.split(y), 'concat': lambda *x: "".join(str(c) for c in x),

        # autres
        'time': time.time, 'round': round, 'abs': abs, 'zip': lambda *x: list(zip(*x)),
        'map': lambda *x: list(map(*x)), 'max': max, 'min': min,
        'print': lambda *x: print(mtoa(*x), flush=True), 'printc': lambda x: print(x, end='', flush=True), 'input': input,
        'include': lambda x: _env.update({x: __import__(x)}),

        # fichiers
        'open-input-file': lambda f: open(f, 'r'), 'open-output-file': lambda f: open(f, 'w'), 'close-file': lambda f: f.close(),
        'read-file': lambda f: f.read(), 'write-in-file': lambda f, s: f.write(s),

        # types
        'int': lambda x: int(x), 'float': lambda x: float(x), 'number?': lambda x: isinstance(x, (int, float)),
        'bool': lambda x: bool(x), 'bool?': lambda x: isinstance(x, bool),
        'str': lambda x: str(x), 'str?': lambda x: isinstance(x, str),
        'list': lambda *x: list(x), 'list?': lambda x: isinstance(x, list),
        'dict': lambda k, v: dict(zip(k, v)), 'dict?': lambda x: isinstance(x, dict),
        'type': lambda x: type(x).__name__,

        # constantes
        '$10': '\n', '$13': '\r', '$9': '\t',
    })
    return _env


def reduce_parsed(parsed):
    if parsed:
        while isinstance(parsed[0], list) and len(parsed) == 1:
            parsed = parsed[0]
    return parsed


def split_toks_kind(line, kind):
    w = []

    for tok in line:
        if not isinstance(tok, Token) or tok.typ != kind:
            w.append(tok)

    return w


def tok_kind_in(line, kind):
    for tok in line:
        if isinstance(tok, list):
            t = tok_kind_in(tok, kind)
            if t:
                return t
            pass
        elif tok.typ == kind:
            return True
    return False


def indexof_tok_kind(line, kind):
    for i, tok in enumerate(line):
        if tok.typ == kind:
            return i
    return -1


def count_toks_kind(line, kind):
    tot = 0

    for tok in line:
        if tok.typ == kind:
            tot += 1

    return tot


def assemble(toks):
    return " ".join(i.value for i in toks)


def atom(tok):
    value = tok.value
    if tok.typ == 'BOOL':
        if tok.value == 'true':
            value = True
        elif tok.value == 'false':
            value = False
    if tok.typ == 'NUMBER':
        try:
            value = int(tok.value)
        except ValueError:
            try:
                value = float(tok.value)
            except ValueError:
                try:
                    value = complex(tok.value.replace('i', 'j', 1))
                except ValueError:
                    pass
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


def print_d(dct, i=0):
    for k, v in dct.items():
        if not isinstance(v, dict):
            print("\t" * i + "'%s' : %s," % (k, v))
        else:
            print("\t" * i, "'%s' :" % k)
            print_d(v, i + 1)


def is_ok(obj):
    if obj is not None and obj != []:
        return True
    return False


def require(cond, error):
    if not cond:
        raise error
