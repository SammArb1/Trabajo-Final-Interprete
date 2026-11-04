# EVALUADOR DEL AST (TREE-WALKER)
# Recorre el árbol de sintaxis abstracta y produce objetos del runtime.

from ast_nodes import *
from objects import *
from environment import Environment

# Singletons globales: evitan alocar nuevos objetos para valores frecuentes
TRUE_OBJ  = BooleanVal(True)
FALSE_OBJ = BooleanVal(False)
NULL_OBJ  = Null()
BREAK_OBJ = BreakValue()

# ---------------------------------------------------------------------------
# UTILIDADES DE RUNTIME
# ---------------------------------------------------------------------------

def is_error(obj):
    # Detecta errores del runtime para propagarlos inmediatamente (fail-fast)
    return obj is not None and obj.type() == ObjType.ERROR

def native_bool_to_bool_object(input_val):
    # Convierte bool nativo de Python al singleton BooleanVal del intérprete
    return TRUE_OBJ if input_val else FALSE_OBJ

def is_truthy(obj):
    # Semántica canónica: Null, False, 0, 0.0, "" y [] son falsy; todo lo demás es truthy
    if obj is None or obj == NULL_OBJ or obj == FALSE_OBJ:
        return False
    if obj.type() == ObjType.INTEGER and obj.value == 0:
        return False
    if obj.type() == ObjType.FLOAT and obj.value == 0.0:
        return False
    if obj.type() == ObjType.STRING and obj.value == "":
        return False
    if obj.type() == ObjType.ARRAY and len(obj.elements) == 0:
        return False
    return True

# ---------------------------------------------------------------------------
# FUNCIONES INTEGRADAS (BUILT-INS)
# Aridad estricta: retornan Error si se recibe el número incorrecto de args.
# Nunca lanzan excepciones Python — siempre retornan un objeto Error del runtime.
# ---------------------------------------------------------------------------

def builtin_len(*args):
    # len(x) — longitud de arrays y strings; aridad exactamente 1
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para len: esperado 1, obtenido {len(args)}")
    arg = args[0]
    if arg.type() == ObjType.ARRAY:
        return Integer(len(arg.elements))
    if arg.type() == ObjType.STRING:
        return Integer(len(arg.value))
    return Error(f"argumento para 'len' no soportado: {arg.type()}")

def builtin_print(*args):
    # print(...) — imprime en stdout con .inspect(); acepta 0 o más argumentos; retorna Null
    print(*[a.inspect() for a in args])
    return NULL_OBJ

def builtin_int(*args):
    # int(x) — casteo a Integer; aridad 1; soporta INTEGER, FLOAT (trunca), BOOLEAN, STRING
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para int: esperado 1, obtenido {len(args)}")
    arg = args[0]
    if arg.type() == ObjType.INTEGER:
        return arg                              # identidad: ya es entero
    if arg.type() == ObjType.FLOAT:
        return Integer(int(arg.value))          # truncamiento hacia cero
    if arg.type() == ObjType.BOOLEAN:
        return Integer(1 if arg.value else 0)  # true→1, false→0
    if arg.type() == ObjType.STRING:
        try:
            return Integer(int(arg.value.strip()))
        except ValueError:
            # Cadena no entera: propagamos Error en vez de propagar la excepción Python
            return Error(f"no se pudo convertir la cadena '{arg.value}' a entero")
    return Error(f"argumento para 'int' no soportado: {arg.type()}")

def builtin_str(*args):
    # str(x) — serialización textual vía .inspect(); aridad 1; cualquier tipo es válido
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para str: esperado 1, obtenido {len(args)}")
    return StringObj(args[0].inspect())

def builtin_bool(*args):
    # bool(x) — valor de verdad vía is_truthy(); aridad 1; unifica semántica con if/while
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para bool: esperado 1, obtenido {len(args)}")
    return native_bool_to_bool_object(is_truthy(args[0]))

