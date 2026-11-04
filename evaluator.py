# EVALUADOR DEL AST (TREE-WALKER)

from ast_nodes import *
from objects import *
from environment import Environment

TRUE_OBJ = BooleanVal(True)
FALSE_OBJ = BooleanVal(False)
NULL_OBJ = Null()
BREAK_OBJ = BreakValue()

def is_error(obj):
    """Verifica si un objeto del runtime representa un error de evaluación."""
    return obj is not None and obj.type() == ObjType.ERROR

def native_bool_to_bool_object(input_val):
    """Mapea un valor booleano nativo de Python a los singletons del intérprete."""
    return TRUE_OBJ if input_val else FALSE_OBJ

def is_truthy(obj):
    """
    Determina si un objeto en tiempo de ejecución evalúa a verdadero (truthy)
    o falso (falsy) siguiendo la semántica canónica de evaluación:
    - Null y BooleanVal(False) evalúan a falso.
    - Integer(0) representa el cero numérico (falso).
    - StringObj("") representa la cadena vacía (falso).
    - ArrayObj([]) representa la lista vacía sin elementos (falso).
    - Cualquier otro objeto (enteros != 0, cadenas pobladas, listas con elementos, funciones) evalúa a verdadero.
    """
    if obj is None or obj == NULL_OBJ or obj == FALSE_OBJ:
        return False
    if obj.type() == ObjType.INTEGER and obj.value == 0:
        return False
    if obj.type() == ObjType.STRING and obj.value == "":
        return False
    if obj.type() == ObjType.ARRAY and len(obj.elements) == 0:
        return False
    return True

# =============================================================================
# FUNCIONES INTEGRADAS (BUILT-INS) DEL RUNTIME
# =============================================================================

def builtin_len(*args):
    """
    Propósito:
        Calcula la cardinalidad o longitud de estructuras de datos indexables (ArrayObj)
        y secuencias de caracteres (StringObj).

    Parámetros:
        *args: Argumentos posicionales recibidos desde la llamada en el código evaluado.
               Requiere aridad estricta de exactamente 1 argumento.

    Retorno:
        Integer: Instancia que encapsula la cantidad entera de elementos o caracteres.

    Manejo de errores:
        - Retorna un objeto Error si la aridad es distinta de 1 (aridad estricta).
        - Retorna un objeto Error si el argumento no es una lista ni una cadena de texto.
    """
    # 1. Validación de aridad estricta:
    # Verificamos que se suministre exactamente un operando conforme a la signatura requerida.
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para len: esperado 1, obtenido {len(args)}")

    arg = args[0]

    # 2. Despacho polimórfico según el tipo de objeto en tiempo de ejecución:
    # Para estructuras de datos (ArrayObj), medimos la longitud de su lista interna de elementos.
    if arg.type() == ObjType.ARRAY:
        return Integer(len(arg.elements))
    # Para cadenas de texto (StringObj), medimos la cantidad de caracteres de la cadena nativa.
    elif arg.type() == ObjType.STRING:
        return Integer(len(arg.value))

    # 3. Manejo de error de tipo controlado:
    # Retornamos un objeto Error del runtime en vez de lanzar excepciones de Python (evita crashes).
    return Error(f"argumento para 'len' no soportado: {arg.type()}")


def builtin_print(*args):
    """
    Propósito:
        Escribe en la salida estándar (consola) la representación textual legible
        de uno o más objetos del lenguaje, separados por espacio y finalizando con salto de línea.

    Parámetros:
        *args: Colección variable de argumentos a desplegar en consola (aridad flexible: >= 0).

    Retorno:
        Null: Retorna el singleton NULL_OBJ (equivalente a None en Python / ausencia de valor).

    Manejo de errores:
        No genera errores de aridad ya que admite cero o múltiples argumentos.
    """
    # 1. Inspección y formateo de argumentos:
    # Invocamos el método .inspect() de cada objeto para obtener su representación textual estándar.
    output_parts = [a.inspect() for a in args]

    # 2. Emisión a la salida estándar:
    # Desplegamos en pantalla utilizando la función nativa print del host.
    print(*output_parts)

    # 3. Retorno canónico:
    # En un lenguaje funcional/orientado a expresiones, toda llamada debe producir un valor.
    # Siguiendo la convención de Python (None), retornamos NULL_OBJ.
    return NULL_OBJ


