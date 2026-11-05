# PRUEBAS DEL PARSER: precedencia, asociatividad y forma del AST
# Se compara el AST serializado como S-expression (ver helpers.sexp).

import unittest
from helpers import parse, sexp
import ast_nodes as ast


def ast_of(source):
    program, parser, lexer = parse(source)
    assert not parser.errors, f"errores de parseo inesperados: {parser.errors}"
    return sexp(program)


class TestPrecedencia(unittest.TestCase):

    def test_multiplicacion_antes_que_suma(self):
        self.assertEqual(ast_of("1 + 2 * 3"), "(+ 1 (* 2 3))")
        self.assertEqual(ast_of("1 * 2 + 3"), "(+ (* 1 2) 3)")

    def test_division_antes_que_resta(self):
        self.assertEqual(ast_of("10 - 8 / 2"), "(- 10 (/ 8 2))")

    def test_parentesis_alteran_la_precedencia(self):
        self.assertEqual(ast_of("(1 + 2) * 3"), "(* (+ 1 2) 3)")

    def test_potencia_antes_que_producto(self):
        self.assertEqual(ast_of("2 * 3 ** 2"), "(* 2 (** 3 2))")

    def test_prefijo_antes_que_infijo(self):
        self.assertEqual(ast_of("-1 + 2"), "(+ (- 1) 2)")
        self.assertEqual(ast_of("!true == false"), "(== (! true) false)")

    def test_relacional_menor_que_aritmetica(self):
        self.assertEqual(ast_of("1 + 2 < 3 * 4"), "(< (+ 1 2) (* 3 4))")

    def test_igualdad_menor_que_relacional(self):
        self.assertEqual(ast_of("1 < 2 == true"), "(== (< 1 2) true)")

    def test_and_antes_que_or(self):
        self.assertEqual(ast_of("a or b and c"), "(or a (and b c))")

    def test_logicos_menor_que_igualdad(self):
        self.assertEqual(ast_of("a == 1 and b != 2"), "(and (== a 1) (!= b 2))")

    def test_llamada_e_indice_son_los_mas_fuertes(self):
        self.assertEqual(ast_of("-f(1)"), "(- (call f 1))")
        self.assertEqual(ast_of("a[0] + 1"), "(+ (index a 0) 1)")
        self.assertEqual(ast_of("2 * a[1]"), "(* 2 (index a 1))")


class TestAsociatividad(unittest.TestCase):

    def test_resta_asocia_a_la_izquierda(self):
        self.assertEqual(ast_of("10 - 4 - 3"), "(- (- 10 4) 3)")

    def test_division_asocia_a_la_izquierda(self):
        self.assertEqual(ast_of("100 / 10 / 2"), "(/ (/ 100 10) 2)")

    def test_suma_asocia_a_la_izquierda(self):
        self.assertEqual(ast_of("1 + 2 + 3"), "(+ (+ 1 2) 3)")

    def test_potencia_asocia_a_la_derecha(self):
        self.assertEqual(ast_of("2 ** 3 ** 2"), "(** 2 (** 3 2))")

    def test_asignacion_asocia_a_la_derecha(self):
        self.assertEqual(ast_of("a = b = 3"), "(= a (= b 3))")


class TestConstruccionAST(unittest.TestCase):

    def test_let_statement(self):
        program, parser, _ = parse("let x = 5;")
        self.assertEqual(parser.errors, [])
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ast.LetStatement)
        self.assertEqual(stmt.name.value, "x")
        self.assertIsInstance(stmt.value, ast.IntegerLiteral)
        self.assertEqual(stmt.value.value, 5)

    def test_punto_y_coma_es_opcional(self):
        self.assertEqual(ast_of("let a = 1\nlet b = 2"), "(let a 1) ; (let b 2)")

    def test_return_y_break(self):
        self.assertEqual(ast_of("return 1 + 2;"), "(return (+ 1 2))")
        self.assertEqual(ast_of("break;"), "(break)")

    def test_literal_de_cadena_y_flotante(self):
        self.assertEqual(ast_of('"hola"'), "'hola'")
        self.assertEqual(ast_of("3.5"), "3.5")

    def test_if_else(self):
        self.assertEqual(ast_of("if (x < 1) { 1 } else { 2 }"),
                         "(if (< x 1) {1} else {2})")

    def test_if_elif_else(self):
        self.assertEqual(
            ast_of("if (a) { 1 } elif (b) { 2 } elif (c) { 3 } else { 4 }"),
            "(if a {1} elif b {2} elif c {3} else {4})")

    def test_if_anidado(self):
        self.assertEqual(
            ast_of("if (a) { if (b) { 1 } else { 2 } }"),
            "(if a {(if b {1} else {2})})")

    def test_while(self):
        self.assertEqual(ast_of("while (i < 3) { i = i + 1 }"),
                         "(while (< i 3) {(= i (+ i 1))})")

    def test_for_con_tres_partes(self):
        self.assertEqual(
            ast_of("for (let i = 0; i < 3; i = i + 1) { i }"),
            "(for (let i 0) (< i 3) (= i (+ i 1)) {i})")

    def test_funcion_con_parametros_y_llamada(self):
        self.assertEqual(
            ast_of("let suma = function(a, b) { return a + b }; suma(1, 2)"),
            "(let suma (fn (a,b) {(return (+ a b))})) ; (call suma 1 2)")

    def test_funcion_sin_parametros(self):
        self.assertEqual(ast_of("function() { 1 }"), "(fn () {1})")

    def test_llamada_sin_argumentos(self):
        self.assertEqual(ast_of("f()"), "(call f)")

    def test_arreglo_literal_vacio_y_con_elementos(self):
        self.assertEqual(ast_of("[]"), "[]")
        self.assertEqual(ast_of("[1, 2 * 3, x]"), "[1 (* 2 3) x]")

    def test_indexacion_y_asignacion_por_indice(self):
        self.assertEqual(ast_of("a[1 + 1]"), "(index a (+ 1 1))")
        self.assertEqual(ast_of("a[0] = 9"), "(= (index a 0) 9)")

    def test_cantidad_de_sentencias(self):
        program, _, _ = parse("let a = 1; let b = 2; a + b")
        self.assertEqual(len(program.statements), 3)

    def test_programa_vacio(self):
        program, parser, _ = parse("")
        self.assertEqual(program.statements, [])
        self.assertEqual(parser.errors, [])


if __name__ == "__main__":
    unittest.main()
