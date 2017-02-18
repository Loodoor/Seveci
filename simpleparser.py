import tokenizer
from utils import *


class Procedure(object):
    def __init__(self, params, body, envi, dispatch=False):
        self.params, self.body, self.env, self.dispatch = params, body, envi, dispatch
        self.params = [p.value for p in self.params]

    def __call__(self, *args):
        env = Env(self.params, args, outer=self.env, dispatch=self.dispatch)
        if self.body[:-1]:
            for line in self.body[:-1]:
                evaluate([line] if not isinstance(line, list) else line, env)
        ret = evaluate([self.body[-1]] if not isinstance(self.body[-1], list) else self.body[-1], env)
        for k, v in self.env.items():
            if k in env.keys():
                self.env[k] = env[k]
        return ret


class Struct(object):
    def __init__(self, outer):
        self.outer = outer
        self.env = Env(outer=self.outer)

    def __call__(self, *args):
        try:
            ret = self.env["create"]
        except KeyError as ker:
            raise StructConstructionError("Missing entry point 'create'") from ter
        else:
            ret = ret(*args)
            envi = Env()
            envi.update({k: v for k, v in self.env.items()})

            self.env = Env(outer=self.outer)
            self.env.update(envi)
            return envi



def isfunc(m):
    return isinstance(m, (type(lambda: None), type(abs), Procedure, type(t.meth)))


