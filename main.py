import os
import argparse
import tokenizer
import simpleparser
from utils import *


arg_parser = argparse.ArgumentParser(
    prog='seveci',
    description="Tokenize, parse, and execute the given input file"
)
arg_parser.add_argument('--version', action='version',
                        version='%(prog)s 2.0')
arg_parser.add_argument('-p', '--path', dest='path', action='store',
                        help='the input file')
arg_parser.add_argument('-l', '--lex', dest='lex', action='store_true',
                   	    help='tokenize the given input file')
arg_parser.add_argument('-a', '--ast', dest='ast', action='store_true',
                   	    help='parse the given input file')
arg_parser.add_argument('-e', '--execute', dest='exe', action='store_true',
                        help='execute the given input file')
arg_parser.add_argument('-i', '--interpreter', dest='repl', action='store_true',
                        help='start an interpreter')
arg_parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='turn on debug mode')


def main(path="", lex=False, ast=False, exe=False, repl=False, debug=False):
    if debug:
        print("Debug mode on")

    if path:
        path = os.path.abspath(path)
        print("Opening {}".format(path))
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        print(" " * 7, "{} lines, {} characters".format(len(content.split('\n')), len(content)))

    if ast:
        lex = True
    if exe:
        lex = True
        ast = True

    tokens = None
    parsed = None

    if lex:
        if debug:
            print("[i] Creating tokens list,", end=" ")
        tokens = [tok for tok in tokenizer.tokenize(content) if is_ok(tok)]
        if debug:
            print(count_all_toks_in_list(tokens), "tokens")
        if not ast:
            print_r(tokens)
    if ast:
        if debug:
            print("[i] Creating abstract syntax tree,", end=" ")
        parsed = [p for p in [simpleparser.parse(content, toks) for toks in tokens] if is_ok(p)]
        if debug:
            print(len(parsed), "blocs")
        if not exe:
            print_r(parsed)
    if repl:
        print("Starting a REPL instance. Type !go to execute your code")
        env = standard_env()
        code = []
        while True:
            cmd = input('> ')
            if cmd != "!go":
                code.append(cmd)
            else:
                print("Executing code\n%s\n" % "\n".join(code))
                tokens = [t for t in tokenizer.tokenize("\n".join(code)) if is_ok(t)]
                parsed = [p for p in [simpleparser.parse("\n".join(code), toks) for toks in tokens] if is_ok(p)]
                for li in parsed:
                    try:
                        val = simpleparser.evaluate(li, env)
                        if val:
                            print(mtoa(val))
                    except Exception as exc:
                        print(exc)
                code = []
    if exe:
        if debug:
            print("[i] Executing\n\nOut:\n***\n")
        env = standard_env()
        for line in parsed:
            val = simpleparser.evaluate(line, env)
            if val and debug:
                print(mtoa(val))
        if debug:
            print("\n***")


if __name__ == '__main__':
    args = arg_parser.parse_args()
    main(**args.__dict__)
