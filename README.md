# Intérprete — Trabajo final de Lenguajes y Compiladores

Intérprete de un lenguaje de scripting imperativo con sintaxis tipo JavaScript/Monkey,
escrito en **Python 3**. Procesa el programa en cuatro etapas:

```
Código fuente → Lexer → Parser → Evaluador (+ Environment) → Resultado / Error
   (texto)      tokens    AST      recorre el AST              salida
```

Universidad EIA · Compiladores · Entrega: 4 de noviembre de 2026 · Sustentación: 5 de noviembre de 2026

## Integrantes

| Integrante | Responsabilidad |
|---|---|
| Samuel Arbelaez (`SammArb1`) | Evaluador, sistema de tipos y CLI |
| Nicolás Aguas | Frontend del lenguaje (lexer, parser y sintaxis) |
| Jerónimo Aristizabal | Colecciones (mutación por índice), suite de pruebas, ejemplos y documentación |


## Requisitos

- Python 3.10 o superior (probado con 3.12). No requiere dependencias externas.
- `pytest` es opcional (solo si se prefiere ese ejecutor de pruebas).

## Instalación

```bash
git clone https://github.com/SammArb1/Trabajo-Final-Interprete.git
cd Trabajo-Final-Interprete
```

No hay paso de compilación: el intérprete se ejecuta directamente con `python`.

## Cómo ejecutar

Se implementan **ambas** modalidades de entrada.

### REPL (consola interactiva)

```bash
python main.py
```

```
>> let x = 2
>> x * 3
6
>> let a = [1, 2]
>> a[1] = 5
>> a
[1, 5]
>> exit
```

El entorno persiste entre líneas. Cada línea se analiza completa (el REPL no admite
bloques de varias líneas; para eso use un archivo). Se sale con `exit`, Ctrl+C o Ctrl+D.

### Archivo

```bash
python main.py examples/04_recursividad_fibonacci.src
```

Códigos de salida: `0` éxito · `1` error léxico, sintáctico o de ejecución (el mensaje
va a `stderr`, con línea y columna cuando es un error léxico o sintáctico). Si el
último valor del programa no es `null`, se imprime al terminar.

## Cómo correr las pruebas

Un solo comando, desde la raíz del repositorio:

```bash
python -m unittest discover tests
```

Alternativa con pytest: `pytest tests`.

| Archivo | Qué verifica |
|---|---|
| `tests/test_lexer.py` | Tokens válidos, palabras reservadas, línea/columna, caracteres ilegales y cadenas sin cerrar |
| `tests/test_parser.py` | Precedencia, asociatividad y forma exacta del AST (serializado como S-expression) |
| `tests/test_evaluator.py` | Aritmética, condicionales, ámbitos y *shadowing*, bucles, recursión, closures, arreglos, mutación por índice y built-ins |
| `tests/test_errors.py` | División por cero, variable no declarada, errores de sintaxis y de tipos, y códigos de salida de `main.py` |
| `tests/test_examples.py` | Cada programa de `examples/` produce exactamente la salida de `tests/expected/*.out` |

## Resumen del lenguaje

```
let x = 10                      // declaración (el ';' es opcional)
x = x + 1                       // reasignación
let a = [1, 2, 3]              // arreglo
a[0] = 99                       // mutación por índice
let f = function(n) { return n * 2 }
if (x > 5) { ... } elif (x > 2) { ... } else { ... }
while (cond) { ... }
for (let i = 0; i < 10; i = i + 1) { ... }   // break; sale del bucle
x > 1 and y < 2 or !z           // también && y ||, con cortocircuito
```

- **Tipos:** entero, flotante, cadena, booleano, `null`, arreglo, función.
- **Operadores:** `+ - * / **`, `< > <= >= == !=`, `and or !` (`&&`, `||`).
- **Built-ins:** `print`, `len`, `int`, `float`, `str`, `bool`, `type`.
- **Valores falsy:** `false`, `null`, `0`, `0.0`, `""` y `[]`.

## Programas de ejemplo (`examples/`)

| Archivo | Demuestra |
|---|---|
| `01_variables_operaciones.src` | Variables, reasignación, precedencia, asociatividad, flotantes y cadenas |
| `02_condicionales_anidados.src` | `if / elif / else` anidados, cortocircuito y *shadowing* |
| `03_ciclos_y_break.src` | `while`, `for` y `break` |
| `04_recursividad_fibonacci.src` | Funciones, retorno, recursión (Fibonacci, factorial) y closures |
| `05_arreglos_builtins.src` | Arreglos, mutación por índice, paso por referencia y built-ins |

> El lexer actual no admite comentarios, por eso los `.src` no los incluyen; la
> descripción de cada ejemplo está en esta tabla.

## Estructura del repositorio

```
tokens.py        Tipos de token, palabras reservadas, clase Token
lexer.py         Analizador léxico (texto → tokens con línea/columna)
ast_nodes.py     Nodos del AST
parser.py        Parser Pratt (tokens → AST, precedencia y asociatividad)
objects.py       Sistema de objetos del runtime (Integer, ArrayObj, Error, ...)
environment.py   Entornos anidados (ámbitos)
evaluator.py     Evaluador tree-walking + funciones integradas
repl.py          Bucle interactivo
main.py          Punto de entrada (REPL o archivo)
examples/        Programas de demostración
tests/           Suite de pruebas automáticas
diseno.md        Documento de diseño (gramática, arquitectura, decisiones, uso de IA)
```
