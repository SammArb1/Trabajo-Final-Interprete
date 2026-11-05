# PRUEBAS DE ERRORES: en qué etapa se detecta cada error y qué mensaje produce.
#   léxico      -> lexer.errors
#   sintáctico  -> parser.errors (con línea y columna)
#   ejecución   -> objeto Error devuelto por el evaluador (el proceso Python no se cae)

import os
import subprocess
import sys
import tempfile
import unittest

from helpers import ROOT, parse, run, tokenize
from objects import ObjType


def assert_runtime_error(testcase, source, fragmento):
    r = run(source)
    testcase.assertEqual(r.type(), ObjType.ERROR, f"se esperaba Error para: {source!r}")
    testcase.assertIn(fragmento, r.message)


class TestErroresDeEjecucion(unittest.TestCase):

    def test_division_por_cero_enteros(self):
        assert_runtime_error(self, "1 / 0", "división por cero")

    def test_division_por_cero_flotantes(self):
        assert_runtime_error(self, "1.5 / 0.0", "división por cero")

    def test_division_por_cero_con_variable(self):
        assert_runtime_error(self, "let d = 0; 10 / d", "división por cero")

    def test_cero_elevado_a_potencia_negativa(self):
        assert_runtime_error(self, "0 ** -1", "potencia")

    def test_variable_no_declarada(self):
        assert_runtime_error(self, "x + 1", "identificador no encontrado: x")

    def test_variable_no_declarada_dentro_de_funcion(self):
        assert_runtime_error(self, "let f = function() { y }; f()", "identificador no encontrado: y")

    def test_llamar_a_funcion_inexistente(self):
        assert_runtime_error(self, "noexiste(1)", "identificador no encontrado: noexiste")

    def test_llamar_a_algo_que_no_es_funcion(self):
        assert_runtime_error(self, "let n = 5; n(1)", "no es una función")

    def test_tipos_incompatibles_en_suma(self):
        assert_runtime_error(self, '1 + "a"', "discrepancia de tipos")

    def test_operador_no_soportado_para_cadenas(self):
        assert_runtime_error(self, '"a" - "b"', "operador desconocido")

    def test_prefijo_menos_sobre_cadena(self):
        assert_runtime_error(self, '-"a"', "operador desconocido")

    def test_len_con_tipo_no_soportado(self):
        assert_runtime_error(self, "len(5)", "no soportado")

    def test_len_con_aridad_incorrecta(self):
        assert_runtime_error(self, "len()", "número incorrecto de argumentos")
        assert_runtime_error(self, "len([1], [2])", "número incorrecto de argumentos")

    def test_int_de_cadena_no_numerica(self):
        assert_runtime_error(self, 'int("abc")', "no se pudo convertir")

    def test_indexar_algo_que_no_es_arreglo(self):
        assert_runtime_error(self, "let n = 5; n[0]", "no soportado")

    def test_error_se_propaga_a_traves_de_funciones(self):
        assert_runtime_error(self, "let f = function() { 1 / 0 }; let g = function() { f() + 1 }; g()",
                             "división por cero")

    def test_error_detiene_el_programa(self):
        # La sentencia posterior al error no debe ejecutarse
        r = run("let a = [1]; a[0] = 1 / 0; a")
        self.assertEqual(r.type(), ObjType.ERROR)

    def test_indice_fuera_de_rango_en_mutacion(self):
        assert_runtime_error(self, "let a = [1, 2, 3]; a[3] = 0", "índice fuera de rango: 3")


