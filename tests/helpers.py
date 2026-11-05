# UTILIDADES COMPARTIDAS POR LA SUITE DE PRUEBAS
# Permite importar los módulos del intérprete (que viven en la raíz del repo)
# sin importar desde dónde se lance unittest/pytest.

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lexer import Lexer
from parser import Parser
from environment import Environment
from evaluator import evaluate
from tokens import EOF
import ast_nodes as ast


def tokenize(source):
    # Devuelve (lista de tokens sin EOF, lexer) para poder inspeccionar lexer.errors
    lexer = Lexer(source)
    tokens = []
    while True:
        tok = lexer.next_token()
        if tok.type == EOF:
            break
        tokens.append(tok)
    return tokens, lexer


def parse(source):
    # Devuelve (programa, parser, lexer)
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()
    return program, parser, lexer


def run(source):
    # Ejecuta el programa completo en un entorno nuevo y devuelve el objeto resultado.
    # Falla la prueba si hubo errores léxicos/sintácticos (para eso está test_errors).
    program, parser, lexer = parse(source)
    assert not lexer.errors, f"errores léxicos inesperados: {lexer.errors}"
    assert not parser.errors, f"errores sintácticos inesperados: {parser.errors}"
    return evaluate(program, Environment())


def sexp(node):
    # Serializa el AST como S-expression para comparar la estructura de forma legible.
    # Ejemplo: 1 + 2 * 3  ->  (+ 1 (* 2 3))
    if isinstance(node, ast.Program):
        return " ; ".join(sexp(s) for s in node.statements)
    if isinstance(node, ast.ExpressionStatement):
        return sexp(node.expression)
    if isinstance(node, ast.LetStatement):
        return f"(let {node.name.value} {sexp(node.value)})"
    if isinstance(node, ast.ReturnStatement):
        return f"(return {sexp(node.return_value)})"
    if isinstance(node, ast.BreakStatement):
        return "(break)"
    if isinstance(node, ast.BlockStatement):
        return "{" + " ".join(sexp(s) for s in node.statements) + "}"
    if isinstance(node, (ast.IntegerLiteral, ast.FloatLiteral)):
        return str(node.value)
    if isinstance(node, ast.StringLiteral):
        return repr(node.value)
    if isinstance(node, ast.Boolean):
        return "true" if node.value else "false"
    if isinstance(node, ast.Identifier):
        return node.value
    if isinstance(node, ast.PrefixExpression):
        return f"({node.operator} {sexp(node.right)})"
    if isinstance(node, ast.InfixExpression):
        return f"({node.operator} {sexp(node.left)} {sexp(node.right)})"
    if isinstance(node, ast.AssignExpression):
        return f"(= {sexp(node.name)} {sexp(node.value)})"
    if isinstance(node, ast.IndexExpression):
        return f"(index {sexp(node.left)} {sexp(node.index)})"
    if isinstance(node, ast.ArrayLiteral):
        return "[" + " ".join(sexp(e) for e in node.elements) + "]"
    if isinstance(node, ast.CallExpression):
        args = " ".join(sexp(a) for a in node.arguments)
        return f"(call {sexp(node.function)}{' ' + args if args else ''})"
    if isinstance(node, ast.FunctionLiteral):
        params = ",".join(p.value for p in node.parameters)
        return f"(fn ({params}) {sexp(node.body)})"
    if isinstance(node, ast.IfExpression):
        out = f"(if {sexp(node.condition)} {sexp(node.consequence)}"
        for cond, block in node.elifs:
            out += f" elif {sexp(cond)} {sexp(block)}"
        if node.alternative is not None:
            out += f" else {sexp(node.alternative)}"
        return out + ")"
    if isinstance(node, ast.WhileExpression):
        return f"(while {sexp(node.condition)} {sexp(node.body)})"
    if isinstance(node, ast.ForExpression):
        return (f"(for {sexp(node.init)} {sexp(node.condition)} "
                f"{sexp(node.update)} {sexp(node.body)})")
    return f"<{type(node).__name__}>"
