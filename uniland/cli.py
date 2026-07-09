#!/usr/bin/env python3
import sys
import argparse
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter
from .errors import UniLandError
from . import builtins as _builtins
from . import __version__


def _force_utf8():
    # UniLand source is UTF-8; make sure non-ASCII text prints correctly even
    # on terminals that default to a legacy code page (e.g. Windows).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def run_source(source, debug=False, script_args=None):
    _builtins.set_argv(script_args or [])
    tokens = Lexer(source).tokenize()
    if debug:
        print("Tokens:")
        for tok in tokens:
            print(" ", tok)
    program = Parser(tokens).parse()
    Interpreter().interpret(program)


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: file '{path}' not found.", file=sys.stderr)
        sys.exit(1)


def run_file(path, debug=False, script_args=None):
    run_source(_read(path), debug=debug, script_args=script_args)


def eval_code(code):
    """Выполнить одну строку кода (как `python -c`)."""
    run_source(code)


def check_file(path):
    """Проверить синтаксис без запуска."""
    source = _read(path)
    Parser(Lexer(source).tokenize()).parse()
    print(f"OK: {path} — синтаксис в порядке")


def _balanced(src):
    """Грубая проверка: закрыты ли все скобки (для многострочного ввода в REPL)."""
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    in_str = None
    prev = ''
    for ch in src:
        if in_str:
            if ch == in_str and prev != '\\':
                in_str = None
        elif ch in ('"', '`', "'"):
            in_str = ch
        elif ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if stack and stack[-1] == pairs[ch]:
                stack.pop()
        prev = ch
    return not stack and in_str is None


def repl():
    """Интерактивный режим (REPL): вводишь код — сразу видишь результат."""
    from .ast_nodes import ExpressionStatement
    _force_utf8()
    _builtins.set_argv([])
    interp = Interpreter()
    print(f"UniLand {__version__} — интерактивный режим.")
    print("Введи код и Enter. Выход: exit, quit или Ctrl+D.")
    buffer = ""
    while True:
        try:
            line = input("... " if buffer else "uni> ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("^C")
            buffer = ""
            continue
        if not buffer and line.strip() in ("exit", "exit()", "quit", "quit()"):
            break
        buffer = (buffer + "\n" + line) if buffer else line
        if buffer.strip() and not _balanced(buffer):
            continue  # ждём закрывающую скобку / кавычку — многострочный ввод
        source, buffer = buffer, ""
        if not source.strip():
            continue
        try:
            program = Parser(Lexer(source).tokenize()).parse()
            for stmt in program.statements:
                if isinstance(stmt, ExpressionStatement):
                    value = interp.evaluate(stmt.expr)
                    if value is not None:
                        print(_builtins.uland_str(value))
                else:
                    interp.execute(stmt)
        except UniLandError as e:
            print(f"UniLand error: {e}", file=sys.stderr)
        except SystemExit:
            break
        except KeyboardInterrupt:
            print("^C")


def main():
    _force_utf8()
    parser = argparse.ArgumentParser(
        prog="uniland",
        description="UniLand — лёгкий дружелюбный язык сценариев",
        epilog="Примеры:  uniland run script.uni   |   uniland -e 'print(2+2)'   |   uniland -i",
    )
    parser.add_argument("-v", "--version", action="version", version=f"UniLand {__version__}")
    parser.add_argument("-e", "--eval", metavar="CODE", help="выполнить код одной строкой и выйти")
    parser.add_argument("-i", "--interactive", action="store_true", help="запустить интерактивный режим (REPL)")
    parser.add_argument("-c", "--check", metavar="FILE", help="проверить синтаксис файла без запуска")

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="запустить .uni скрипт")
    run_p.add_argument("file", help="путь к .uni файлу")
    run_p.add_argument("-d", "--debug", action="store_true", help="показать токены перед запуском")
    run_p.add_argument("script_args", nargs=argparse.REMAINDER,
                       help="аргументы для скрипта (читаются через argv())")

    ev_p = sub.add_parser("eval", help="выполнить код одной строкой")
    ev_p.add_argument("code", help="код UniLand")

    sub.add_parser("repl", help="интерактивный режим (REPL)")

    ck_p = sub.add_parser("check", help="проверить синтаксис без запуска")
    ck_p.add_argument("file", help="путь к .uni файлу")

    args = parser.parse_args()

    try:
        # короткие флаги имеют приоритет
        if args.check:
            check_file(args.check)
        elif args.eval:
            eval_code(args.eval)
        elif args.interactive:
            repl()
        elif args.command == "run":
            run_file(args.file, debug=args.debug, script_args=args.script_args)
        elif args.command == "eval":
            eval_code(args.code)
        elif args.command == "check":
            check_file(args.file)
        elif args.command == "repl":
            repl()
        else:
            # без аргументов — дружелюбно открываем REPL
            repl()
    except UniLandError as e:
        print(f"UniLand error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