def builtin_type(*args):
    # type(x) — retorna StringObj con el nombre del tipo interno (ej. "INTEGER", "FLOAT")
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para type: esperado 1, obtenido {len(args)}")
    return StringObj(args[0].type())

def builtin_float(*args):
    # float(x) — casteo a Float; aridad 1; soporta FLOAT (identidad), INTEGER, BOOLEAN, STRING
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para float: esperado 1, obtenido {len(args)}")
    arg = args[0]
    if arg.type() == ObjType.FLOAT:
        return arg                                      # identidad: ya es flotante
    if arg.type() == ObjType.INTEGER:
        return Float(float(arg.value))                  # widening: int → float
    if arg.type() == ObjType.BOOLEAN:
        return Float(1.0 if arg.value else 0.0)        # true→1.0, false→0.0
    if arg.type() == ObjType.STRING:
        try:
            return Float(float(arg.value.strip()))
        except ValueError:
            # Cadena no numérica: propagamos Error en vez de propagar la excepción Python
            return Error(f"no se pudo convertir la cadena '{arg.value}' a float")
    return Error(f"argumento para 'float' no soportado: {arg.type()}")

# Registro central de funciones integradas disponibles en el ámbito global
BUILTINS = {
    "len":   Builtin(builtin_len),
    "print": Builtin(builtin_print),
    "int":   Builtin(builtin_int),
    "str":   Builtin(builtin_str),
    "bool":  Builtin(builtin_bool),
    "type":  Builtin(builtin_type),
    "float": Builtin(builtin_float),
}

# ---------------------------------------------------------------------------
# MOTOR DE EVALUACIÓN (TREE-WALKING EVALUATOR)
# ---------------------------------------------------------------------------

def evaluate(node, env):
    # Dispatch central: cada tipo de nodo del AST tiene su rama de evaluación
    if node is None:
        return NULL_OBJ

    # --- Sentencias ---
    elif isinstance(node, Program):
        return eval_program(node.statements, env)
    elif isinstance(node, BlockStatement):
        return eval_block_statement(node, env)
    elif isinstance(node, ExpressionStatement):
        return evaluate(node.expression, env)
    elif isinstance(node, ReturnStatement):
        val = evaluate(node.return_value, env)
        if is_error(val): return val
        return ReturnValue(val)
    elif isinstance(node, BreakStatement):
        return BREAK_OBJ
    elif isinstance(node, LetStatement):
        val = evaluate(node.value, env)
        if is_error(val): return val
        env.set(node.name.value, val)
        return val

    # --- Asignación mutable (identificador o índice de array) ---
    elif isinstance(node, AssignExpression):
        val = evaluate(node.value, env)
        if is_error(val): return val
        if isinstance(node.name, Identifier):
            env.assign(node.name.value, val)
            return val
        elif isinstance(node.name, IndexExpression):
            # Mutación por índice: arr[i] = valor
            left_obj = evaluate(node.name.left, env)
            if is_error(left_obj): return left_obj
            idx_obj = evaluate(node.name.index, env)
            if is_error(idx_obj): return idx_obj
            if left_obj.type() != ObjType.ARRAY:
                return Error(f"asignación por índice no soportada para: {left_obj.type()}")
            if idx_obj.type() != ObjType.INTEGER:
                return Error(f"el índice debe ser un entero, no {idx_obj.type()}")
            idx = idx_obj.value
            if idx < 0 or idx >= len(left_obj.elements):
                return Error(f"índice fuera de rango: {idx}")
            left_obj.elements[idx] = val
            return val
        return Error(f"destino de asignación inválido: {type(node.name).__name__}")

    # --- Literales ---
    elif isinstance(node, IntegerLiteral):
        return Integer(node.value)
    elif isinstance(node, FloatLiteral):
        return Float(node.value)
    elif isinstance(node, StringLiteral):
        return StringObj(node.value)
    elif isinstance(node, Boolean):
        return native_bool_to_bool_object(node.value)

    # --- Expresiones de operador ---
    elif isinstance(node, PrefixExpression):
        right = evaluate(node.right, env)
        if is_error(right): return right
        return eval_prefix_expression(node.operator, right)
    elif isinstance(node, InfixExpression):
        # and/or se interceptan antes de evaluar node.right (cortocircuito estricto)
        if node.operator in ("and", "&&"):
            return eval_logical_and_expression(node, env)
        elif node.operator in ("or", "||"):
            return eval_logical_or_expression(node, env)
        left = evaluate(node.left, env)
        if is_error(left): return left
        right = evaluate(node.right, env)
        if is_error(right): return right
        return eval_infix_expression(node.operator, left, right)

    # --- Estructuras de control ---
    elif isinstance(node, IfExpression):
        return eval_if_expression(node, env)
    elif isinstance(node, WhileExpression):
        return eval_while_expression(node, env)
    elif isinstance(node, ForExpression):
        return eval_for_expression(node, env)

    # --- Identificadores y funciones ---
    elif isinstance(node, Identifier):
        return eval_identifier(node, env)
    elif isinstance(node, FunctionLiteral):
        return FunctionObj(node.parameters, node.body, env)
    elif isinstance(node, CallExpression):
        function = evaluate(node.function, env)
        if is_error(function): return function
        args = eval_expressions(node.arguments, env)
        if len(args) == 1 and is_error(args[0]): return args[0]
        return apply_function(function, args)

    # --- Arrays e índices ---
    elif isinstance(node, ArrayLiteral):
        elements = eval_expressions(node.elements, env)
        if len(elements) == 1 and is_error(elements[0]): return elements[0]
        return ArrayObj(elements)
    elif isinstance(node, IndexExpression):
        left = evaluate(node.left, env)
        if is_error(left): return left
        index = evaluate(node.index, env)
        if is_error(index): return index
        return eval_index_expression(left, index)

    return Error(f"nodo de AST no soportado: {type(node).__name__}")