def builtin_int(*args):
    """
    Propósito:
        Conversión explícita de un objeto a su representación numérica entera (Integer).

    Parámetros:
        *args: Argumentos posicionales recibidos desde la llamada en el código evaluado.
               Requiere aridad estricta de exactamente 1 argumento.

    Retorno:
        Integer: Objeto numérico entero resultante de la conversión.

    Manejo de errores:
        - Retorna un objeto Error si se reciben 0 o más de 1 argumentos (aridad inválida).
        - Retorna un objeto Error si una cadena no contiene una representación entera convertible.
        - Retorna un objeto Error si el tipo de origen no admite conversión a entero.
    """
    # 1. Validación de aridad estricta:
    # int() requiere exactamente un argumento para realizar el casteo.
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para int: esperado 1, obtenido {len(args)}")

    arg = args[0]

    # 2. Conversión por identidad:
    # Si el objeto ya es una instancia de Integer, se retorna directamente sin procesamiento adicional.
    if arg.type() == ObjType.INTEGER:
        return arg

    # 3. Conversión desde BooleanVal:
    # Aplica la regla estándar en compiladores donde true mapea a 1 y false mapea a 0.
    if arg.type() == ObjType.BOOLEAN:
        return Integer(1 if arg.value else 0)

    # 4. Conversión desde StringObj:
    # Se analiza el texto eliminando espacios en blanco circundantes.
    if arg.type() == ObjType.STRING:
        try:
            # Intentamos el parseo mediante el conversor nativo int() de Python.
            parsed_val = int(arg.value.strip())
            return Integer(parsed_val)
        except ValueError:
            # Interceptamos ValueError de Python para evitar el quiebre abrupto del proceso
            # y propagamos un objeto Error descriptivo propio del entorno de ejecución.
            return Error(f"no se pudo convertir la cadena '{arg.value}' a entero")

    # 5. Restricción para tipos no convertibles:
    # Tipos complejos (ArrayObj, FunctionObj, Null) no poseen conversión trivial a entero.
    return Error(f"argumento para 'int' no soportado: {arg.type()}")


def builtin_str(*args):
    """
    Propósito:
        Conversión explícita de cualquier objeto del lenguaje a su representación
        textual canónica (StringObj).

    Parámetros:
        *args: Argumentos posicionales recibidos desde la llamada en el código evaluado.
               Requiere aridad estricta de exactamente 1 argumento.

    Retorno:
        StringObj: Cadena de texto resultante con la inspección del objeto.

    Manejo de errores:
        - Retorna un objeto Error si la aridad es distinta de 1.
    """
    # 1. Validación de aridad estricta:
    # str() debe recibir exactamente un argumento a serializar.
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para str: esperado 1, obtenido {len(args)}")

    arg = args[0]

    # 2. Delegación al protocolo de inspección:
    # Toda clase que hereda de Obj implementa .inspect(), asegurando una conversión
    # polimórfica y robusta sin riesgo de excepción en tiempo de ejecución.
    return StringObj(arg.inspect())


def builtin_bool(*args):
    """
    Propósito:
        Conversión explícita de un objeto a su valor de verdad booleano (BooleanVal),
        aplicando la semántica canónica de verdad y falsedad (truthiness / falsiness).

    Parámetros:
        *args: Argumentos posicionales recibidos desde la llamada en el código evaluado.
               Requiere aridad estricta de exactamente 1 argumento.

    Retorno:
        BooleanVal: TRUE_OBJ si el objeto evalúa como verdadero; FALSE_OBJ si evalúa como falso.

    Manejo de errores:
        - Retorna un objeto Error si la aridad es distinta de 1.
    """
    # 1. Validación de aridad estricta:
    # bool() debe invocarse con exactamente un argumento.
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para bool: esperado 1, obtenido {len(args)}")

    arg = args[0]

    # 2. Evaluación de falsedad / verdad:
    # Delegamos a la función central is_truthy() para mantener coherencia semántica unificada
    # en todo el compilador (utilizada igualmente por condicionales if y ciclos while/for).
    return native_bool_to_bool_object(is_truthy(arg))


