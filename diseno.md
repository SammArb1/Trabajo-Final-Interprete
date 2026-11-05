# Documento de diseño — Intérprete

Universidad EIA · Compiladores · Equipo:

Samuel Arbelaez
Jeronimo Aristizabal 
Nicolas Aguas

## 1. Gramática (EBNF)

Notación: `{ x }` cero o más, `[ x ]` opcional, `|` alternativa. Los terminales en
minúscula entre comillas son palabras reservadas; `IDENT`, `INT`, `FLOAT` y `STRING` son tokens del lexer.

```ebnf
program        = { statement } ;
statement      = letStmt | returnStmt | breakStmt | exprStmt ;
letStmt        = "let" IDENT "=" expression [ ";" ] ;
returnStmt     = "return" expression [ ";" ] ;
breakStmt      = "break" [ ";" ] ;
exprStmt       = expression [ ";" ] ;
block          = "{" { statement } "}" ;

expression     = assignment ;
assignment     = logicOr [ "=" assignment ] ;          (* destino: IDENT o indexación; asoc. derecha *)
logicOr        = logicAnd { ( "or" | "||" ) logicAnd } ;
logicAnd       = equality { ( "and" | "&&" ) equality } ;
equality       = comparison { ( "==" | "!=" ) comparison } ;
comparison     = sum { ( "<" | ">" | "<=" | ">=" ) sum } ;
sum            = product { ( "+" | "-" ) product } ;
product        = power { ( "*" | "/" ) power } ;
power          = unary [ "**" power ] ;                  (* asociatividad a la derecha *)
unary          = ( "!" | "-" ) unary | postfix ;
postfix        = primary { "(" [ args ] ")" | "[" expression "]" } ;
args           = expression { "," expression } ;

primary        = IDENT | INT | FLOAT | STRING | "true" | "false"
               | "(" expression ")" | arrayLit | funcLit | ifExpr | whileExpr | forExpr ;
arrayLit       = "[" [ args ] "]" ;
funcLit        = "function" "(" [ IDENT { "," IDENT } ] ")" block ;
ifExpr         = "if" "(" expression ")" block { "elif" "(" expression ")" block } [ "else" block ] ;
whileExpr      = "while" "(" expression ")" block ;
forExpr        = "for" "(" [ statement ] ";" [ expression ] ";" [ expression ] ")" block ;
```

**Precedencia** (de menor a mayor, tabla `PRECEDENCES` en `parser.py`): asignación (2) <
`or` (3) < `and` (4) < `== !=` (5) < `< > <= >=` (6) < `+ -` (7) < `* /` (8) < `**` (9) <
prefijo `! -` (10) < llamada (11) < índice (12).

## 2. Arquitectura

```
 texto ──► Lexer ──tokens──► Parser ──AST──► Evaluador ──► objeto resultado
            │                  │               │  ▲
       lexer.errors       parser.errors        ▼  │
                                          Environment (cadena de ámbitos)
```

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Lexer | `lexer.py` | Lee carácter a carácter, produce `Token(tipo, literal, línea, columna)`. Registra cadenas sin cerrar en `errors` y marca caracteres desconocidos como `ILLEGAL`. |
| Parser | `parser.py` | Parser Pratt (precedence climbing). Cada token tiene función prefija y/o infija; la precedencia decide cuándo detener la expresión. Acumula errores con posición en `errors`. |
| AST | `ast_nodes.py` | Un nodo por construcción (`LetStatement`, `InfixExpression`, `IfExpression`, `IndexExpression`, ...). |
| Evaluador | `evaluator.py` | `evaluate(node, env)` despacha por tipo de nodo (tree-walking). Contiene las funciones integradas. |
| Environment | `environment.py` | Diccionario por ámbito + referencia al ámbito padre (`outer`). `set` define en el ámbito local; `assign` busca hacia arriba la variable existente. |
| Objetos | `objects.py` | Valores del runtime (`Integer`, `Float`, `StringObj`, `BooleanVal`, `Null`, `ArrayObj`, `FunctionObj`, `Builtin`) y señales internas (`ReturnValue`, `BreakValue`, `Error`). |
| Punto de entrada | `main.py`, `repl.py` | Ejecuta archivo o REPL; revisa errores léxicos y sintácticos **antes** de evaluar. |