def eval_program(stmts, env):
    # Ejecuta sentencias en orden; propaga return y errors, descarta otros resultados intermedios
    result = None
    for stmt in stmts:
        result = evaluate(stmt, env)
        if isinstance(result, ReturnValue):
            return result.value     # desenvuelve el valor para el nivel top-level
        elif isinstance(result, Error):
            return result
    return result


def eval_block_statement(block, env):
    # Aislamiento de ámbito: cada bloque { } obtiene un entorno hijo para evitar contaminación
    block_env = Environment(outer=env)
    result    = None
    for stmt in block.statements:
        result = evaluate(stmt, block_env)
        # Propagamos return, error y break sin desempaquetar (el llamador los maneja)
        if result is not None and result.type() in (
            ObjType.RETURN_VALUE, ObjType.ERROR, ObjType.BREAK_VALUE
        ):
            return result
    return result


def eval_prefix_expression(operator, right):
    if operator == "!":  return eval_bang_operator_expression(right)
    elif operator == "-": return eval_minus_prefix_operator_expression(right)
    return Error(f"operador desconocido: {operator}{right.type()}")


def eval_bang_operator_expression(right):
    # Negación lógica: invierte el valor de verdad usando is_truthy unificado
    return FALSE_OBJ if is_truthy(right) else TRUE_OBJ


def eval_minus_prefix_operator_expression(right):
    if right.type() == ObjType.INTEGER:
        return Integer(-right.value)
    if right.type() == ObjType.FLOAT:
        return Float(-right.value)
    return Error(f"operador desconocido: -{right.type()}")


def eval_logical_and_expression(node, env):
    # Cortocircuito AND: si left es falsy, retorna inmediatamente sin evaluar right
    left = evaluate(node.left, env)
    if is_error(left): return left
    if not is_truthy(left):
        return left if left.type() == ObjType.BOOLEAN else FALSE_OBJ
    # left es truthy → el resultado depende de right
    right = evaluate(node.right, env)
    if is_error(right): return right
    return right if right.type() == ObjType.BOOLEAN else native_bool_to_bool_object(is_truthy(right))