def builtin_type(*args):
    """
    Propósito:
        Inspección dinámica de metadatos de tipos en tiempo de ejecución,
        permitiendo introspection y verificación de tipos en el lenguaje evaluado.

    Parámetros:
        *args: Argumentos posicionales recibidos desde la llamada en el código evaluado.
               Requiere aridad estricta de exactamente 1 argumento.

    Retorno:
        StringObj: Cadena que contiene el identificador literal del tipo interno
                   ("INTEGER", "STRING", "BOOLEAN", "ARRAY", "FUNCTION", "NULL", etc.).

    Manejo de errores:
        - Retorna un objeto Error si la aridad es distinta de 1.
    """
    # 1. Validación de aridad estricta:
    # type() requiere exactamente un elemento para inspeccionar sus metadatos.
    if len(args) != 1:
        return Error(f"número incorrecto de argumentos para type: esperado 1, obtenido {len(args)}")

    arg = args[0]

    # 2. Consulta de metadatos del objeto:
    # Invocamos el método .type() que expone cada subclase de Obj conforme a ObjType
    # y devolvemos el resultado empaquetado como un StringObj accesible para el programa.
    return StringObj(arg.type())


BUILTINS = {
    "len": Builtin(builtin_len),
    "print": Builtin(builtin_print),
    "int": Builtin(builtin_int),
    "str": Builtin(builtin_str),
    "bool": Builtin(builtin_bool),
    "type": Builtin(builtin_type)
}

# =============================================================================
# MOTOR DE EVALUACIÓN (TREE-WALKING EVALUATOR)
# =============================================================================

def evaluate(node, env):
    if node is None:
        return NULL_OBJ
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
    elif isinstance(node, AssignExpression):
        val = evaluate(node.value, env)
        if is_error(val): return val
        if isinstance(node.name, Identifier):
            env.assign(node.name.value, val)
            return val
        elif isinstance(node.name, IndexExpression):
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
    elif isinstance(node, IntegerLiteral):
        return Integer(node.value)
    elif isinstance(node, StringLiteral):
        return StringObj(node.value)
    elif isinstance(node, Boolean):
        return native_bool_to_bool_object(node.value)
    elif isinstance(node, PrefixExpression):
        right = evaluate(node.right, env)
        if is_error(right): return right
        return eval_prefix_expression(node.operator, right)
    elif isinstance(node, InfixExpression):
        # Intercepción de operadores lógicos booleanos para evaluación en cortocircuito (Short-circuit evaluation)
        # Se interceptan antes de evaluar node.right para evitar cómputo innecesario o errores.
        if node.operator in ("and", "&&"):
            return eval_logical_and_expression(node, env)
        elif node.operator in ("or", "||"):
            return eval_logical_or_expression(node, env)

        left = evaluate(node.left, env)
        if is_error(left): return left
        right = evaluate(node.right, env)
        if is_error(right): return right
        return eval_infix_expression(node.operator, left, right)
    elif isinstance(node, IfExpression):
        return eval_if_expression(node, env)
    elif isinstance(node, WhileExpression):
        return eval_while_expression(node, env)
    elif isinstance(node, ForExpression):
        return eval_for_expression(node, env)
    elif isinstance(node, Identifier):
        return eval_identifier(node, env)
    elif isinstance(node, FunctionLiteral):
        params = node.parameters
        body = node.body
        return FunctionObj(params, body, env)
    elif isinstance(node, CallExpression):
        function = evaluate(node.function, env)
        if is_error(function): return function
        args = eval_expressions(node.arguments, env)
        if len(args) == 1 and is_error(args[0]): return args[0]
        return apply_function(function, args)
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
    return Error(f"nodo de AST no soportado o desconocido: {type(node).__name__}")

def eval_program(stmts, env):
    result = None
    for stmt in stmts:
        result = evaluate(stmt, env)
        if isinstance(result, ReturnValue):
            return result.value
        elif isinstance(result, Error):
            return result
    return result

