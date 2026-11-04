# ANALIZADOR LÉXICO — convierte texto fuente en stream de tokens con posición exacta

from tokens import Token, lookup_ident, EQ, ASSIGN, PLUS, MINUS, BANG, NOT_EQ
from tokens import SLASH, POW, ASTERISK, LTE, LT, GTE, GT, SEMICOLON, COMMA
from tokens import LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET, EOF, ILLEGAL, INT, FLOAT, STRING, AND, OR

class Lexer:
    def __init__(self, input_text):
        self.input         = input_text
        self.position      = 0
        self.read_position = 0
        self.ch            = ''
        self.line          = 1
        self.column        = 0
        self.errors        = []   # errores léxicos (cadenas no cerradas, chars ilegales)
        self.read_char()

    def read_char(self):
        # Avanza el cursor; actualiza línea y columna para tracking de posición exacta
        if self.ch == '\n':
            self.line  += 1
            self.column = 0
        self.ch = self.input[self.read_position] if self.read_position < len(self.input) else ''
        self.position      = self.read_position
        self.read_position += 1
        self.column        += 1

    def peek_char(self):
        # Lee el siguiente carácter sin consumirlo (lookahead de 1)
        return self.input[self.read_position] if self.read_position < len(self.input) else ''

    def next_token(self):
        self.skip_whitespace()
        tok_line = self.line
        tok_col  = self.column
        tok      = None

        if self.ch == '=':
            if self.peek_char() == '=':
                ch = self.ch; self.read_char()
                tok = Token(EQ, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ASSIGN, self.ch, tok_line, tok_col)
        elif self.ch == '+':
            tok = Token(PLUS, self.ch, tok_line, tok_col)
        elif self.ch == '-':
            tok = Token(MINUS, self.ch, tok_line, tok_col)
        elif self.ch == '!':
            if self.peek_char() == '=':
                ch = self.ch; self.read_char()
                tok = Token(NOT_EQ, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(BANG, self.ch, tok_line, tok_col)
        elif self.ch == '/':
            tok = Token(SLASH, self.ch, tok_line, tok_col)
        elif self.ch == '*':
            if self.peek_char() == '*':
                ch = self.ch; self.read_char()
                tok = Token(POW, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ASTERISK, self.ch, tok_line, tok_col)
        elif self.ch == '<':
            if self.peek_char() == '=':
                ch = self.ch; self.read_char()
                tok = Token(LTE, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(LT, self.ch, tok_line, tok_col)
        elif self.ch == '>':
            if self.peek_char() == '=':
                ch = self.ch; self.read_char()
                tok = Token(GTE, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(GT, self.ch, tok_line, tok_col)
        elif self.ch == ';':
            tok = Token(SEMICOLON, self.ch, tok_line, tok_col)
        elif self.ch == ',':
            tok = Token(COMMA, self.ch, tok_line, tok_col)
        elif self.ch == '(':
            tok = Token(LPAREN, self.ch, tok_line, tok_col)
        elif self.ch == ')':
            tok = Token(RPAREN, self.ch, tok_line, tok_col)
        elif self.ch == '{':
            tok = Token(LBRACE, self.ch, tok_line, tok_col)
        elif self.ch == '}':
            tok = Token(RBRACE, self.ch, tok_line, tok_col)
        elif self.ch == '[':
            tok = Token(LBRACKET, self.ch, tok_line, tok_col)
        elif self.ch == ']':
            tok = Token(RBRACKET, self.ch, tok_line, tok_col)
        elif self.ch == '&':
            # && → AND; & suelto es ilegal en este lenguaje
            if self.peek_char() == '&':
                ch = self.ch; self.read_char()
                tok = Token(AND, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ILLEGAL, self.ch, tok_line, tok_col)
        elif self.ch == '|':
            # || → OR; | suelto es ilegal en este lenguaje
            if self.peek_char() == '|':
                ch = self.ch; self.read_char()
                tok = Token(OR, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ILLEGAL, self.ch, tok_line, tok_col)
        elif self.ch == '"' or self.ch == "'":
            quote_type = self.ch
            str_val, err = self.read_string(quote_type)
            if err is not None:
                self.errors.append(err)
                tok = Token(ILLEGAL, err, tok_line, tok_col)
            else:
                tok = Token(STRING, str_val, tok_line, tok_col)
        elif self.ch == '':
            tok = Token(EOF, "", tok_line, tok_col)
        else:
            if self.is_letter(self.ch):
                literal = self.read_identifier()
                type_   = lookup_ident(literal)
                return Token(type_, literal, tok_line, tok_col)   # ya avanzó en read_identifier
            elif self.is_digit(self.ch):
                num_literal, num_type = self.read_number()
                return Token(num_type, num_literal, tok_line, tok_col)  # ya avanzó en read_number
            else:
                tok = Token(ILLEGAL, self.ch, tok_line, tok_col)

        self.read_char()
        return tok

    def skip_whitespace(self):
        while self.ch in (' ', '\t', '\n', '\r'):
            self.read_char()

    def is_letter(self, ch):
        return 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_'

    def is_digit(self, ch):
        return '0' <= ch <= '9'

    def read_identifier(self):
        pos = self.position
        while self.is_letter(self.ch) or self.is_digit(self.ch):
            self.read_char()
        return self.input[pos:self.position]

    def read_number(self):
        pos      = self.position
        is_float = False
        while self.is_digit(self.ch):
            self.read_char()
        # Punto decimal válido: '.' seguido de al menos un dígito
        if self.ch == '.' and self.is_digit(self.peek_char()):
            is_float = True
            self.read_char()  # consume el punto
            while self.is_digit(self.ch):
                self.read_char()
        return self.input[pos:self.position], (FLOAT if is_float else INT)

    def read_string(self, quote_type):
        chars      = []
        start_line = self.line
        start_col  = self.column
        self.read_char()  # avanza más allá de la comilla de apertura
        while self.ch != quote_type:
            # Cadena sin cerrar: salto de línea o EOF dentro de la cadena
            if self.ch == '' or self.ch == '\n':
                return None, f"Línea {start_line}, Columna {start_col}: cadena no cerrada antes de fin de línea o archivo"
            if self.ch == '\\':
                self.read_char()
                # Tabla de secuencias de escape reconocidas
                if   self.ch == 'n':         chars.append('\n')
                elif self.ch == 't':         chars.append('\t')
                elif self.ch == 'r':         chars.append('\r')
                elif self.ch == '\\':        chars.append('\\')
                elif self.ch == quote_type:  chars.append(quote_type)
                elif self.ch == '':
                    return None, f"Línea {start_line}, Columna {start_col}: cadena no cerrada antes de fin de archivo"
                else:
                    chars.append(self.ch)   # escape desconocido: se pasa literal
            else:
                chars.append(self.ch)
            self.read_char()
        return "".join(chars), None