def eval_logical_or_expression(node, env):
    # Cortocircuito OR: si left es truthy, retorna inmediatamente sin evaluar right
    left = evaluate(node.left, env)
    if is_error(left): return left
    if is_truthy(left):
        return left if left.type() == ObjType.BOOLEAN else TRUE_OBJ
    # left es falsy → el resultado depende de right
    right = evaluate(node.right, env)
    if is_error(right): return right
    return right if right.type() == ObjType.BOOLEAN else native_bool_to_bool_object(is_truthy(right))


def eval_infix_expression(operator, left, right):
    # Despacho por tipos: INTEGER+INTEGER primero para preservar semántica entera
    if left.type() == ObjType.INTEGER and right.type() == ObjType.INTEGER:
        return eval_integer_infix_expression(operator, left, right)
    # Coerción implícita a float cuando al menos un operando es FLOAT
    if left.type() in (ObjType.FLOAT, ObjType.INTEGER) and right.type() in (ObjType.FLOAT, ObjType.INTEGER):
        return eval_numeric_infix_expression(operator, left, right)
    if left.type() == ObjType.STRING and right.type() == ObjType.STRING:
        return eval_string_infix_expression(operator, left, right)
    # Comparaciones de igualdad polimórficas (usan __eq__ de cada clase Obj)
    if operator == "==": return native_bool_to_bool_object(left == right)
    if operator == "!=": return native_bool_to_bool_object(left != right)
    if left.type() != right.type():
        return Error(f"discrepancia de tipos: {left.type()} {operator} {right.type()}")
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")


def eval_string_infix_expression(operator, left, right):
    if operator == "+":  return StringObj(left.value + right.value)
    if operator == "==": return native_bool_to_bool_object(left.value == right.value)
    if operator == "!=": return native_bool_to_bool_object(left.value != right.value)
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")


def eval_numeric_infix_expression(operator, left, right):
    # Coerción: si alguno es FLOAT los valores se tratan como float; resultado preserva el tipo dominante
    l_val    = float(left.value)
    r_val    = float(right.value)
    is_float = left.type() == ObjType.FLOAT or right.type() == ObjType.FLOAT
    make     = Float if is_float else Integer

    if operator == "+":   return make(l_val + r_val)
    if operator == "-":   return make(l_val - r_val)
    if operator == "*":   return make(l_val * r_val)
    if operator == "/":
        if r_val == 0.0:
            return Error("división por cero")
        return Float(l_val / r_val)   # la división siempre produce float
    if operator == "**":
        if l_val == 0 and r_val < 0:
            return Error("cálculo de potencia inválido: cero elevado a potencia negativa")
        result = l_val ** r_val
        return Float(result) if is_float else Integer(int(result))
    if operator == "<":  return native_bool_to_bool_object(l_val < r_val)
    if operator == ">":  return native_bool_to_bool_object(l_val > r_val)
    if operator == "<=": return native_bool_to_bool_object(l_val <= r_val)
    if operator == ">=": return native_bool_to_bool_object(l_val >= r_val)
    if operator == "==": return native_bool_to_bool_object(l_val == r_val)
    if operator == "!=": return native_bool_to_bool_object(l_val != r_val)
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")


def eval_integer_infix_expression(operator, left, right):
    # Operaciones puras entero+entero; / produce float (semántica Python 3)
    l_val = left.value
    r_val = right.value
    if operator == "+": return Integer(l_val + r_val)
    if operator == "-": return Integer(l_val - r_val)
    if operator == "*": return Integer(l_val * r_val)
    if operator == "/":
        if r_val == 0:
            return Error("división por cero")
        return Float(l_val / r_val)   # / siempre produce float
    if operator == "**":
        if l_val == 0 and r_val < 0:
            return Error("cálculo de potencia inválido: cero elevado a potencia negativa")
        return Integer(l_val ** r_val)
    if operator == "<":  return native_bool_to_bool_object(l_val < r_val)
    if operator == ">":  return native_bool_to_bool_object(l_val > r_val)
    if operator == "<=": return native_bool_to_bool_object(l_val <= r_val)
    if operator == ">=": return native_bool_to_bool_object(l_val >= r_val)
    if operator == "==": return native_bool_to_bool_object(l_val == r_val)
    if operator == "!=": return native_bool_to_bool_object(l_val != r_val)
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")


