# PRUEBAS DEL FRONTEND (lexer + parser) — ejecutar con: python -m unittest test_frontend -v

import unittest
from lexer import Lexer
from parser import Parser
from environment import Environment
from evaluator import evaluate
from tokens import *


def tokens_of(src):
    lx = Lexer(src)
    toks = []
    while True:
        t = lx.next_token()
        toks.append(t)
        if t.type == EOF:
            return toks, lx


def parse(src):
    lx = Lexer(src)
    p = Parser(lx)
    return p.parse_program(), lx, p


def run(src):
    program, lx, p = parse(src)
    assert not lx.errors and not p.errors, (lx.errors, p.errors)
    return evaluate(program, Environment()).inspect()


class TestPosicionTokens(unittest.TestCase):
    def test_linea_y_columna(self):
        toks, _ = tokens_of("let x = 5;\n  y")
        pos = [(t.literal, t.line, t.column) for t in toks]
        self.assertIn(("let", 1, 1), pos)
        self.assertIn(("x", 1, 5), pos)
        self.assertIn(("5", 1, 9), pos)
        self.assertIn(("y", 2, 3), pos)

    def test_alias_col(self):
        t = Token(IDENT, "a", 3, 7)
        self.assertEqual((t.line, t.col), (3, 7))


class TestErroresLexicos(unittest.TestCase):
    def test_caracter_ilegal(self):
        toks, lx = tokens_of("let x = 1;\n  let y = @;")
        ill = [t for t in toks if t.type == ILLEGAL]
        self.assertEqual([(t.literal, t.line, t.column) for t in ill], [("@", 2, 11)])
        self.assertEqual(len(lx.errors), 1)
        self.assertIn("Línea 2, Columna 11", lx.errors[0])

    def test_and_or_sueltos_son_ilegales(self):
        _, lx = tokens_of("a & b | c")
        self.assertEqual(len(lx.errors), 2)

    def test_cadena_sin_cerrar_eof(self):
        toks, lx = tokens_of('let s = "hola')
        self.assertEqual(toks[3].type, ILLEGAL)
        self.assertIn("Línea 1, Columna 9", lx.errors[0])

    def test_cadena_sin_cerrar_salto_de_linea(self):
        _, lx = tokens_of('let s = "hola\nlet x = 1;')
        self.assertEqual(len(lx.errors), 1)   # no se "traga" el resto del archivo


class TestBreak(unittest.TestCase):
    def assert_break_error(self, src):
        _, _, p = parse(src)
        self.assertTrue(any("'break' fuera de un ciclo" in e for e in p.errors), p.errors)

    def test_break_en_toplevel(self):
        self.assert_break_error("break;")

    def test_break_en_if_sin_ciclo(self):
        self.assert_break_error("if (true) { break; }")

    def test_break_en_funcion_dentro_de_ciclo(self):
        self.assert_break_error("while (true) { let f = function() { break; }; break; }")

    def test_break_valido(self):
        self.assertEqual(run("let i=0; while (true) { i=i+1; if (i>3) { break; } } i;"), "4")
        self.assertEqual(run("let n=0; for (let i=0;i<9;i=i+1) { if (i==2) { break; } n=n+1; } n;"), "2")

    def test_loop_depth_se_restaura(self):
        _, _, p = parse("while (true) { break; } break;")
        self.assertEqual(len(p.errors), 1)   # solo el segundo break es inválido


class TestFor(unittest.TestCase):
    def test_for_completo(self):
        self.assertEqual(run("let s=0; for (let i=0; i<4; i=i+1) { s = s + i; } s;"), "6")

    def test_for_sin_init(self):
        self.assertEqual(run("let i=0; for (; i<3; i=i+1) { } i;"), "3")

    def test_for_sin_update(self):
        self.assertEqual(run("let n=0; for (let j=0; j<3; ) { j=j+1; n=n+1; } n;"), "3")

    def test_for_sin_condicion(self):
        self.assertEqual(run("let n=0; for (let j=0;; j=j+1) { if (j>2) { break; } n=n+1; } n;"), "3")

    def test_for_infinito_con_break(self):
        self.assertEqual(run("let i=0; for (;;) { i=i+1; if (i>2) { break; } } i;"), "3")

    def test_for_falta_punto_y_coma(self):
        _, _, p = parse("for (let i=0 i<3; i=i+1) { }")
        self.assertTrue(p.errors)


class TestPrecedencia(unittest.TestCase):
    def test_pow_sobre_producto(self):
        self.assertEqual(run("2 * 3 ** 2;"), "18")
        self.assertEqual(run("2 ** 3 * 2;"), "16")
        self.assertEqual(run("10 / 2 ** 2;"), "2.5")

    def test_pow_asociativo_por_derecha(self):
        self.assertEqual(run("2 ** 3 ** 2;"), "512")     # 2 ** 9, no (2 ** 3) ** 2 = 64

    def test_menos_unario_con_pow(self):
        self.assertEqual(run("-2 ** 2;"), "-4")
        self.assertEqual(run("2 ** -1;"), "0.5")

    def test_resta_asociativa_por_izquierda(self):
        self.assertEqual(run("10 - 3 - 2;"), "5")

    def test_and_sobre_or(self):
        self.assertEqual(run("true or false and false;"), "true")
        self.assertEqual(run("(true or false) and false;"), "false")

    def test_relacional_sobre_logico(self):
        self.assertEqual(run("1 < 2 and 2 < 3;"), "true")
        self.assertEqual(run("1 == 1 && 2 != 3 || false;"), "true")

    def test_aritmetica_sobre_relacional(self):
        self.assertEqual(run("1 + 1 == 2;"), "true")


class TestAsignacionPorIndice(unittest.TestCase):
    def test_basica(self):
        self.assertEqual(run("let a=[1,2,3]; a[0] = 9; a[0];"), "9")

    def test_indice_y_valor_son_expresiones(self):
        self.assertEqual(run("let a=[1,2,3]; a[1+1] = a[0] + 5; a;"), "[1, 2, 6]")

    def test_anidada(self):
        self.assertEqual(run("let a=[[1,2],[3,4]]; a[1][0] = 9; a;"), "[[1, 2], [9, 4]]")

    def test_encadenada(self):
        self.assertEqual(run("let a=1; let b=2; a = b = 5; a;"), "5")

    def test_destino_invalido(self):
        _, _, p = parse("1 = 2;")
        self.assertTrue(p.errors)
        _, _, p = parse("a + b = 3;")
        self.assertTrue(p.errors)


if __name__ == "__main__":
    unittest.main()