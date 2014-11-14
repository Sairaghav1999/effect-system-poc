
class Object(object):
    """
    Base class of all Pixie Object
    """
    pass

class EffectObject(object):
    """
    Base class for all objects in the effect system. Not a Object so that the rtyper will catch
    at least some typing errors for us
    """
    _immutable_=True

class Effect(EffectObject):
    """
    Base class for any effects
    """
    _immutable_ = True
    pass

class Answer(EffectObject):
    """
    If an effect function wants to return an actual value, it should be wrapped in an Answer.
    """
    _immutable_=True
    def __init__(self, w_val):
        self._w_val = w_val

    def val(self):
        return self._w_val

class Handler(EffectObject):
    """
    Base class for all handlers.
    """
    _immutable_=True
    def handle(self, effect, k):
        """
        Handle the given affect, calling k when done. Return None if this effect is unhandled with this
        handler. This will cause the effect to bubble up to other handlers.
        """
        raise NotImplementedError()

class Thunk(EffectObject):
    """
    A trampoline. Returning a Thunk will cause control to bubble up to the top of the interpreter before
    being executed.
    """
    _immutable_=True
    def execute_thunk(self):
        raise NotImplementedError()

    def get_loc(self):
        return (None, None)

class Continuation(object):
    """
    Defines a computation that should be continued after a given effect has executed.
    """
    _immutable_= True
    def step(self, x):
        """
        Continue execution, x is the value returned by the effect.
        """
        raise NotImplementedError()

class Fn(Object):
    """
    An app-level callable.
    """
    _immutable_ = True
    def invoke_(self, args):
        raise NotImplementedError()

def answer(x):
    """
    Construct an answer that returns x
    """
    return Answer(x)

def raise_(x, k):
    """
    Used inside @cps transformed functions, recognized by @cps, and the k is automatically supplied. Cannot be called
    in return position. Use thusly

    @cps
    def foo_(x):
      if not x:
        effect = SomeEffect(x)
        result = raise_(effect)  ## @cps provides k to raise_ here

      else:
        result = Integer(42)

      return result

    """
    x._k = k
    return x

def handle_with(handler, effect, k):
    """
    Installs a handler into the effect stack so that both k and effect are handed to handler after effect has executed.
    """
    assert isinstance(effect, EffectObject)
    if isinstance(effect, Thunk):
        return CallEffectFn(handler, effect, k)
    else:
        ret = handler.handle(effect, k)
        if ret is None:
            without = effect.without_k()
            without._k = HandledEffectExecutingContinuation(handler, effect, k)

            return without
        else:
            return ret

class ContinuationThunk(Thunk):
    """
    An Thunk that simply calls k with the provided value.
    """
    _immutable_ = True
    def __init__(self, k, val):
        self._k = k
        self._val = val

    def execute_thunk(self):
        return self._k.step(self._val)

class HandledEffectExecutingContinuation(Continuation):
    """
    Extracts the continuation from the effect and creates a continuation that passes the value to the effect continuation.
    The result of calling the effect is then handles with handler before continuing with k. In essence this converts a
    handler, effect and continuation into a single continuation.
    """
    _immutable_ = True
    def __init__(self, handler, effect, k):
        self._k = k
        self._effect_k = effect._k
        self._handler = handler

    def step(self, val):
        return handle_with(self._handler, ContinuationThunk(self._effect_k, val), self._k)


class ConstantValContinuation(Continuation):
    """
    Creates a Continuation that always receives a constant value
    """
    def __init__(self, val, k):
        self._w_val = val
        self._w_k = k

    def step(self, _):
        return self._w_k(self._w_val)


def handle(effect, k):
    return handle_with(default_handler, effect, k)

class CallEffectFn(Thunk):
    """
    Assumes effect is a thunk, calls it then handles it continuing with k.
    """
    _immutable_ = True
    def __init__(self, handler, effect, k):
        self._handler = handler
        self._k = k
        self._effect = effect

    def execute_thunk(self):
        return handle_with(self._handler, self._effect.execute_thunk(), self._k)

    def get_loc(self):
        return self._effect.get_loc()


class HandleRecFn(Handler):
    """
    Internal class for handling recursive effects.
    """
    _immutable_ = True
    def __init__(self, handler, k):
        self._handler = handler
        self._k = k

    def handle_rec(self, arg):
        return handle_with(self._handler, arg, self._k)

## End Handle With

## Default Handler

class DefaultHandler(Handler):
    """
    Defines a handler that calls the continuation when the effect is an Answer
    """
    _immutable_ = True
    def handle(self, effect, k):
        if isinstance(effect, Answer):
            return DefaultHandlerFn(k, effect.val())

default_handler = DefaultHandler()

class DefaultHandlerFn(Thunk):
    """
    Internal Thunk for default_handler
    """
    _immutable_ = True
    def __init__(self, k, val):
        assert isinstance(k, Continuation)
        self._val = val
        self._k = k

    def execute_thunk(self):
        return self._k.step(self._val)

    def get_loc(self):
        return (None, None)

## End Default Handler
