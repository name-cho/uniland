class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class VariableDeclaration(ASTNode):
    def __init__(self, name, value, is_const=False, line=None):
        self.name = name
        self.value = value
        self.is_const = is_const
        self.line = line

class FunctionDeclaration(ASTNode):
    def __init__(self, name, params, body, line=None):
        self.name = name
        self.params = params
        self.body = body
        self.line = line

class FunctionExpression(ASTNode):
    """A lambda / anonymous function value, e.g. (x) => x + 1."""
    def __init__(self, params, body, line=None):
        self.params = params
        self.body = body
        self.line = line

class ReturnStatement(ASTNode):
    def __init__(self, value, line=None):
        self.value = value
        self.line = line

class IfStatement(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None, line=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line

class ForLoop(ASTNode):
    def __init__(self, init, condition, update, body, line=None):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
        self.line = line

class ForInLoop(ASTNode):
    """for (item in collection) { ... }"""
    def __init__(self, var, iterable, body, line=None):
        self.var = var
        self.iterable = iterable
        self.body = body
        self.line = line

class WhileLoop(ASTNode):
    def __init__(self, condition, body, line=None):
        self.condition = condition
        self.body = body
        self.line = line

class BreakStatement(ASTNode):
    def __init__(self, line=None):
        self.line = line

class ContinueStatement(ASTNode):
    def __init__(self, line=None):
        self.line = line

class Block(ASTNode):
    def __init__(self, statements, line=None):
        self.statements = statements
        self.line = line

class ExpressionStatement(ASTNode):
    def __init__(self, expr, line=None):
        self.expr = expr
        self.line = line

class BinaryOp(ASTNode):
    def __init__(self, left, op, right, line=None):
        self.left = left
        self.op = op
        self.right = right
        self.line = line

class UnaryOp(ASTNode):
    def __init__(self, op, expr, line=None):
        self.op = op
        self.expr = expr
        self.line = line

class CallExpression(ASTNode):
    def __init__(self, callee, args, line=None):
        self.callee = callee
        self.args = args
        self.line = line

class Identifier(ASTNode):
    def __init__(self, name, line=None):
        self.name = name
        self.line = line

class Literal(ASTNode):
    def __init__(self, value, line=None):
        self.value = value
        self.line = line

class TemplateLiteral(ASTNode):
    """A backtick string with {expr} interpolation, stored as a list of
    parts where each part is either a str (literal) or an AST expression."""
    def __init__(self, parts, line=None):
        self.parts = parts
        self.line = line

class ArrayLiteral(ASTNode):
    def __init__(self, elements, line=None):
        self.elements = elements
        self.line = line

class ObjectLiteral(ASTNode):
    def __init__(self, pairs, line=None):
        self.pairs = pairs
        self.line = line

class Assignment(ASTNode):
    def __init__(self, target, value, op='=', line=None):
        self.target = target
        self.value = value
        self.op = op
        self.line = line

class TryCatch(ASTNode):
    def __init__(self, try_block, catch_var, catch_block, finally_block=None, line=None):
        self.try_block = try_block
        self.catch_var = catch_var
        self.catch_block = catch_block
        self.finally_block = finally_block
        self.line = line

class ThrowStatement(ASTNode):
    def __init__(self, value, line=None):
        self.value = value
        self.line = line

class IndexExpression(ASTNode):
    def __init__(self, obj, index, line=None):
        self.obj = obj
        self.index = index
        self.line = line

class MemberExpression(ASTNode):
    """Dot access: obj.name"""
    def __init__(self, obj, name, line=None):
        self.obj = obj
        self.name = name
        self.line = line

class PythonBlock(ASTNode):
    """python { ... raw python ... } embedded code block."""
    def __init__(self, code, line=None):
        self.code = code
        self.line = line
