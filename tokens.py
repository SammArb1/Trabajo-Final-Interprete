# DEFINICIÓN DE TOKENS — constantes de tipo, tabla de palabras reservadas y clase Token

# --- Tipos de tokens especiales ---
ILLEGAL = "ILLEGAL"   # carácter no reconocido
EOF     = "EOF"       # fin de entrada

# --- Tipos de tokens de valor ---
IDENT  = "IDENT"     # identificadores de usuario
INT    = "INT"        # literales enteros
FLOAT  = "FLOAT"     # literales de punto flotante
STRING = "STRING"     # literales de cadena de texto

# --- Operadores ---
ASSIGN   = "="
PLUS     = "+"
MINUS    = "-"
BANG     = "!"
ASTERISK = "*"
SLASH    = "/"
LT       = "<"
GT       = ">"
LTE      = "<="
GTE      = ">="
EQ       = "=="
NOT_EQ   = "!="
POW      = "**"
AND      = "AND"      # operador lógico (también captura &&)
OR       = "OR"       # operador lógico (también captura ||)

# --- Delimitadores ---
COMMA     = ","
SEMICOLON = ";"
LPAREN    = "("
RPAREN    = ")"
LBRACE    = "{"
RBRACE    = "}"
LBRACKET  = "["
RBRACKET  = "]"

# --- Palabras reservadas ---
FUNCTION = "FUNCTION"
LET      = "LET"
TRUE     = "TRUE"
FALSE    = "FALSE"
IF       = "IF"
ELSE     = "ELSE"
ELIF     = "ELIF"
RETURN   = "RETURN"
FOR      = "FOR"
WHILE    = "WHILE"
BREAK    = "BREAK"

# Tabla de despacho: identificador literal → tipo de token reservado
KEYWORDS = {
    "function": FUNCTION,
    "let":      LET,
    "true":     TRUE,
    "false":    FALSE,
    "if":       IF,
    "else":     ELSE,
    "elif":     ELIF,
    "return":   RETURN,
    "for":      FOR,
    "while":    WHILE,
    "break":    BREAK,
    "and":      AND,
    "or":       OR,
}

class Token:
    # Almacena tipo, valor literal y posición exacta en la fuente para diagnósticos
    def __init__(self, type, literal, line=1, column=1):
        self.type    = type
        self.literal = literal
        self.line    = line
        self.column  = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.literal)}, {self.line}:{self.column})"

def lookup_ident(ident):
    # Retorna el tipo reservado si coincide, IDENT si es un nombre de usuario
    return KEYWORDS.get(ident, IDENT)
