# ANALIZADOR SINTÁCTICO (PARSER PRATT) — construye el AST a partir de tokens con precedencias

from tokens import *
from ast_nodes import *

# Niveles de precedencia para parsing de expresiones (Pratt Parser)
LOWEST      = 1   # Nivel base (por defecto)
ASSIGN_PREC = 2   # = (asignación: total = 5)
OR_PREC     = 3   # or, || (tu Fase 2)
AND_PREC    = 4   # and, && (tu Fase 2)
EQUALS      = 5   # ==, !=
LESSGREATER = 6   # <, >, <=, >=
SUM         = 7   # +, -
PRODUCT     = 8   # *, /
POWER       = 9   # ** (potencia)
PREFIX      = 10  # !x, -5 (operadores unarios)
CALL        = 11  # funcion(...)
INDEX       = 12  # arreglo[...]

# Tabla de precedencias por tipo de operador
PRECEDENCES = {
    ASSIGN: ASSIGN_PREC,
    OR: OR_PREC,
    AND: AND_PREC,
    EQ: EQUALS,
    NOT_EQ: EQUALS,
    LT: LESSGREATER,
    GT: LESSGREATER,
    LTE: LESSGREATER,
    GTE: LESSGREATER,
    PLUS: SUM,
    MINUS: SUM,
    SLASH: PRODUCT,
    ASTERISK: PRODUCT,
    POW: POWER,
    LPAREN: CALL,
    LBRACKET: INDEX
}

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.cur_token = None
        self.peek_token = None
        self.errors = []
        self.prefix_parse_fns = {}
        self.infix_parse_fns = {}
        
        self.register_prefix(IDENT, self.parse_identifier)
        self.register_prefix(INT, self.parse_integer_literal)
        self.register_prefix(FLOAT, self.parse_float_literal)
        self.register_prefix(STRING, self.parse_string_literal)
        self.register_prefix(BANG, self.parse_prefix_expression)
        self.register_prefix(MINUS, self.parse_prefix_expression)
        self.register_prefix(TRUE, self.parse_boolean)
        self.register_prefix(FALSE, self.parse_boolean)
        self.register_prefix(LPAREN, self.parse_grouped_expression)
        self.register_prefix(IF, self.parse_if_expression)
        self.register_prefix(FUNCTION, self.parse_function_literal)
        self.register_prefix(LBRACKET, self.parse_array_literal)
        self.register_prefix(WHILE, self.parse_while_expression)
        self.register_prefix(FOR, self.parse_for_expression)

        self.register_infix(PLUS, self.parse_infix_expression)
        self.register_infix(MINUS, self.parse_infix_expression)
        self.register_infix(SLASH, self.parse_infix_expression)
        self.register_infix(ASTERISK, self.parse_infix_expression)
        self.register_infix(POW, self.parse_infix_expression)
        self.register_infix(EQ, self.parse_infix_expression)
        self.register_infix(NOT_EQ, self.parse_infix_expression)
        self.register_infix(LT, self.parse_infix_expression)
        self.register_infix(GT, self.parse_infix_expression)
        self.register_infix(LTE, self.parse_infix_expression)
        self.register_infix(GTE, self.parse_infix_expression)
        self.register_infix(AND, self.parse_infix_expression)
        self.register_infix(OR, self.parse_infix_expression)
        self.register_infix(LPAREN, self.parse_call_expression)
        self.register_infix(LBRACKET, self.parse_index_expression)
        self.register_infix(ASSIGN, self.parse_assign_expression)

        self.next_token()
        self.next_token()

    def register_prefix(self, token_type, fn):
        self.prefix_parse_fns[token_type] = fn

    def register_infix(self, token_type, fn):
        self.infix_parse_fns[token_type] = fn

    def next_token(self):
        self.cur_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def parse_program(self):
        program = Program()
        while self.cur_token.type != EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            self.next_token()
        return program

    def parse_statement(self):
        if self.cur_token.type == LET:
            return self.parse_let_statement()
        elif self.cur_token.type == RETURN:
            return self.parse_return_statement()
        elif self.cur_token.type == BREAK:
            return self.parse_break_statement()
        else:
            return self.parse_expression_statement()

    def parse_let_statement(self):
        stmt_token = self.cur_token
        if not self.expect_peek(IDENT): return None
        name = Identifier(self.cur_token, self.cur_token.literal)
        if not self.expect_peek(ASSIGN): return None
        self.next_token()
        value = self.parse_expression(LOWEST)
        if self.peek_token.type == SEMICOLON:
            self.next_token()
        return LetStatement(stmt_token, name, value)

    def parse_return_statement(self):
        stmt_token = self.cur_token
        self.next_token()
        return_value = self.parse_expression(LOWEST)
        if self.peek_token.type == SEMICOLON:
            self.next_token()
        return ReturnStatement(stmt_token, return_value)

    def parse_break_statement(self):
        stmt_token = self.cur_token
        if self.peek_token.type == SEMICOLON:
            self.next_token()
        return BreakStatement(stmt_token)

    def parse_expression_statement(self):
        stmt_token = self.cur_token
        expression = self.parse_expression(LOWEST)
        if self.peek_token.type == SEMICOLON:
            self.next_token()
        return ExpressionStatement(stmt_token, expression)

    def parse_expression(self, precedence):
        prefix = self.prefix_parse_fns.get(self.cur_token.type)
        if prefix is None:
            line = self.cur_token.line if self.cur_token else "?"
            col = self.cur_token.column if self.cur_token else "?"
            self.errors.append(f"Línea {line}, Columna {col}: no se encontró prefijo para {self.cur_token.type}")
            return None
        left_exp = prefix()
        while self.peek_token.type != SEMICOLON and precedence < self.peek_precedence():
            infix = self.infix_parse_fns.get(self.peek_token.type)
            if infix is None:
                return left_exp
            self.next_token()
            left_exp = infix(left_exp)
        return left_exp

    def parse_identifier(self):
        return Identifier(self.cur_token, self.cur_token.literal)

    def parse_integer_literal(self):
        try:
            value = int(self.cur_token.literal)
            return IntegerLiteral(self.cur_token, value)
        except ValueError:
            line = self.cur_token.line if self.cur_token else "?"
            col = self.cur_token.column if self.cur_token else "?"
            self.errors.append(f"Línea {line}, Columna {col}: no se pudo parsear {self.cur_token.literal} como entero")
            return None

    def parse_float_literal(self):
        try:
            value = float(self.cur_token.literal)
            return FloatLiteral(self.cur_token, value)
        except ValueError:
            line = self.cur_token.line if self.cur_token else "?"
            col = self.cur_token.column if self.cur_token else "?"
            self.errors.append(f"Línea {line}, Columna {col}: no se pudo parsear {self.cur_token.literal} como float")
            return None

    def parse_string_literal(self):
        return StringLiteral(self.cur_token, self.cur_token.literal)

    def parse_boolean(self):
        return Boolean(self.cur_token, self.cur_token.type == TRUE)

    def parse_grouped_expression(self):
        self.next_token()
        exp = self.parse_expression(LOWEST)
        if not self.expect_peek(RPAREN): return None
        return exp

    def parse_if_expression(self):
        token = self.cur_token
        if not self.expect_peek(LPAREN): return None
        self.next_token()
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(RPAREN): return None
        if not self.expect_peek(LBRACE): return None
        consequence = self.parse_block_statement()
        elifs = []
        while self.peek_token.type == ELIF:
            self.next_token()
            if not self.expect_peek(LPAREN): return None
            self.next_token()
            elif_cond = self.parse_expression(LOWEST)
            if not self.expect_peek(RPAREN): return None
            if not self.expect_peek(LBRACE): return None
            elif_cons = self.parse_block_statement()
            elifs.append((elif_cond, elif_cons))
        alternative = None
        if self.peek_token.type == ELSE:
            self.next_token()
            if not self.expect_peek(LBRACE): return None
            alternative = self.parse_block_statement()
        return IfExpression(token, condition, consequence, alternative, elifs)

    def parse_while_expression(self):
        token = self.cur_token
        if not self.expect_peek(LPAREN): return None
        self.next_token()
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(RPAREN): return None
        if not self.expect_peek(LBRACE): return None
        body = self.parse_block_statement()
        return WhileExpression(token, condition, body)

    def parse_for_expression(self):
        token = self.cur_token
        if not self.expect_peek(LPAREN): return None
        self.next_token()
        
        # 1. Inicialización
        init = None
        if self.cur_token.type != SEMICOLON:
            init = self.parse_statement()
        if self.cur_token.type == SEMICOLON:
            self.next_token()

        # 2. Condición
        condition = None
        if self.cur_token.type != SEMICOLON:
            condition = self.parse_expression(LOWEST)
            if not self.expect_peek(SEMICOLON): return None
        if self.cur_token.type == SEMICOLON:
            self.next_token()

        # 3. Incremento/Actualización
        update = None
        if self.cur_token.type != RPAREN:
            update = self.parse_expression(LOWEST)
        if not self.expect_peek(RPAREN): return None
        if not self.expect_peek(LBRACE): return None
        body = self.parse_block_statement()
        return ForExpression(token, init, condition, update, body)

    def parse_block_statement(self):
        token = self.cur_token
        statements = []
        self.next_token()
        while self.cur_token.type != RBRACE and self.cur_token.type != EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self.next_token()
        return BlockStatement(token, statements)

    def parse_function_literal(self):
        token = self.cur_token
        if not self.expect_peek(LPAREN): return None
        parameters = self.parse_function_parameters()
        if not self.expect_peek(LBRACE): return None
        body = self.parse_block_statement()
        return FunctionLiteral(token, parameters, body)

    def parse_function_parameters(self):
        identifiers = []
        if self.peek_token.type == RPAREN:
            self.next_token()
            return identifiers
        self.next_token()
        ident = Identifier(self.cur_token, self.cur_token.literal)
        identifiers.append(ident)
        while self.peek_token.type == COMMA:
            self.next_token()
            self.next_token()
            ident = Identifier(self.cur_token, self.cur_token.literal)
            identifiers.append(ident)
        if not self.expect_peek(RPAREN): return None
        return identifiers

    def parse_array_literal(self):
        token = self.cur_token
        elements = self.parse_expression_list(RBRACKET)
        return ArrayLiteral(token, elements)

    def parse_expression_list(self, end):
        elements = []
        if self.peek_token.type == end:
            self.next_token()
            return elements
        self.next_token()
        elements.append(self.parse_expression(LOWEST))
        while self.peek_token.type == COMMA:
            self.next_token()
            self.next_token()
            elements.append(self.parse_expression(LOWEST))
        if not self.expect_peek(end): return None
        return elements

    def parse_prefix_expression(self):
        token = self.cur_token
        operator = self.cur_token.literal
        self.next_token()
        right = self.parse_expression(PREFIX)
        return PrefixExpression(token, operator, right)

    def parse_infix_expression(self, left):
        # Construye InfixExpression; ** es right-assoc (precedencia-1), el resto left-assoc
        token      = self.cur_token
        operator   = self.cur_token.literal
        precedence = self.cur_precedence()
        self.next_token()
        if operator == "**":
            right = self.parse_expression(precedence - 1)   # asociatividad a la derecha
        else:
            right = self.parse_expression(precedence)       # asociatividad a la izquierda
        return InfixExpression(token, left, operator, right)
        
    def parse_assign_expression(self, left):
        # Validación de lvalue: solo identificadores o expresiones de índice (arr[i]) son asignables
        if not isinstance(left, (Identifier, IndexExpression)):
            line = self.cur_token.line if self.cur_token else "?"
            col = self.cur_token.column if self.cur_token else "?"
            self.errors.append(f"Línea {line}, Columna {col}: se esperaba un identificador o indexación para la asignación")
            return None
        token = self.cur_token
        self.next_token()
        value = self.parse_expression(LOWEST)
        return AssignExpression(token, left, value)

    def parse_call_expression(self, function):
        token = self.cur_token
        arguments = self.parse_expression_list(RPAREN)
        return CallExpression(token, function, arguments)

    def parse_index_expression(self, left):
        token = self.cur_token
        self.next_token()
        index = self.parse_expression(LOWEST)
        if not self.expect_peek(RBRACKET): return None
        return IndexExpression(token, left, index)

    def expect_peek(self, t):
        if self.peek_token.type == t:
            self.next_token()
            return True
        else:
            self.peek_error(t)
            return False

    def peek_error(self, t):
        line = self.peek_token.line if self.peek_token else "?"
        col = self.peek_token.column if self.peek_token else "?"
        msg = f"Línea {line}, Columna {col}: se esperaba que el siguiente token fuera {t}, pero fue {self.peek_token.type}"
        self.errors.append(msg)

    def cur_precedence(self):
        return PRECEDENCES.get(self.cur_token.type, LOWEST)

    def peek_precedence(self):
        return PRECEDENCES.get(self.peek_token.type, LOWEST)