def eval_block_statement(block, env):
    block_env = Environment(outer=env)
    result = None
    for stmt in block.statements:
        result = evaluate(stmt, block_env)
        if result is not None and (result.type() == ObjType.RETURN_VALUE or result.type() == ObjType.ERROR or result.type() == ObjType.BREAK_VALUE):
            return result
    return result

def eval_prefix_expression(operator, right):
    if operator == "!": return eval_bang_operator_expression(right)
    elif operator == "-": return eval_minus_prefix_operator_expression(right)
    return Error(f"operador desconocido: {operator}{right.type()}")

def eval_bang_operator_expression(right):
    if is_truthy(right):
        return FALSE_OBJ
    return TRUE_OBJ

def eval_minus_prefix_operator_expression(right):
    if right.type() != ObjType.INTEGER:
        return Error(f"operador desconocido: -{right.type()}")
    return Integer(-right.value)

def eval_logical_and_expression(node, env):
    """
    Propósito:
        Evalúa una expresión lógica de conjunción ('and' o '&&') implementando
        semántica de evaluación en cortocircuito (short-circuit / evaluación perezosa).

    Precedencia y asociatividad:
        - Precedencia: Mayor que 'or'/'||', menor que comparaciones relacionales ('==', '<', etc.).
        - Asociatividad: Por la izquierda (left-associative).

    Semántica de evaluación:
        1. Evalúa estrictamente el operando izquierdo (node.left). Si produce un Error, se retorna inmediatamente.
        2. Aplica is_truthy(left):
           - Si 'left' es FALSO, se produce el cortocircuito: se omite por completo la
             evaluación del operando derecho (node.right), protegiendo contra efectos
             secundarios indeseados o errores de ejecución (ej. división por cero),
             y se retorna inmediatamente 'left' (o FALSE_OBJ si se normaliza a booleano).
           - Si 'left' es VERDADERO, el resultado final depende enteramente del operando
             derecho, por lo que se procede a evaluar y retornar evaluate(node.right, env).
    """
    # 1. Evaluación del operando izquierdo:
    left = evaluate(node.left, env)
    if is_error(left):
        return left

    # 2. Comprobación de cortocircuito (Short-circuit):
    # Si el operando izquierdo es falso, la conjunción (A and B) es falsa sin importar B.
    # Por definición de evaluación perezosa, node.right NO debe evaluarse.
    if not is_truthy(left):
        return left if left.type() == ObjType.BOOLEAN else FALSE_OBJ

    # 3. Evaluación perezosa del operando derecho:
    # Solo se evalúa si el operando izquierdo resultó verdadero.
    right = evaluate(node.right, env)
    if is_error(right):
        return right
    return right if right.type() == ObjType.BOOLEAN else native_bool_to_bool_object(is_truthy(right))


def eval_logical_or_expression(node, env):
    """
    Propósito:
        Evalúa una expresión lógica de disyunción ('or' o '||') implementando
        semántica de evaluación en cortocircuito (short-circuit / evaluación perezosa).

    Precedencia y asociatividad:
        - Precedencia: Menor que 'and'/'&&', asociatividad por la izquierda.
        - Asociatividad: Por la izquierda (left-associative).

    Semántica de evaluación:
        1. Evalúa estrictamente el operando izquierdo (node.left). Si produce un Error, se retorna inmediatamente.
        2. Aplica is_truthy(left):
           - Si 'left' es VERDADERO, se produce el cortocircuito: la disyunción completa
             (A or B) ya es verdadera independientemente de B. Se retorna inmediatamente
             'left' (o TRUE_OBJ) SIN evaluar node.right.
           - Si 'left' es FALSO, se evalúa y retorna el resultado de evaluate(node.right, env).
    """
    # 1. Evaluación del operando izquierdo:
    left = evaluate(node.left, env)
    if is_error(left):
        return left

    # 2. Comprobación de cortocircuito (Short-circuit):
    # Si el operando izquierdo es verdadero, la disyunción (A or B) es verdadera sin importar B.
    # Por definición de evaluación perezosa, node.right NO debe evaluarse.
    if is_truthy(left):
        return left if left.type() == ObjType.BOOLEAN else TRUE_OBJ

    # 3. Evaluación perezosa del operando derecho:
    # Solo se evalúa si el operando izquierdo resultó falso.
    right = evaluate(node.right, env)
    if is_error(right):
        return right
    return right if right.type() == ObjType.BOOLEAN else native_bool_to_bool_object(is_truthy(right))


