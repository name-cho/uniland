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


def main():
    parser = argparse.ArgumentParser(prog="uniland", description="UniLand interpreter")
    parser.add_argument("--version", action="version", version=f"UniLand {__version__}")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a .uni script")
    run_p.add_argument("file", help="Path to the .uni file")
    run_p.add_argument("--debug", action="store_true", help="Print tokens before running")
    run_p.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments passed to the script (read with argv())")

    _force_utf8()
    args = parser.parse_args()

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        run_source(source, debug=args.debug, script_args=args.script_args)
    except UniLandError as e:
        print(f"UniLand error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