def evaluate(parsed_line, env):
    def eval_math(line):
        nonlocal env
        if isinstance(line, list):
            f, _op, *ts = line

            if len(ts) == 1:
                s = ts[0]
            elif not len(ts):
                s = None
            else:
                s = eval_math(ts)

            if _op.value not in ASSIGNERS + POSTFIX + ('<<',):
                z = env.find(_op.value)(eval_math(f), eval_math(s))
            else:
                z = evaluate(line, env)
            return z
        elif isinstance(line, Token):
            return line.value if line.typ != 'ID' else env.find(line.value)
        return line

    def eval_callfrom(line):
        w = split_toks_kind(line, 'CALL_FROM')

        if not tok_kind_in(w, 'CALL'):
            return [e.value for e in w], []
        iof = indexof_tok_kind(w, 'CALL')
        if iof != -1:
            return [e.value for e in w[:iof]], w[1 + iof:]

    def consume_modules(main, modules):
        nonlocal env
        _module = env.find(main)
        try:
            require(type(_module).__name__ == 'module', ValueError("Module unreachable"))
            m = modules.pop(0)
            ens = dict(vars(_module))[m]
            while type(ens).__name__ == 'module':
                require(len(modules), RuntimeError("Can't call a module ('%s')" % m))
                m = modules.pop(0)
                ens = dict(vars(ens))[m]
            return ens
        except ValueError as ver:
            try:
                require(isinstance(_module, dict), ValueError("Undefined. Can not call that thing, sorry."))
                m = modules.pop(0)
                return _module.find(m)
            except ValueError as ver2:
                if str(type(_module))[1:6] == 'class':
                    if len(modules) == 1:
                        return getattr(_module, modules[0])
                    raise ValueError("Too much sub modules")

    if len(parsed_line):
        parsed_line = reduce_parsed(parsed_line)
    else:
        return  # there is no use to parse an empty bloc

    if len(parsed_line) > 1 and isinstance(parsed_line[0], list) and tok_kind_in(parsed_line, 'CALL'):
        o = reduce_parsed(parsed_line.pop(0))
        temp = evaluate(o, env)
        parsed_line.insert(0, Token('PROC', temp, o[0].line, o[0].column - 1))

    if len(parsed_line) > 1 and isinstance(parsed_line[1], Token) and parsed_line[1].typ in ('OP', 'BINARYOP', 'COND'):
        require(len(parsed_line) >= 3,
            ValueError("Missing arguments for %s, line: %i" % (parsed_line[1].value, parsed_line[1].line)))
        return eval_math(parsed_line)
    if parsed_line[0].typ in ('ID', 'PROC') and len(parsed_line) > 1:
        if parsed_line[0].value == 'load':
            _env = Env()
            with open(evaluate([parsed_line[2]], env)) as sr:
                code = sr.read()
            ts = [tok for tok in tokenizer.tokenize(code) if is_ok(tok)]
            ps = [p for p in [parse(code, toks) for toks in ts] if is_ok(p)]
            evaluate(ps, _env)
            return _env
        if parsed_line[1].typ == 'CALL':
            require(env.find(parsed_line[0].value) or parsed_line[0].typ == 'PROC',
                RuntimeError("'%s' does not exist, line: %i" % (parsed_line[0].value, parsed_line[0].line)))
            val = env.find(parsed_line[0].value) if parsed_line[0].typ == 'ID' else parsed_line[0].value
            dispatch = False
            if len(parsed_line[2:]) and get_first(parsed_line[2:]).typ == 'DISPATCH':
                require(len(parsed_line[2:]) == 2,
                    RuntimeError("Can not dispatch more than one argument"))
                dispatch = True
                parsed_line.pop(2)
                require(parsed_line[2].typ in COLLECTIONS,
                    TypeError("Can not dispatch an argument of type {}".format(parsed_line[2].typ)))
            args = [evaluate([bloc] if not isinstance(bloc, list) else bloc, env) for bloc in parsed_line[2:]]
            return val(*args) if not dispatch else val(*args[0])
    if parsed_line[0].typ in ('ID', 'PROC'):
        if len(parsed_line) > 1:
            if parsed_line[1].typ == 'CALL_FROM':
                callfrom, args = eval_callfrom(parsed_line)
                module, end = callfrom[0], callfrom[1:]
                dispatch = False
                if args:
                    if get_first(args).typ == 'DISPATCH':
                        require(len(args) == 2,
                            RuntimeError("Can not dispatch more than one argument"))
                        dispatch = True
                        args.pop(0)
                        require(args[0].typ in COLLECTIONS,
                            TypeError("Can not dispatch an argument of type {}".format(args[0].typ)))
                    args = [evaluate([a] if not isinstance(a, list) else a, env) for a in args]
                m = consume_modules(module, end)
                return m(*args) if isfunc(m) and not dispatch else m(*args[0]) if dispatch else m
            if parsed_line[1].typ == 'ASSIGN_ONLY':
                if env.find(parsed_line[0].value) is None:
                    env[parsed_line[0].value] = evaluate(parsed_line[2:], env)
                    return True
                return False
            if parsed_line[1].typ == 'ASSIGN':
                env[parsed_line[0].value] = evaluate(parsed_line[2:], env)
                return env[parsed_line[0].value]
            if parsed_line[1].typ == 'POSTFIX_OP':
                if parsed_line[1].value in postfix_int:
                    old = evaluate([parsed_line[0]], env)
                    old = old if old is not None else 0
                    value = +1
                    if parsed_line[1].value == '--':
                        value = -1
                    env[parsed_line[0].value] = old + value
                    return env[parsed_line[0].value]
                elif parsed_line[1].value in postfix_others:
                    return env.find(parsed_line[1].value)(evaluate([parsed_line[0]], env))
        return env.find(parsed_line[0].value)
    if parsed_line[0].typ == 'kwtype':
        if parsed_line[0].value == 'function':
            dispatch = get_first(parsed_line[1])
            dispatch = dispatch and dispatch.typ == 'DISPATCH'
            if dispatch:
                parsed_line[1].pop(0)
                require(len(parsed_line[1]) == 1,
                    DispatchError("Can not dispatch multiple variables on more than one argument"))
            for supposed_arg in parsed_line[1]:
                require(supposed_arg.typ == 'ID',
                    SyntaxError("'%s' should be an ID, not '%s'. Line: %i" % (supposed_arg.value, supposed_arg.typ, supposed_arg.line)))
            return Procedure(parsed_line[1], parsed_line[2:], env, dispatch=dispatch)
        if parsed_line[0].value == 'struct':
            obj = Struct(env)
            for bloc in parsed_line[1:]:
                evaluate([bloc] if not isinstance(bloc, list) else bloc, obj.env)
            return obj
        if parsed_line[0].value == 'if':
            require(len(parsed_line) >= 3,
                SyntaxError("Missing a part of the expression for 'if'. Line: %i" % parsed_line[0].line))
            cond = bool(evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env))
            ret, c = None, 0
            blocs = parsed_line[2:]
            for i, b in enumerate(blocs):
                if not isinstance(b, list) and b.value == 'else':
                    c = i
                    break
            if cond:
                for _, elem in enumerate(blocs[:c] if c else blocs):
                    ret = evaluate([elem] if not isinstance(elem, list) else elem, env)
            else:
                if c:
                    for _, elem in enumerate(blocs[c:]):
                        ret = evaluate([elem] if not isinstance(elem, list) else elem, env)
            return ret
        if parsed_line[0].value == 'while':
            require(len(parsed_line) >= 3,
                SyntaxError("Missing a part of the expression for 'while'. Line: %i" % parsed_line[0].line))
            cond = lambda: bool(evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env))
            while cond():
                for expr in parsed_line[2:]:
                    evaluate([expr] if not isinstance(expr, list) else expr, env)
            return None
    if parsed_line[0].typ in types:
        return atom(parsed_line[0]).value
    return None


