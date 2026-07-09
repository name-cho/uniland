__version__ = "2.2.0"

from .errors import UniLandError
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter


def run(source, debug=False):
    """Run UniLand source code from a string."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    Interpreter().interpret(program)
