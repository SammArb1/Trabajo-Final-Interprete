# SISTEMA DE TIPOS Y OBJETOS DEL INTÉRPRETE
# Cada clase hereda de Obj y expone type() e inspect() para el runtime.

class ObjType:
    INTEGER      = "INTEGER"
    FLOAT        = "FLOAT"
    BOOLEAN      = "BOOLEAN"
    STRING       = "STRING"
    NULL         = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    ERROR        = "ERROR"
    FUNCTION     = "FUNCTION"
    ARRAY        = "ARRAY"
    BUILTIN      = "BUILTIN"
    BREAK_VALUE  = "BREAK_VALUE"

class Obj:
    def type(self):    pass
    def inspect(self): pass

class Integer(Obj):
    def __init__(self, value):
        self.value = value
    def type(self):    return ObjType.INTEGER
    def inspect(self): return str(self.value)
    def __eq__(self, other):
        # Comparación por valor numérico; acepta Float para operaciones mixtas
        return isinstance(other, (Integer, Float)) and self.value == other.value

class Float(Obj):
    def __init__(self, value):
        self.value = float(value)   # normalización garantizada
    def type(self):    return ObjType.FLOAT
    def inspect(self): return str(self.value)
    def __eq__(self, other):
        # Comparación por valor numérico; acepta Integer para operaciones mixtas
        return isinstance(other, (Float, Integer)) and self.value == other.value

class StringObj(Obj):
    def __init__(self, value):
        self.value = value
    def type(self):    return ObjType.STRING
    def inspect(self): return self.value
    def __eq__(self, other):
        return isinstance(other, StringObj) and self.value == other.value

class BooleanVal(Obj):
    def __init__(self, value):
        self.value = value
    def type(self):    return ObjType.BOOLEAN
    def inspect(self): return "true" if self.value else "false"
    def __eq__(self, other):
        return isinstance(other, BooleanVal) and self.value == other.value

class Null(Obj):
    def type(self):    return ObjType.NULL
    def inspect(self): return "null"
    def __eq__(self, other):
        return isinstance(other, Null)

class ReturnValue(Obj):
    # Envuelve el valor de retorno para propagarlo a través de marcos de pila
    def __init__(self, value):
        self.value = value
    def type(self):    return ObjType.RETURN_VALUE
    def inspect(self): return self.value.inspect()

class BreakValue(Obj):
    # Señal interna para propagar break; nunca escapa al nivel del programa
    def type(self):    return ObjType.BREAK_VALUE
    def inspect(self): return "break"

class Error(Obj):
    # Error de runtime: se propaga hacia arriba sin abortar el proceso Python
    def __init__(self, message):
        self.message = message
    def type(self):    return ObjType.ERROR
    def inspect(self): return f"ERROR: {self.message}"

class FunctionObj(Obj):
    def __init__(self, parameters, body, env):
        self.parameters = parameters
        self.body       = body
        self.env        = env   # cierre léxico capturado en el momento de definición
    def type(self): return ObjType.FUNCTION
    def inspect(self):
        params = ", ".join([p.value for p in self.parameters])
        return f"fn({params}) {{ ... }}"

class ArrayObj(Obj):
    def __init__(self, elements):
        self.elements = elements
    def type(self): return ObjType.ARRAY
    def inspect(self):
        return "[" + ", ".join([e.inspect() for e in self.elements]) + "]"
    def __eq__(self, other):
        # Igualdad estructural: misma longitud y cada elemento igual por valor
        if not isinstance(other, ArrayObj) or len(self.elements) != len(other.elements):
            return False
        return all(a == b for a, b in zip(self.elements, other.elements))

class Builtin(Obj):
    # Envuelve funciones Python nativas para exponerlas como ciudadanos del lenguaje
    def __init__(self, fn):
        self.fn = fn
    def type(self):    return ObjType.BUILTIN
    def inspect(self): return "builtin function"
