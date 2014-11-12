from byteplay import *
from pprint import pprint
import dis as dis
import types

def answer(x):
    return Answer(x)

iname = 0
SELF_NAME = "__SELF__"
RET_NAME = "__RET__"
BUILDING_NAME = "__BUILDING__"
STATE_NAME = "_K_state"

def cps(f):
    global iname
    c = Code.from_code(f.func_code)
    pprint(c.code)

    iname += 1
    cls_name = "_K_" + str(iname) + "_class"

    code = c.code
    ret_points = []
    locals = set(f.func_code.co_varnames[:f.func_code.co_argcount])
    print locals, "locals <<<--"
    i = 0
    while i < len(code):
        nm, arg = code[i]
        if nm == STORE_FAST:
            locals.add(arg)
        if nm == LOOKUP_METHOD:
            code[i] = (LOAD_ATTR, arg)

        if nm == CALL_METHOD:
            code[i] = (CALL_FUNCTION, arg)

        if nm == CALL_METHOD:
            op, arg = code[i - arg - 1]
            assert op == LOAD_ATTR
            if arg == "invoke":
                i += 1
                code.insert(i, (STORE_FAST, RET_NAME))
                i += 1
                code.insert(i, (LOAD_GLOBAL, cls_name))
                i += 1
                code.insert(i, (CALL_FUNCTION, 0))
                i += 1
                code.insert(i, (STORE_FAST, BUILDING_NAME))
                i += 1
                code.insert(i, (LOAD_FAST, RET_NAME))
                i += 1
                code.insert(i, (LOAD_FAST, BUILDING_NAME))
                i += 1
                code.insert(i, (STORE_ATTR, "_K_v"))
                i += 1
                code.insert(i, (LOAD_FAST, BUILDING_NAME))
                i += 1
                code.insert(i, (LOAD_CONST, len(ret_points) + 1))
                i += 1
                code.insert(i, (LOAD_FAST, BUILDING_NAME))
                i += 1
                code.insert(i, (STORE_ATTR, STATE_NAME))
                i += 1
                for x in locals:
                    code.insert(i, (LOAD_FAST, x))
                    i += 1
                    code.insert(i, (LOAD_FAST, BUILDING_NAME))
                    i += 1
                    code.insert(i, (STORE_ATTR, "_K_" + str(iname) + "_" +  x))
                    i += 1

                code.insert(i, (LOAD_FAST, BUILDING_NAME))
                i += 1
                code.insert(i, (RETURN_VALUE, None))
                i += 1
                lbl = Label()
                ret_points.append(lbl)
                code.insert(i, (lbl, None))
                i += 1
                code.insert(i, (LOAD_FAST, RET_NAME))
                i += 1

                for x in locals:
                    code.insert(i, (LOAD_FAST, BUILDING_NAME))
                    i += 1
                    code.insert(i, (LOAD_ATTR, "_K_" + str(iname) + "_" +  x))
                    i += 1
                    code.insert(i, (STORE_FAST, x))
                    i += 1

                print op, arg

        if nm == RETURN_VALUE:
            code.insert(i, (STORE_FAST, RET_NAME))
            i += 1
            code.insert(i, (LOAD_CONST, answer))
            i += 1
            code.insert(i, (LOAD_FAST, RET_NAME))
            i += 1
            code.insert(i, (CALL_FUNCTION, 1))
            i += 1


        i += 1

    i = 0
    for x in f.func_code.co_varnames[:f.func_code.co_argcount]:
        code.insert(i, (LOAD_FAST, BUILDING_NAME))
        i += 1
        code.insert(i, (LOAD_ATTR, "_K_" + str(iname) + "_" +  x))
        i += 1
        code.insert(i, (STORE_FAST, x))
        i += 1

    state_idx = 1
    for lbl in ret_points:
        i = 0
        code.insert(i, (LOAD_FAST, BUILDING_NAME))
        i += 1
        code.insert(i, (LOAD_ATTR, STATE_NAME))
        i += 1
        code.insert(i, (LOAD_CONST, state_idx))
        i += 1
        code.insert(i, (COMPARE_OP, "=="))
        i += 1
        exit_lbl = Label()
        code.insert(i, (POP_JUMP_IF_FALSE, exit_lbl))
        i += 1
        code.insert(i, (JUMP_ABSOLUTE, lbl))
        i += 1
        code.insert(i, (exit_lbl, None))

        state_idx += 1


    c = Code(code=code, freevars=[], args=[BUILDING_NAME, RET_NAME],
             varargs=False, varkwargs=False, newlocals=True, name=f.func_code.co_name,
             filename=f.func_code.co_filename, firstlineno=f.func_code.co_firstlineno,
             docstring=f.func_code.__doc__)

    new_func = types.FunctionType(c.to_code(), f.func_globals, "step")

    dis.dis(new_func)

    f.func_globals[cls_name] = type(cls_name, (Fn,), {"step": new_func})

    code = [(LOAD_GLOBAL, cls_name),
            (CALL_FUNCTION, 0),
            (STORE_FAST, BUILDING_NAME),
        (LOAD_CONST, 0),
        (LOAD_FAST, BUILDING_NAME),
        (STORE_ATTR, STATE_NAME)]

    for x in range(f.func_code.co_argcount):
        code.append((LOAD_FAST, f.func_code.co_varnames[x]))
        code.append((LOAD_FAST, BUILDING_NAME))
        code.append((STORE_ATTR, "_K_" + str(iname) + "_" +  f.func_code.co_varnames[x]))

    code.append((LOAD_FAST, BUILDING_NAME))
    code.append((LOAD_ATTR, "step"))
    code.append((LOAD_CONST, None))
    code.append((CALL_FUNCTION, 1))

    code.append((RETURN_VALUE, None))


    c = Code(code=code, freevars=[], args=f.func_code.co_varnames[:f.func_code.co_argcount],
             varargs=False, varkwargs=False, newlocals=True, name=f.func_code.co_name,
             filename=f.func_code.co_filename, firstlineno=f.func_code.co_firstlineno,
             docstring=f.func_code.__doc__)
    f.func_code = c.to_code()

    return f

class EffectOrAnswer(object):
    pass

class Answer(EffectOrAnswer):
    def __init__(self, w_val):
        self._w_val = w_val

class Fn(object):
    def invoke(self, x):
        return Answer(42)