**Dónde se detecta cada error:** léxico (cadena sin cerrar) → lexer; estructura inválida →
parser (mensaje con `Línea L, Columna C`); división por cero, variable no declarada, tipos
incompatibles, índice fuera de rango → evaluador.

## 3. Decisiones de diseño

1. **Parser Pratt en lugar de descenso recursivo por niveles.** Agregar un operador es una
   entrada en la tabla de precedencias más una función; la asociatividad a la derecha de
   `**` se logra parseando el lado derecho con `precedence - 1`.
2. **Errores de ejecución como valores, no excepciones.** `Error` es un objeto que se propaga
   hacia arriba (`is_error`); el proceso Python nunca se cae por un error del programa
   interpretado, y `main.py` lo traduce a código de salida 1.
3. **Ámbitos léxicos con entornos encadenados.** Cada bloque `{}` y cada llamada crea un
   `Environment` hijo; `let` hace *shadowing* local y la asignación sin `let` modifica la
   variable del ámbito donde se declaró. `FunctionObj` captura su entorno, lo que da closures.
4. **Señales de control como objetos** (`ReturnValue`, `BreakValue`) que suben por los bloques
   hasta la función o el bucle que los consume, sin usar excepciones.
5. **Mutación de arreglos por índice** (`arr[i] = x`): se evalúa el arreglo, el índice y el
   valor; se valida tipo del índice y rango (`0 ≤ i < len`) y se modifica `elements` en
   sitio. Fuera de rango devuelve un `Error` («índice fuera de rango: i (longitud n)»). Los
   arreglos tienen semántica de referencia: la mutación es visible a través de alias y
   dentro de funciones. La *lectura* fuera de rango devuelve `null` (convención Python-like).
6. **Cortocircuito en `and` / `or`**, interceptado antes de evaluar el operando derecho.
7. **Aritmética:** `/` siempre produce flotante; entero con flotante se promueve a flotante.
8. **Pruebas:** el AST se serializa como S-expression para comparar su estructura sin
   depender de la identidad de los objetos; los ejemplos se validan contra salidas esperadas.

## 4. Limitaciones conocidas

- No hay comentarios en el lexer ni identificadores con tildes/ñ (`ILLEGAL`).
- Un carácter desconocido (`@`, `#`) se reporta en la etapa del parser, no en `lexer.errors`.
- No hay diccionarios (la mutación se implementó solo para arreglos).
- El REPL no soporta bloques de varias líneas.
- No se valida la aridad de funciones definidas por el usuario (un parámetro faltante
  queda sin enlazar y falla al usarse con «identificador no encontrado»).
- `2 ** -1` con enteros devuelve `0.5` pero con tipo `INTEGER`.
- Asignar a una variable inexistente la crea en el ámbito actual (sin error).

## 5. Uso de herramientas de IA

| Tarea | Herramienta | Cómo se verificó |
|---|---|---|
| Redacción inicial de la suite de pruebas (`tests/`), los 5 programas de `examples/`, README y este documento | Claude (Anthropic) | Se leyó el código fuente completo antes de escribir cada prueba; se ejecutaron las 158 pruebas y los 5 ejemplos; las salidas esperadas se revisaron a mano; se hicieron pruebas de mutación (alterar a propósito la asociatividad de `**`, el rango en la mutación, el *shadowing*, el cortocircuito y la columna del lexer) y se confirmó que la suite falla en cada caso. |
| Mensaje de error de índice fuera de rango (`evaluator.py`) | Claude (Anthropic) | Cubierto por `test_evaluator.py` y `test_errors.py`. |

Todo el equipo debe poder explicar y modificar cualquier parte del código, independientemente de quién o qué lo escribió.
