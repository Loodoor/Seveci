from utils import *


def transpile(psource, out, **kwargs):
    for tok in psource:
        if not isinstance(tok, list):
            # we can parse it to python
            if tok.typ == 'ID':
                if tok.value not in ('include', 'length', 'printc', 'load') and tok.value[-1] != '?':
                    out.append(tok.value)
                else:
                    if tok.value == 'include':
                        out.append("__import__")
                    elif tok.value == 'length':
                        out.append('len')
                    elif tok.value == 'printc':
                        out.append('print')
            elif tok.typ in ('NUMBER', 'STRING', 'BOOL', 'ARRAY'):
                out.append(str(atom(tok).value))
            elif tok.typ == 'ASSIGN':
                out.append("=")
            elif tok.typ == 'CALL':
                out.append('(')
            elif tok.typ == 'CALL_FROM':
                out.append('.')
            elif tok.typ in ('OP', 'BINARYOP', 'COND'):
                if tok.value not in ('@@', '@', '@~', 'rshift', 'lshift'):
                    out.append(tok.value)
                else:
                    if tok.value == 'rshift':
                        out.append('>>')
                    elif tok.value == 'lshift':
                        out.append('<<')
                    elif tok.value == '@':
                        out.append('[')
                    elif tok.value == '@@':
                        out.append('*')
                    elif tok.value == '@~':
                        out.append('del')
            elif tok.typ == 'kwtype':
                if tok.value == 'function':
                    pass
                elif tok.value == 'struct':
                    pass
                elif tok.value == 'alias':
                    pass
        else:
            w = []
            transpile(tok, w)
            # some work to do with w
            out.append(" ".join(w))
