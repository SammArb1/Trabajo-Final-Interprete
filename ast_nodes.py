# NODOS DEL ARBOL DE SINTAXIS ABSTRACTA (AST)

class Node:
    pass

class Statement(Node):
    pass

class Expression(Node):
    pass

class Program(Node):
    def __init__(self):
        self.statements = []

class LetStatement(Statement):
    def __init__(self, token, name, value):
        self.token = token
        self.name = name
        self.value = value

class ReturnStatement(Statement):
    def __init__(self, token, return_value):
        self.token = token
        self.return_value = return_value

class BreakStatement(Statement):
    def __init__(self, token):
        self.token = token

class ExpressionStatement(Statement):
    def __init__(self, token, expression):
        self.token = token
        self.expression = expression

class BlockStatement(Statement):
    def __init__(self, token, statements):
        self.token = token
        self.statements = statements

class Identifier(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value

class IntegerLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value

class FloatLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value

class StringLiteral(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value

class Boolean(Expression):
    def __init__(self, token, value):
        self.token = token
        self.value = value

class PrefixExpression(Expression):
    def __init__(self, token, operator, right):
        self.token = token
        self.operator = operator
        self.right = right

class InfixExpression(Expression):
    def __init__(self, token, left, operator, right):
        self.token = token
        self.left = left
        self.operator = operator
        self.right = right

class AssignExpression(Expression):
    def __init__(self, token, name, value):
        self.token = token
        self.name = name
        self.value = value

class IfExpression(Expression):
    def __init__(self, token, condition, consequence, alternative=None, elifs=None):
        self.token = token
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative
        self.elifs = elifs or []

class FunctionLiteral(Expression):
    def __init__(self, token, parameters, body):
        self.token = token
        self.parameters = parameters
        self.body = body

class CallExpression(Expression):
    def __init__(self, token, function, arguments):
        self.token = token
        self.function = function
        self.arguments = arguments

class ArrayLiteral(Expression):
    def __init__(self, token, elements):
        self.token = token
        self.elements = elements

class IndexExpression(Expression):
    def __init__(self, token, left, index):
        self.token = token
        self.left = left
        self.index = index

class WhileExpression(Expression):
    def __init__(self, token, condition, body):
        self.token = token
        self.condition = condition
        self.body = body

class ForExpression(Expression):
    def __init__(self, token, init, condition, update, body):
        self.token = token
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
