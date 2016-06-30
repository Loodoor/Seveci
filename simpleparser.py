from utils import *


class Procedure(object):
    def __init__(self, params, body, envi):
        self.params, self.body, self.env = params, body, envi
        self.params = [p.value for p in self.params]

    def __call__(self, *args):
        env = Env(self.params, args, outer=self.env)
        if self.body[:-1]:
            for line in self.body[:-1]:
                evaluate(line, env)
        return evaluate(self.body[-1], env)


def evaluate(parsed_line, env):
    def eval_math(line):
        nonlocal env
        if isinstance(line, list):
            f, _op, s = line
            return env.find(_op.value)(eval_math(f), eval_math(s))
        return line.value if not isinstance(line.value, str) else env.find(line.value)

    def eval_callfrom(line):
        w = []
        while True:
            if len(line) >= 3:
                f, _op, *s = line
            else:
                break
            w.append(f.value)
            if _op.typ != "CALL" and f.typ != "CALL":
                line = s
            else:
                line.pop(0)
                break
        line = [line] if not isinstance(line, list) else line
        w.append(line.pop(0).value)
        return '.'.join(w), line

    if len(parsed_line) > 1 and isinstance(parsed_line[1], Token) and parsed_line[1].typ in ('OP', 'BINARYOP', 'COND'):
        require(len(parsed_line) >= 3,
            ValueError("Missing arguments for %s, line: %i" % (parsed_line[1].value, parsed_line[1].line)))
        return eval_math(parsed_line)
    if parsed_line[0].typ == 'ID':
        if len(parsed_line) > 1:
            if parsed_line[1].typ == 'CALL_FROM':
                callfrom, args = eval_callfrom(parsed_line)
                module, end = callfrom.split('.', 1)
                if args:
                    t = args.pop(0)
                    require(t.typ == 'CALL',
                            SyntaxError("Arguments found. Require '<<' operator, got '%s'" % t.value))
                    args = [evaluate([a] if not isinstance(a, list) else a, env) for a in args]
                return dict(vars(env.find(module)))[end](*args)
            if parsed_line[1].typ == 'ASSIGN':
                if "alias" in env.keys():
                    require(parsed_line[0].value not in env["alias"].keys(), RuntimeError("Is already an alias, overwritting it would cause problems"))
                env[parsed_line[0].value] = evaluate(parsed_line[2:], env)
                return None
            if parsed_line[1].typ == 'CALL':
                require(env.find(parsed_line[0].value) or parsed_line[0].value in env["alias"].keys(),
                    RuntimeError("'%s' does not exist, line: %i" % (parsed_line[0].value, parsed_line[0].line)))
                val = parsed_line[0].value if env.find(parsed_line[0].value) is not None else env["alias"][parsed_line[0].value]
                return env.find(val)(*[evaluate([bloc] if not isinstance(bloc, list) else bloc, env) for bloc in parsed_line[2:]])
        return env.find(parsed_line[0].value)
    if parsed_line[0].typ == 'kwtype':
        if parsed_line[0].value == 'function':
            for supposed_arg in parsed_line[1]:
                require(supposed_arg.typ == 'ID',
                    SyntaxError("'%s' should be an ID, not '%s'. Line: %i" % (supposed_arg.value, supposed_arg.typ, supposed_arg.line)))
            return Procedure(parsed_line[1], parsed_line[2:], env)
        if parsed_line[0].value == 'if':
            require(3 <= len(parsed_line) <= 4,
                SyntaxError("Missing a part of the expression. Line: %i" % parsed_line[0].line))
            cond = evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env)
            if cond:
                return evaluate([parsed_line[2]] if not isinstance(parsed_line[2], list) else parsed_line[2], env)
            else:
                if len(parsed_line) == 4:
                    return evaluate([parsed_line[3]] if not isinstance(parsed_line[3], list) else parsed_line[3], env)
            return None
        if parsed_line[0].value == 'while':
            require(len(parsed_line) >= 3,
                SyntaxError("Missing a part of the expression. Line: %i" % parsed_line[0].line))
            while evaluate([parsed_line[1]] if not isinstance(parsed_line[1], list) else parsed_line[1], env):
                for expr in parsed_line[2:]:
                    evaluate([expr] if not isinstance(expr, list) else expr, env)
            return None
        if parsed_line[0].value == "alias":
            require(len(parsed_line) == 3, ValueError("'alias' missing an argument : method. Line: %i" % parsed_line[0].line))
            env["alias"][parsed_line[1].value] = parsed_line[2].value
    if parsed_line[0].typ in ('NUMBER', 'STRING', 'BOOL', 'ARRAY'):
        return parsed_line[0].value
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
                raise ParseError("Can't continue to parse.\nLine: %i, %s" % (_tokens[-1].line, context[_tokens[-1].line - 1]))
        return checker
    return decorator


@check_parsing('ARRAY_END', ']')
def parse_array(context, tokens):
    array = []

    while tokens[0].typ != 'ARRAY_END':
        val = parse_tokens(context, tokens)
        if val is not None:
            array.append(val)
    tok_array = Token('ARRAY', [t.value for t in array], token.line, token.column)

    return tok_array


@check_parsing('BLOC_END', ')')
def parse_bloc(context, tokens):
    ast = []

    while tokens[0].typ != 'BLOC_END':
        val = parse_tokens(context, tokens)
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
