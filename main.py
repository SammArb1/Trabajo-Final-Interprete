# PUNTO DE ENTRADA DEL INTÉRPRETE
# Modos: REPL interactivo (sin args) o ejecución de archivo (1 arg).
# Códigos de salida: 0 → éxito, 1 → error (léxico, sintáctico o de runtime).

import sys
import os

# Garantiza que los módulos del intérprete sean localizables sin importar el CWD
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from lexer import Lexer
from parser import Parser
from environment import Environment
from evaluator import evaluate
from repl import start_repl
from objects import ObjType

def run_file(file_path):
    # Verifica existencia antes de abrir para dar un mensaje de error claro
    if not os.path.isfile(file_path):
        print(f"Error: el archivo '{file_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error al leer el archivo '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

    lexer   = Lexer(source_code)
    parser  = Parser(lexer)
    program = parser.parse_program()

    # Fase 1: errores léxicos — aborta antes de continuar al parser
    if lexer.errors:
        print(f"Se encontraron {len(lexer.errors)} error(es) léxico(s):", file=sys.stderr)
        for err in lexer.errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    # Fase 2: errores sintácticos — aborta antes de evaluar
    if parser.errors:
        print(f"Se encontraron {len(parser.errors)} error(es) sintáctico(s):", file=sys.stderr)
        for err in parser.errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    result = evaluate(program, Environment())

    # Fase 3: errores de runtime — reporta en stderr y termina con código 1
    if result is not None and result.type() == ObjType.ERROR:
        print(result.inspect(), file=sys.stderr)
        sys.exit(1)

    # Éxito: imprime el último valor si no es Null (útil en modo script)
    if result is not None and result.type() != ObjType.NULL:
        print(result.inspect())

    sys.exit(0)   # salida limpia

def main():
    if len(sys.argv) == 1:
        start_repl()
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        print("Uso: python main.py [ruta_archivo]", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