def check_parsing(required_tok_type, repr_of_type):
    check_parsing.order = []
    def decorator(parser):
        def checker(context, tokens):
            check_parsing.order.append([parser.__name__, tokens[:]])
            try:
                _tokens = tokens[:]

                res = parser(context, tokens)

                last = tokens.pop(0)
                line = "%s\n" % context[last.line - 1]
                line += " " * last.column + "^" * len(last.value) + "\n"
                require(last.typ == required_tok_type, SyntaxError("Expected '%s'\n%s" % (repr_of_type, line)))

                return res
            except IndexError as exc:
                print("***")
                print_r(check_parsing.order)
                print("***")
                raise ParseError("Can't continue to parse.\nLine: %i, %s" % (_tokens[-1].line, assemble(_tokens)))
        return checker
    return decorator


@check_parsing('DICT_END', '}')
def parse_dict(context, tokens):
    hashmap = {}
    first = get_first(tokens)

    key = True
    t_key = ""
    while tokens[0].typ != 'DICT_END':
        val = parse(context, tokens)

        if key and val.typ != 'DICT_ASSIGN':
            t_key = val.value
        elif val.typ == 'DICT_ASSIGN' and key:
            key = False
            pass
        elif val is not None and t_key and not key:
            hashmap[t_key] = val.value
            t_key = ""
            key = True
    tok_hashmap = Token('DICT', hashmap, first.line, first.column)

    return tok_hashmap


@check_parsing('ARRAY_END', ']')
def parse_array(context, tokens):
    array = []
    first = get_first(tokens)

    while tokens[0].typ != 'ARRAY_END':
        val = parse(context, tokens)
        if val is not None:
            array.append(val)
    tok_array = Token('ARRAY', [t.value for t in array], first.line, first.column)

    return tok_array


@check_parsing('BLOC_END', ')')
def parse_bloc(context, tokens):
    ast = []

    while tokens[0].typ != 'BLOC_END':
        val = parse(context, tokens)
        if val is not None:
            ast.append(val)

    return ast


def parse(context, tokens):
    token = tokens.pop(0)
    require(token.typ != 'BLOC_END',
        SyntaxError("Unexpected '%s', line: %i, column: %i (instead of '(')\n%s" % (token.value, token.line, token.column, context[token.line - 1])))

    if token.typ == 'DICT_START':
        return parse_dict(context, tokens)
    elif token.typ == 'ARRAY_START':
        return parse_array(context, tokens)
    elif token.typ == 'BLOC_START':
        return parse_bloc(context, tokens)
    else:
        return atom(token)
