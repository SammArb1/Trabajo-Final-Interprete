# ANALIZADOR LEXICO

from tokens import Token, lookup_ident, EQ, ASSIGN, PLUS, MINUS, BANG, NOT_EQ
from tokens import SLASH, POW, ASTERISK, LTE, LT, GTE, GT, SEMICOLON, COMMA
from tokens import LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET, EOF, ILLEGAL, INT, STRING, AND, OR

class Lexer:
    def __init__(self, input_text):
        self.input = input_text
        self.position = 0
        self.read_position = 0
        self.ch = ''
        self.line = 1
        self.column = 0
        self.errors = []
        self.read_char()

    def read_char(self):
        if self.ch == '\n':
            self.line += 1
            self.column = 0

        if self.read_position >= len(self.input):
            self.ch = ''
        else:
            self.ch = self.input[self.read_position]
        self.position = self.read_position
        self.read_position += 1
        self.column += 1

    def peek_char(self):
        if self.read_position >= len(self.input):
            return ''
        return self.input[self.read_position]

    def next_token(self):
        self.skip_whitespace()
        tok = None
        tok_line = self.line
        tok_col = self.column

        if self.ch == '=':
            if self.peek_char() == '=':
                ch = self.ch
                self.read_char()
                tok = Token(EQ, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ASSIGN, self.ch, tok_line, tok_col)
        elif self.ch == '+':
            tok = Token(PLUS, self.ch, tok_line, tok_col)
        elif self.ch == '-':
            tok = Token(MINUS, self.ch, tok_line, tok_col)
        elif self.ch == '!':
            if self.peek_char() == '=':
                ch = self.ch
                self.read_char()
                tok = Token(NOT_EQ, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(BANG, self.ch, tok_line, tok_col)
        elif self.ch == '/':
            tok = Token(SLASH, self.ch, tok_line, tok_col)
        elif self.ch == '*':
            if self.peek_char() == '*':
                ch = self.ch
                self.read_char()
                tok = Token(POW, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ASTERISK, self.ch, tok_line, tok_col)
        elif self.ch == '<':
            if self.peek_char() == '=':
                ch = self.ch
                self.read_char()
                tok = Token(LTE, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(LT, self.ch, tok_line, tok_col)
        elif self.ch == '>':
            if self.peek_char() == '=':
                ch = self.ch
                self.read_char()
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
            if self.peek_char() == '&':
                ch = self.ch
                self.read_char()
                tok = Token(AND, ch + self.ch, tok_line, tok_col)
            else:
                tok = Token(ILLEGAL, self.ch, tok_line, tok_col)
        elif self.ch == '|':
            if self.peek_char() == '|':
                ch = self.ch
                self.read_char()
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
                type_ = lookup_ident(literal)
                return Token(type_, literal, tok_line, tok_col)
            elif self.is_digit(self.ch):
                return Token(INT, self.read_number(), tok_line, tok_col)
            else:
                tok = Token(ILLEGAL, self.ch, tok_line, tok_col)

        self.read_char()
        return tok

    def skip_whitespace(self):
        while self.ch in [' ', '\t', '\n', '\r']:
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
        pos = self.position
        while self.is_digit(self.ch):
            self.read_char()
        return self.input[pos:self.position]

    def read_string(self, quote_type):
        chars = []
        start_line = self.line
        start_col = self.column
        self.read_char()  # avanzar de la comilla de apertura
        while self.ch != quote_type:
            if self.ch == '' or self.ch == '\n':
                err = f"Línea {start_line}, Columna {start_col}: cadena no cerrada antes de fin de línea o archivo"
                return None, err
            if self.ch == '\\':
                self.read_char()
                if self.ch == 'n':
                    chars.append('\n')
                elif self.ch == 't':
                    chars.append('\t')
                elif self.ch == 'r':
                    chars.append('\r')
                elif self.ch == '\\':
                    chars.append('\\')
                elif self.ch == quote_type:
                    chars.append(quote_type)
                elif self.ch == '':
                    err = f"Línea {start_line}, Columna {start_col}: cadena no cerrada antes de fin de archivo"
                    return None, err
                else:
                    chars.append(self.ch)
            else:
                chars.append(self.ch)
            self.read_char()
        return "".join(chars), None