def eval_if_expression(ie, env):
    condition = evaluate(ie.condition, env)
    if is_error(condition): return condition
    if is_truthy(condition):
        return evaluate(ie.consequence, env)
    for elif_cond_node, elif_cons_node in ie.elifs:
        elif_cond = evaluate(elif_cond_node, env)
        if is_error(elif_cond): return elif_cond
        if is_truthy(elif_cond):
            return evaluate(elif_cons_node, env)
    if ie.alternative is not None:
        return evaluate(ie.alternative, env)
    return NULL_OBJ


def eval_while_expression(we, env):
    while True:
        condition = evaluate(we.condition, env)
        if is_error(condition): return condition
        if not is_truthy(condition):
            break
        result = evaluate(we.body, env)
        if is_error(result): return result
        if result is not None and result.type() == ObjType.RETURN_VALUE:
            return result
        if result is not None and result.type() == ObjType.BREAK_VALUE:
            break
    return NULL_OBJ


def eval_for_expression(fe, env):
    # Ámbito propio del for: init puede declarar variables que no escapan al bloque externo
    new_env = Environment(fe.init and env or env)   # nuevo hijo siempre
    new_env = Environment(env)
    if fe.init is not None:
        init_res = evaluate(fe.init, new_env)
        if is_error(init_res): return init_res
    while True:
        if fe.condition is not None:
            condition = evaluate(fe.condition, new_env)
            if is_error(condition): return condition
            if not is_truthy(condition):
                break
        result = evaluate(fe.body, new_env)
        if is_error(result): return result
        if result is not None and result.type() == ObjType.RETURN_VALUE:
            return result
        if result is not None and result.type() == ObjType.BREAK_VALUE:
            break
        if fe.update is not None:
            update_res = evaluate(fe.update, new_env)
            if is_error(update_res): return update_res
    return NULL_OBJ


def eval_identifier(node, env):
    # Búsqueda: primero en el entorno léxico, luego en BUILTINS globales
    val = env.get(node.value)
    if val is not None: return val
    builtin = BUILTINS.get(node.value)
    if builtin is not None: return builtin
    return Error(f"identificador no encontrado: {node.value}")


def eval_expressions(exps, env):
    # Evalúa lista de expresiones; aborta y retorna el primer error encontrado
    result = []
    for e in exps:
        evaluated = evaluate(e, env)
        if is_error(evaluated): return [evaluated]
        result.append(evaluated)
    return result


def apply_function(fn, args):
    if isinstance(fn, FunctionObj):
        extended_env = extend_function_env(fn, args)
        evaluated    = evaluate(fn.body, extended_env)
        return unwrap_return_value(evaluated)
    elif isinstance(fn, Builtin):
        return fn.fn(*args)
    return Error(f"no es una función: {fn.type()}")


def extend_function_env(fn, args):
    # Crea un entorno hijo del cierre de la función y vincula parámetros a argumentos
    env = Environment(fn.env)
    for i, param in enumerate(fn.parameters):
        if i < len(args):
            env.set(param.value, args[i])
    return env


def unwrap_return_value(obj):
    # Desempaqueta ReturnValue para que el return no escape más allá del cuerpo de la función
    return obj.value if isinstance(obj, ReturnValue) else obj


def eval_index_expression(left, index):
    if left.type() == ObjType.ARRAY and index.type() == ObjType.INTEGER:
        idx = index.value
        if idx < 0 or idx > len(left.elements) - 1:
            return NULL_OBJ   # índice fuera de rango retorna null, no error (convención pythónica)
        return left.elements[idx]
    return Error(f"operador de índice no soportado para: {left.type()}")