class TestErroresSintacticos(unittest.TestCase):

    def errores(self, source):
        _, parser, lexer = parse(source)
        self.assertEqual(lexer.errors, [], "no debería ser un error léxico")
        return parser.errors

    def test_let_sin_valor(self):
        errs = self.errores("let x = ;")
        self.assertTrue(errs)
        self.assertIn("Línea 1, Columna 9", errs[0])

    def test_let_sin_nombre(self):
        errs = self.errores("let = 5")
        self.assertTrue(errs)
        self.assertIn("IDENT", errs[0])
        self.assertIn("Línea 1, Columna 5", errs[0])

    def test_let_sin_igual(self):
        errs = self.errores("let x 5")
        self.assertTrue(errs)
        self.assertIn("se esperaba que el siguiente token fuera =", errs[0])

    def test_expresion_incompleta(self):
        errs = self.errores("1 +")
        self.assertTrue(errs)
        self.assertIn("EOF", errs[0])

    def test_parentesis_sin_cerrar(self):
        errs = self.errores("(1 + 2")
        self.assertTrue(errs)
        self.assertIn("se esperaba que el siguiente token fuera )", errs[0])

    def test_if_sin_parentesis(self):
        errs = self.errores("if x { 1 }")
        self.assertTrue(errs)
        self.assertIn("se esperaba que el siguiente token fuera (", errs[0])

    def test_if_sin_llave(self):
        errs = self.errores("if (true) 1")
        self.assertTrue(errs)
        self.assertIn("se esperaba que el siguiente token fuera {", errs[0])

    def test_corchete_sin_cerrar(self):
        errs = self.errores("[1, 2")
        self.assertTrue(errs)

    def test_asignacion_a_valor_no_asignable(self):
        errs = self.errores("5 = 3")
        self.assertTrue(errs)
        self.assertIn("se esperaba un identificador o indexación", errs[0])
        self.assertIn("Línea 1, Columna 3", errs[0])

    def test_error_en_segunda_linea_reporta_la_linea_correcta(self):
        errs = self.errores("let a = 1\nlet b = ;")
        self.assertTrue(errs)
        self.assertIn("Línea 2", errs[0])

    def test_operador_binario_sin_operando_izquierdo(self):
        errs = self.errores("* 3")
        self.assertTrue(errs)
        self.assertIn("no se encontró prefijo", errs[0])

    def test_programa_valido_no_produce_errores(self):
        self.assertEqual(self.errores("let x = 1; if (x) { x } else { 0 }"), [])


class TestErroresLexicos(unittest.TestCase):

    def test_cadena_sin_cerrar_es_error_lexico(self):
        _, lexer = tokenize('"sin cerrar')
        self.assertEqual(len(lexer.errors), 1)
        self.assertIn("Línea 1, Columna 1", lexer.errors[0])

    def test_caracter_desconocido_genera_token_illegal_con_posicion(self):
        # El lexer marca el carácter como ILLEGAL (con línea/columna); el rechazo
        # del programa ocurre al llegar al parser, que lo reporta con esa posición.
        toks, _ = tokenize("let x = #")
        self.assertEqual(toks[-1].type, "ILLEGAL")
        self.assertEqual((toks[-1].line, toks[-1].column), (1, 9))
        _, parser, _ = parse("let x = #")
        self.assertTrue(parser.errors)
        self.assertIn("Línea 1, Columna 9", parser.errors[0])
        self.assertIn("ILLEGAL", parser.errors[0])


class TestErroresDesdeMain(unittest.TestCase):
    # Pruebas de extremo a extremo: código de salida y flujo (stdout/stderr) de main.py

    def ejecutar(self, source):
        with tempfile.NamedTemporaryFile("w", suffix=".src", delete=False, encoding="utf-8") as f:
            f.write(source)
            ruta = f.name
        try:
            return subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), ruta],
                                  capture_output=True, text=True, timeout=30)
        finally:
            os.unlink(ruta)

    def test_programa_correcto_sale_con_codigo_0(self):
        p = self.ejecutar('print("ok")')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "ok\n")

    def test_error_de_ejecucion_sale_con_1_y_va_a_stderr(self):
        p = self.ejecutar("1 / 0")
        self.assertEqual(p.returncode, 1)
        self.assertIn("ERROR: división por cero", p.stderr)

    def test_error_sintactico_sale_con_1_y_no_ejecuta_nada(self):
        p = self.ejecutar('print("no debe imprimirse")\nlet = 5')
        self.assertEqual(p.returncode, 1)
        self.assertIn("sintáctico", p.stderr)
        self.assertNotIn("no debe imprimirse", p.stdout)

    def test_error_lexico_sale_con_1(self):
        p = self.ejecutar('let s = "abc')
        self.assertEqual(p.returncode, 1)
        self.assertIn("léxico", p.stderr)

    def test_archivo_inexistente(self):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), "no_existe.src"],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 1)
        self.assertIn("no existe", p.stderr)


if __name__ == "__main__":
    unittest.main()
