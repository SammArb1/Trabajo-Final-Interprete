# PRUEBAS DEL EVALUADOR: aritmética, condicionales, ámbitos, bucles, recursión,
# arreglos (lectura y mutación por índice) y funciones integradas.

import unittest
from helpers import run
from objects import ObjType


def val(source):
    # Resultado como texto (inspect) para comparar fácilmente
    return run(source).inspect()


class TestAritmetica(unittest.TestCase):

    def test_operaciones_basicas(self):
        self.assertEqual(val("1 + 2"), "3")
        self.assertEqual(val("10 - 4"), "6")
        self.assertEqual(val("6 * 7"), "42")

    def test_precedencia_en_ejecucion(self):
        self.assertEqual(val("1 + 2 * 3"), "7")
        self.assertEqual(val("(1 + 2) * 3"), "9")

    def test_asociatividad_en_ejecucion(self):
        self.assertEqual(val("10 - 4 - 3"), "3")      # (10-4)-3, no 10-(4-3)
        self.assertEqual(val("2 ** 3 ** 2"), "512")   # 2**(3**2), no (2**3)**2
        self.assertEqual(val("100 / 10 / 2"), "5.0")

    def test_division_siempre_produce_flotante(self):
        r = run("7 / 2")
        self.assertEqual(r.type(), ObjType.FLOAT)
        self.assertEqual(r.value, 3.5)

    def test_coercion_entero_flotante(self):
        r = run("1 + 0.5")
        self.assertEqual((r.type(), r.value), (ObjType.FLOAT, 1.5))

    def test_prefijo_menos(self):
        self.assertEqual(val("-5 + 2"), "-3")

    def test_comparaciones(self):
        self.assertEqual(val("1 < 2"), "true")
        self.assertEqual(val("2 <= 2"), "true")
        self.assertEqual(val("3 > 4"), "false")
        self.assertEqual(val("1 == 1.0"), "true")
        self.assertEqual(val("1 != 2"), "true")

    def test_logicos_y_negacion(self):
        self.assertEqual(val("true and false"), "false")
        self.assertEqual(val("false or true"), "true")
        self.assertEqual(val("!true"), "false")
        self.assertEqual(val("!0"), "true")

    def test_cortocircuito(self):
        # Si no hubiera cortocircuito, 1/0 produciría un error
        self.assertEqual(val("false and (1 / 0)"), "false")
        self.assertEqual(val("true or (1 / 0)"), "true")

    def test_concatenacion_de_cadenas(self):
        self.assertEqual(val('"ho" + "la"'), "hola")


class TestVariablesYCondicionales(unittest.TestCase):

    def test_let_y_reasignacion(self):
        self.assertEqual(val("let x = 1; x = x + 4; x"), "5")

    def test_if_rama_verdadera_y_falsa(self):
        self.assertEqual(val("if (1 < 2) { 10 } else { 20 }"), "10")
        self.assertEqual(val("if (1 > 2) { 10 } else { 20 }"), "20")

    def test_if_sin_else_devuelve_null(self):
        self.assertEqual(val("if (false) { 1 }"), "null")

    def test_elif(self):
        src = "let f = function(n) { if (n < 0) { return \"neg\" } elif (n == 0) { return \"cero\" } else { return \"pos\" } };"
        self.assertEqual(val(src + "f(-1)"), "neg")
        self.assertEqual(val(src + "f(0)"), "cero")
        self.assertEqual(val(src + "f(5)"), "pos")

    def test_condicionales_anidados(self):
        src = """
        let g = function(a, b) {
            if (a) { if (b) { return 1 } else { return 2 } } else { return 3 }
        };
        """
        self.assertEqual(val(src + "g(true, true)"), "1")
        self.assertEqual(val(src + "g(true, false)"), "2")
        self.assertEqual(val(src + "g(false, true)"), "3")

    def test_valores_de_verdad(self):
        # 0, "", [] y null son falsy; el resto es truthy
        self.assertEqual(val("if (0) { 1 } else { 2 }"), "2")
        self.assertEqual(val('if ("") { 1 } else { 2 }'), "2")
        self.assertEqual(val("if ([]) { 1 } else { 2 }"), "2")
        self.assertEqual(val("if ([0]) { 1 } else { 2 }"), "1")