def eval_infix_expression(operator, left, right):
    if left.type() == ObjType.INTEGER and right.type() == ObjType.INTEGER:
        return eval_integer_infix_expression(operator, left, right)
    elif left.type() == ObjType.STRING and right.type() == ObjType.STRING:
        return eval_string_infix_expression(operator, left, right)
    elif operator in ("and", "&&"):
        return native_bool_to_bool_object(is_truthy(left) and is_truthy(right))
    elif operator in ("or", "||"):
        return native_bool_to_bool_object(is_truthy(left) or is_truthy(right))
    elif operator == "==": return native_bool_to_bool_object(left == right)
    elif operator == "!=": return native_bool_to_bool_object(left != right)
    elif left.type() != right.type():
        return Error(f"discrepancia de tipos: {left.type()} {operator} {right.type()}")
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")

def eval_string_infix_expression(operator, left, right):
    if operator == "+":
        return StringObj(left.value + right.value)
    elif operator == "==":
        return native_bool_to_bool_object(left.value == right.value)
    elif operator == "!=":
        return native_bool_to_bool_object(left.value != right.value)
    return Error(f"operador desconocido: {left.type()} {operator} {right.type()}")

def eval_integer_infix_expression(operator, left, right):
    l_val = left.value
    r_val = right.value
    if operator == "+": return Integer(l_val + r_val)
    elif operator == "-": return Integer(l_val - r_val)
    elif operator == "*": return Integer(l_val * r_val)
    elif operator == "/":
        if r_val == 0:
            return Error("división por cero")
        return Integer(l_val // r_val)
    elif operator == "**":
        if l_val == 0 and r_val < 0:
            return Error("cálculo de potencia inválido: cero elevado a potencia negativa")
        return Integer(l_val ** r_val)
    elif operator == "<": return native_bool_to_bool_object(l_val < r_val)
    elif operator == ">": return native_bool_to_bool_object(l_val > r_val)
    elif operator == "<=": return native_bool_to_bool_object(l_val <= r_val)
    elif operator == ">=": return native_bool_to_bool_object(l_val >= r_val)
    elif operator == "==": return native_bool_to_bool_object(l_val == r_val)
    elif operator == "!=": return native_bool_to_bool_object(l_val != r_val)
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
    result = NULL_OBJ
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
    new_env = Environment(env)
    if fe.init is not None:
        init_res = evaluate(fe.init, new_env)
        if is_error(init_res): return init_res
    result = NULL_OBJ
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
    val = env.get(node.value)
    if val is not None: return val
    builtin = BUILTINS.get(node.value)
    if builtin is not None: return builtin
    return Error(f"identificador no encontrado: {node.value}")

def eval_expressions(exps, env):
    result = []
    for e in exps:
        evaluated = evaluate(e, env)
        if is_error(evaluated): return [evaluated]
        result.append(evaluated)
    return result

def apply_function(fn, args):
    if isinstance(fn, FunctionObj):
        extended_env = extend_function_env(fn, args)
        evaluated = evaluate(fn.body, extended_env)
        return unwrap_return_value(evaluated)
    elif isinstance(fn, Builtin):
        return fn.fn(*args)
    return Error(f"no es una función: {fn.type()}")

def extend_function_env(fn, args):
    env = Environment(fn.env)
    for i, param in enumerate(fn.parameters):
        if i < len(args):
            env.set(param.value, args[i])
    return env

def unwrap_return_value(obj):
    if isinstance(obj, ReturnValue): return obj.value
    return obj

def eval_index_expression(left, index):
    if left.type() == ObjType.ARRAY and index.type() == ObjType.INTEGER:
        idx = index.value
        max_idx = len(left.elements) - 1
        if idx < 0 or idx > max_idx: return NULL_OBJ
        return left.elements[idx]
    return Error(f"operador de índice no soportado para: {left.type()}")
