# NODOS DEL ÁRBOL DE SINTAXIS ABSTRACTA (AST)
# Cada clase representa un constructo gramatical del lenguaje interpretado.

# --- Clases base ---

class Node:
    pass

class Statement(Node):
    pass

class Expression(Node):
    pass

# --- Programa raíz ---

class Program(Node):
    def __init__(self):
        self.statements = []

# --- Sentencias ---

class LetStatement(Statement):
    # let <name> = <value>;
    def __init__(self, token, name, value):
        self.token = token
        self.name  = name
        self.value = value

class ReturnStatement(Statement):
    # return <return_value>;
    def __init__(self, token, return_value):
        self.token        = token
        self.return_value = return_value

class BreakStatement(Statement):
    # break;  — sale del bucle más cercano
    def __init__(self, token):
        self.token = token

class ExpressionStatement(Statement):
    # Envuelve una expresión evaluada como sentencia (ej. llamada a función)
    def __init__(self, token, expression):
        self.token      = token
        self.expression = expression

class BlockStatement(Statement):
    # Secuencia de sentencias entre llaves { ... }
    def __init__(self, token, statements):
        self.token      = token
        self.statements = statements

# --- Expresiones literales y de referencia ---

class Identifier(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value   # nombre del símbolo como string

class IntegerLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value   # int nativo de Python

class FloatLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value   # float nativo de Python

class StringLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value   # str nativo de Python (ya desescapado)

class Boolean(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value   # bool nativo (True / False)

# --- Expresiones compuestas ---

class PrefixExpression(Expression):
    # <operator><right>  (ej. !x, -n)
    def __init__(self, token, operator, right):
        self.token    = token
        self.operator = operator
        self.right    = right

class InfixExpression(Expression):
    # <left> <operator> <right>  (aritmética, relacional, lógica)
    def __init__(self, token, left, operator, right):
        self.token    = token
        self.left     = left
        self.operator = operator
        self.right    = right

class AssignExpression(Expression):
    # <name> = <value>  — asignación mutable; name puede ser Identifier o IndexExpression
    def __init__(self, token, name, value):
        self.token = token
        self.name  = name
        self.value = value

class IfExpression(Expression):
    # if (<condition>) { ... } [elif (...) { ... }]* [else { ... }]
    def __init__(self, token, condition, consequence, alternative=None, elifs=None):
        self.token       = token
        self.condition   = condition
        self.consequence = consequence
        self.alternative = alternative
        self.elifs       = elifs or []   # lista de pares (cond_node, block_node)

class FunctionLiteral(Expression):
    # function(<parameters>) { <body> }
    def __init__(self, token, parameters, body):
        self.token      = token
        self.parameters = parameters
        self.body       = body

class CallExpression(Expression):
    # <function>(<arguments>)
    def __init__(self, token, function, arguments):
        self.token     = token
        self.function  = function
        self.arguments = arguments

class ArrayLiteral(Expression):
    # [<element>, ...]
    def __init__(self, token, elements):
        self.token    = token
        self.elements = elements

class IndexExpression(Expression):
    # <left>[<index>]
    def __init__(self, token, left, index):
        self.token = token
        self.left  = left
        self.index = index

class WhileExpression(Expression):
    # while (<condition>) { <body> }
    def __init__(self, token, condition, body):
        self.token     = token
        self.condition = condition
        self.body      = body

class ForExpression(Expression):
    # for (<init>; <condition>; <update>) { <body> }
    def __init__(self, token, init, condition, update, body):
        self.token     = token
        self.init      = init
        self.condition = condition
        self.update    = update
        self.body      = body