class TestAmbitos(unittest.TestCase):

    def test_shadowing_en_bloque_no_modifica_la_externa(self):
        self.assertEqual(val("let x = 1; if (true) { let x = 2 }; x"), "1")

    def test_shadowing_dentro_del_bloque_ve_la_interna(self):
        self.assertEqual(val("let x = 1; if (true) { let x = 2; x } else { 0 }"), "2")

    def test_asignacion_sin_let_modifica_la_externa(self):
        self.assertEqual(val("let x = 1; if (true) { x = 9 }; x"), "9")

    def test_parametro_tapa_variable_global(self):
        src = "let x = 100; let f = function(x) { x + 1 }; "
        self.assertEqual(val(src + "f(1)"), "2")
        self.assertEqual(val(src + "f(1); x"), "100")

    def test_variable_local_de_funcion_no_escapa(self):
        r = run("let f = function() { let local = 5; local }; f(); local")
        self.assertEqual(r.type(), ObjType.ERROR)
        self.assertIn("identificador no encontrado: local", r.message)

    def test_funcion_lee_variable_global(self):
        self.assertEqual(val("let g = 7; let f = function() { g * 2 }; f()"), "14")

    def test_scopes_anidados_de_tres_niveles(self):
        src = """
        let x = "global";
        let f = function() {
            let x = "f";
            let h = function() {
                let x = "h";
                x
            };
            h() + "-" + x
        };
        f() + "-" + x
        """
        self.assertEqual(val(src), "h-f-global")

    def test_variable_del_for_no_escapa(self):
        r = run("for (let i = 0; i < 2; i = i + 1) { i }; i")
        self.assertEqual(r.type(), ObjType.ERROR)

    def test_cierre_conserva_estado(self):
        src = """
        let crear = function() { let c = 0; return function() { c = c + 1; return c } };
        let k = crear(); k(); k(); k()
        """
        self.assertEqual(val(src), "3")


class TestBucles(unittest.TestCase):

    def test_while(self):
        self.assertEqual(val("let i = 0; let s = 0; while (i < 5) { s = s + i; i = i + 1 }; s"), "10")

    def test_while_que_nunca_entra(self):
        self.assertEqual(val("let i = 10; while (i < 5) { i = 0 }; i"), "10")

    def test_while_con_break(self):
        self.assertEqual(val("let i = 0; while (true) { if (i == 3) { break }; i = i + 1 }; i"), "3")

    def test_for_clasico(self):
        self.assertEqual(val("let s = 0; for (let i = 1; i <= 4; i = i + 1) { s = s + i }; s"), "10")

    def test_for_con_break(self):
        src = "let r = 0; for (let i = 0; i < 100; i = i + 1) { if (i == 7) { r = i; break } }; r"
        self.assertEqual(val(src), "7")

    def test_break_solo_corta_el_bucle_interno(self):
        src = """
        let cuenta = 0;
        for (let i = 0; i < 3; i = i + 1) {
            for (let j = 0; j < 10; j = j + 1) {
                if (j == 2) { break }
                cuenta = cuenta + 1
            }
        };
        cuenta
        """
        self.assertEqual(val(src), "6")

    def test_return_dentro_de_while_sale_de_la_funcion(self):
        src = "let f = function() { let i = 0; while (true) { if (i == 4) { return i }; i = i + 1 } }; f()"
        self.assertEqual(val(src), "4")


class TestFuncionesYRecursion(unittest.TestCase):

    def test_llamada_con_parametros(self):
        self.assertEqual(val("let suma = function(a, b) { a + b }; suma(3, 4)"), "7")

    def test_return_explicito_corta_la_ejecucion(self):
        self.assertEqual(val("let f = function() { return 1; 2 }; f()"), "1")

    def test_funcion_sin_return_devuelve_ultimo_valor(self):
        self.assertEqual(val("let f = function(x) { x * 2 }; f(21)"), "42")

    def test_factorial_recursivo(self):
        src = "let fact = function(n) { if (n <= 1) { return 1 }; return n * fact(n - 1) }; "
        self.assertEqual(val(src + "fact(5)"), "120")
        self.assertEqual(val(src + "fact(10)"), "3628800")

    def test_fibonacci_recursivo(self):
        src = "let fib = function(n) { if (n < 2) { return n }; return fib(n - 1) + fib(n - 2) }; "
        self.assertEqual(val(src + "fib(0)"), "0")
        self.assertEqual(val(src + "fib(1)"), "1")
        self.assertEqual(val(src + "fib(10)"), "55")

    def test_funcion_como_argumento(self):
        src = "let aplicar = function(f, x) { f(x) }; aplicar(function(n) { n * n }, 6)"
        self.assertEqual(val(src), "36")

    def test_funcion_que_devuelve_funcion(self):
        src = "let sumador = function(a) { function(b) { a + b } }; sumador(3)(4)"
        self.assertEqual(val(src), "7")


