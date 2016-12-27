from utils import *


class Procedure(object):
    def __init__(self, params, body, envi):
        self.params, self.body, self.env = params, body, envi
        self.params = [p.value for p in self.params]

    def __call__(self, *args):
        env = Env(self.params, args, outer=self.env)
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
            ret = self.env["create"](*args)
            envi = Env()
            envi.update({k: v for k, v in self.env.items()})

            self.env = Env(outer=self.outer)
            self.env.update(envi)
            return envi
        except TypeError as ter:
            raise StructConstructionError("Missing entry point 'create'") from ter


def evaluate(parsed_line, env):
    def eval_math(line):
        nonlocal env
        if isinstance(line, list):
            f, _op, s = line
            return env.find(_op.value)(eval_math(f), eval_math(s))
        return line.value if line.typ != 'ID' else env.find(line.value)

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

    if len(parsed_line) > 1 and isinstance(parsed_line[1], Token) and parsed_line[1].typ in ('OP', 'BINARYOP', 'COND'):
        require(len(parsed_line) >= 3,
            ValueError("Missing arguments for %s, line: %i" % (parsed_line[1].value, parsed_line[1].line)))
        return eval_math(parsed_line)
    if parsed_line[0].typ == 'ID':
        if len(parsed_line) > 1:
            if parsed_line[1].typ == 'CALL_FROM':
                callfrom, args = eval_callfrom(parsed_line)
                module, end = callfrom[0], callfrom[1:]
                if args:
                    args = [evaluate([a] if not isinstance(a, list) else a, env) for a in args]
                m = consume_modules(module, end)
                return m(*args) if (isinstance(m, type(lambda:None)) or isinstance(m, type(abs))) else m
            if parsed_line[1].typ == 'ASSIGN':
                if "alias" in env.keys():
                    require(parsed_line[0].value not in env["alias"].keys(),
                            RuntimeError("'%s' is already an alias, overwritting it would cause problems" % parsed_line[0].value))
                env[parsed_line[0].value] = evaluate(parsed_line[2:], env)
                return None
            if parsed_line[1].typ == 'CALL':
                require(env.find(parsed_line[0].value) or parsed_line[0].value in env["alias"].keys(),
                    RuntimeError("'%s' does not exist, line: %i" % (parsed_line[0].value, parsed_line[0].line)))
                val = parsed_line[0].value if env.find(parsed_line[0].value) is not None else env["alias"][parsed_line[0].value]
                return env.find(val)(*[evaluate([bloc] if not isinstance(bloc, list) else bloc, env) for bloc in parsed_line[2:]])
            if parsed_line[1].typ == 'POSTFIX_OP':
                require(isinstance(env.find(parsed_line[0].value), (int, float)), TypeError("Require a number for a postfix operator"))
                value = +1
                if parsed_line[1].value == '--':
                    value = -1
                env[parsed_line[0].value] += value
                return env[parsed_line[0].value]
        return env.find(parsed_line[0].value)
    if parsed_line[0].typ == 'kwtype':
        if parsed_line[0].value == 'function':
            for supposed_arg in parsed_line[1]:
                require(supposed_arg.typ == 'ID',
                    SyntaxError("'%s' should be an ID, not '%s'. Line: %i" % (supposed_arg.value, supposed_arg.typ, supposed_arg.line)))
            return Procedure(parsed_line[1], parsed_line[2:], env)
        if parsed_line[0].value == 'struct':
            obj = Struct(env)
            for bloc in parsed_line[1:]:
                evaluate([bloc] if not isinstance(bloc, list) else bloc, obj.env)
            return obj
        if parsed_line[0].value == 'if':
            require(len(parsed_line) >= 3,
                SyntaxError("Missing a part of the expression for 'if'. Line: %i" % parsed_line[0].line))
            cond = evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env)
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
            while evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env):
                for expr in parsed_line[2:]:
                    evaluate([expr] if not isinstance(expr, list) else expr, env)
            return None
        if parsed_line[0].value == "alias":
            require(len(parsed_line) == 3, ValueError("'alias' missing an argument : method. Line: %i" % parsed_line[0].line))
            env["alias"][parsed_line[1].value] = parsed_line[2].value
    if parsed_line[0].typ in ('NUMBER', 'STRING', 'BOOL', 'ARRAY'):
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


@check_parsing('ARRAY_END', ']')
def parse_array(context, tokens):
    array = []

    while tokens[0].typ != 'ARRAY_END':
        val = parse(context, tokens)
        if val is not None:
            array.append(val)
    tok_array = Token('ARRAY', [t.value for t in array], array[0].line, array[0].column)

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
    token = tokens.pop(0)  # on enlève le premier token qui doit etre un '('
    # require(token.typ != 'BLOC_END',
        # SyntaxError("Unexpected '%s', line: %i, column: %i (instead of '(')\n%s" % (token.value, token.line, token.column, context[token.line - 1])))

    if token.typ == 'ARRAY_START':
        return parse_array(context, tokens)
    elif token.typ == 'BLOC_START':
        return parse_bloc(context, tokens)
    else:
        return atom(token)
