# PRUEBAS DEL LEXER: tokens válidos, palabras reservadas, posición (línea/columna) e inválidos

import unittest
from helpers import tokenize
import tokens as T


def types(source):
    toks, _ = tokenize(source)
    return [t.type for t in toks]


class TestLexerTokensValidos(unittest.TestCase):

    def test_let_statement_completo(self):
        self.assertEqual(
            types("let x = 5;"),
            [T.LET, T.IDENT, T.ASSIGN, T.INT, T.SEMICOLON],
        )

    def test_literales_numericos(self):
        toks, _ = tokenize("42 3.14")
        self.assertEqual((toks[0].type, toks[0].literal), (T.INT, "42"))
        self.assertEqual((toks[1].type, toks[1].literal), (T.FLOAT, "3.14"))

    def test_punto_sin_digito_no_es_float(self):
        # "5." no forma un float: el 5 es INT y el '.' queda como carácter ilegal
        self.assertEqual(types("5."), [T.INT, T.ILLEGAL])

    def test_cadenas_comilla_doble_y_simple(self):
        toks, lexer = tokenize("\"hola\" 'mundo'")
        self.assertEqual([(t.type, t.literal) for t in toks],
                         [(T.STRING, "hola"), (T.STRING, "mundo")])
        self.assertEqual(lexer.errors, [])

    def test_secuencias_de_escape(self):
        toks, _ = tokenize(r'"a\nb\t\"c\""')
        self.assertEqual(toks[0].literal, 'a\nb\t"c"')

    def test_operadores_de_un_caracter(self):
        self.assertEqual(
            types("+ - * / < > = !"),
            [T.PLUS, T.MINUS, T.ASTERISK, T.SLASH, T.LT, T.GT, T.ASSIGN, T.BANG],
        )

    def test_operadores_de_dos_caracteres(self):
        self.assertEqual(
            types("== != <= >= **"),
            [T.EQ, T.NOT_EQ, T.LTE, T.GTE, T.POW],
        )

    def test_delimitadores(self):
        self.assertEqual(
            types("( ) { } [ ] , ;"),
            [T.LPAREN, T.RPAREN, T.LBRACE, T.RBRACE,
             T.LBRACKET, T.RBRACKET, T.COMMA, T.SEMICOLON],
        )

    def test_palabras_reservadas(self):
        src = "function let true false if else elif return for while break and or"
        self.assertEqual(
            types(src),
            [T.FUNCTION, T.LET, T.TRUE, T.FALSE, T.IF, T.ELSE, T.ELIF,
             T.RETURN, T.FOR, T.WHILE, T.BREAK, T.AND, T.OR],
        )

    def test_operadores_logicos_simbolicos(self):
        # && y || producen los mismos tokens que 'and' y 'or'
        self.assertEqual(types("&& ||"), [T.AND, T.OR])

    def test_identificadores_no_se_confunden_con_reservadas(self):
        toks, _ = tokenize("letra iffy _x1 whilex")
        self.assertTrue(all(t.type == T.IDENT for t in toks))
        self.assertEqual([t.literal for t in toks], ["letra", "iffy", "_x1", "whilex"])

    def test_espacios_y_saltos_de_linea_se_ignoran(self):
        self.assertEqual(types("  1 \n\t 2\r\n 3  "), [T.INT, T.INT, T.INT])

    def test_entrada_vacia_solo_produce_eof(self):
        toks, _ = tokenize("")
        self.assertEqual(toks, [])


class TestLexerPosicion(unittest.TestCase):

    def test_linea_y_columna_en_una_sola_linea(self):
        toks, _ = tokenize("let x = 5;")
        posiciones = [(t.type, t.line, t.column) for t in toks]
        self.assertEqual(posiciones, [
            (T.LET, 1, 1), (T.IDENT, 1, 5), (T.ASSIGN, 1, 7),
            (T.INT, 1, 9), (T.SEMICOLON, 1, 10),
        ])

    def test_linea_y_columna_en_varias_lineas(self):
        toks, _ = tokenize("let a = 1\nlet b = 22\n  a + b")
        por_literal = {}
        for t in toks:
            por_literal.setdefault(t.literal, (t.line, t.column))
        self.assertEqual(por_literal["a"], (1, 5))
        self.assertEqual(por_literal["22"], (2, 9))
        # tercera línea: dos espacios de sangría
        ultima = toks[-3:]
        self.assertEqual([(t.literal, t.line, t.column) for t in ultima],
                         [("a", 3, 3), ("+", 3, 5), ("b", 3, 7)])

    def test_posicion_de_operador_doble(self):
        toks, _ = tokenize("a == b")
        self.assertEqual((toks[1].type, toks[1].line, toks[1].column), (T.EQ, 1, 3))

    def test_posicion_de_cadena(self):
        toks, _ = tokenize('x = "hola"')
        self.assertEqual((toks[2].type, toks[2].line, toks[2].column), (T.STRING, 1, 5))


class TestLexerInvalidos(unittest.TestCase):

    def test_caracter_ilegal_con_posicion(self):
        toks, _ = tokenize("let x = @;")
        ilegal = [t for t in toks if t.type == T.ILLEGAL]
        self.assertEqual(len(ilegal), 1)
        self.assertEqual((ilegal[0].literal, ilegal[0].line, ilegal[0].column), ("@", 1, 9))

    def test_ampersand_y_pipe_sueltos_son_ilegales(self):
        self.assertEqual(types("&"), [T.ILLEGAL])
        self.assertEqual(types("|"), [T.ILLEGAL])

    def test_cadena_sin_cerrar_registra_error_con_posicion(self):
        toks, lexer = tokenize('let s = "hola')
        self.assertEqual(len(lexer.errors), 1)
        self.assertIn("Línea 1, Columna 9", lexer.errors[0])
        self.assertIn("cadena no cerrada", lexer.errors[0])
        self.assertEqual(toks[-1].type, T.ILLEGAL)

    def test_cadena_sin_cerrar_en_linea_posterior(self):
        _, lexer = tokenize('let a = 1\nlet s = "hola\nlet b = 2')
        self.assertEqual(len(lexer.errors), 1)
        self.assertIn("Línea 2", lexer.errors[0])

    def test_cadena_con_escape_al_final_sin_cerrar(self):
        _, lexer = tokenize('"abc\\')
        self.assertEqual(len(lexer.errors), 1)

    def test_programa_valido_no_registra_errores(self):
        _, lexer = tokenize('let x = "ok"; print(x)')
        self.assertEqual(lexer.errors, [])


if __name__ == "__main__":
    unittest.main()