class TestArreglos(unittest.TestCase):

    def test_literal_e_indexacion(self):
        self.assertEqual(val("[1, 2, 3]"), "[1, 2, 3]")
        self.assertEqual(val("[10, 20, 30][1]"), "20")

    def test_arreglo_con_tipos_mixtos(self):
        self.assertEqual(val('[1, "dos", true]'), "[1, dos, true]")

    def test_lectura_fuera_de_rango_devuelve_null(self):
        self.assertEqual(val("[1, 2][5]"), "null")

    def test_mutacion_por_indice(self):
        self.assertEqual(val("let a = [1, 2, 3]; a[1] = 99; a"), "[1, 99, 3]")

    def test_mutacion_devuelve_el_valor_asignado(self):
        self.assertEqual(val("let a = [1, 2]; a[0] = 7"), "7")

    def test_mutacion_con_indice_calculado(self):
        self.assertEqual(val("let a = [1, 2, 3]; a[len(a) - 1] = 0; a"), "[1, 2, 0]")

    def test_mutacion_en_ciclo(self):
        src = "let a = [1, 2, 3]; for (let i = 0; i < len(a); i = i + 1) { a[i] = a[i] * 10 }; a"
        self.assertEqual(val(src), "[10, 20, 30]")

    def test_mutacion_visible_a_traves_de_alias(self):
        self.assertEqual(val("let a = [1, 2]; let b = a; b[0] = 7; a"), "[7, 2]")

    def test_mutacion_dentro_de_funcion_afecta_al_original(self):
        src = "let f = function(arr) { arr[0] = 100 }; let a = [1, 2]; f(a); a"
        self.assertEqual(val(src), "[100, 2]")

    def test_mutacion_conserva_el_tipo_de_otros_elementos(self):
        self.assertEqual(val('let a = [1, "x"]; a[0] = "y"; a'), "[y, x]")

    def test_mutacion_indice_en_el_limite_superior_es_error(self):
        r = run("let a = [1, 2]; a[2] = 0")
        self.assertEqual(r.type(), ObjType.ERROR)
        self.assertIn("índice fuera de rango: 2", r.message)
        self.assertIn("longitud 2", r.message)

    def test_mutacion_indice_negativo_es_error(self):
        r = run("let a = [1, 2]; a[-1] = 0")
        self.assertEqual(r.type(), ObjType.ERROR)
        self.assertIn("índice fuera de rango: -1", r.message)

    def test_mutacion_en_arreglo_vacio_es_error(self):
        r = run("let a = []; a[0] = 1")
        self.assertEqual(r.type(), ObjType.ERROR)

    def test_error_de_mutacion_no_modifica_el_arreglo(self):
        r = run("let a = [1, 2]; a[9] = 0; a")
        # el error detiene el programa: el resultado final es el Error
        self.assertEqual(r.type(), ObjType.ERROR)

    def test_mutacion_con_indice_no_entero_es_error(self):
        r = run('let a = [1, 2]; a["x"] = 0')
        self.assertEqual(r.type(), ObjType.ERROR)
        self.assertIn("el índice debe ser un entero", r.message)

    def test_mutacion_sobre_no_arreglo_es_error(self):
        r = run("let n = 5; n[0] = 1")
        self.assertEqual(r.type(), ObjType.ERROR)
        self.assertIn("no soportada", r.message)


class TestBuiltins(unittest.TestCase):

    def test_len(self):
        self.assertEqual(val("len([1, 2, 3])"), "3")
        self.assertEqual(val('len("hola")'), "4")
        self.assertEqual(val("len([])"), "0")

    def test_print_devuelve_null_e_imprime(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            r = run('print("a", 1, true)')
        self.assertEqual(r.inspect(), "null")
        self.assertEqual(buf.getvalue(), "a 1 true\n")

    def test_int(self):
        self.assertEqual(val('int("42")'), "42")
        self.assertEqual(val("int(3.9)"), "3")
        self.assertEqual(val("int(true)"), "1")

    def test_float(self):
        self.assertEqual(val("float(3)"), "3.0")
        self.assertEqual(val('float("2.5")'), "2.5")

    def test_str_y_bool(self):
        self.assertEqual(val("str(123) + \"!\""), "123!")
        self.assertEqual(val("bool(0)"), "false")
        self.assertEqual(val("bool([1])"), "true")

    def test_type(self):
        self.assertEqual(val("type(1)"), "INTEGER")
        self.assertEqual(val("type(1.5)"), "FLOAT")
        self.assertEqual(val('type("a")'), "STRING")
        self.assertEqual(val("type([1])"), "ARRAY")
        self.assertEqual(val("type(true)"), "BOOLEAN")


if __name__ == "__main__":
    unittest.main()
