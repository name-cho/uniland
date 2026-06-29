from .ast_nodes import *
from .errors import UniLandError
from . import builtins as B
from .builtins import Environment, BUILTIN_FUNCTIONS, uland_str


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class UniFunction:
    """A user-defined function value with a captured closure environment."""
    def __init__(self, params, body, closure, name="<anonymous>"):
        self.params = params
        self.body = body
        self.closure = closure
        self.name = name

    def __repr__(self):
        return f"<func {self.name}({', '.join(self.params)})>"


class UniBridge:
    """Exposed to embedded Python as `uni` — reads/writes UniLand globals."""
    def __init__(self, interp):
        object.__setattr__(self, '_i', interp)

    def __getattr__(self, key):
        try:
            return self._i.global_env.get(key)
        except UniLandError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self._i.global_env.define(key, value)

    def __getitem__(self, key):
        return self._i.global_env.get(key)

    def __setitem__(self, key, value):
        self._i.global_env.define(key, value)

    def call(self, name, *args):
        return self._i.call_value(self._i.global_env.get(name), list(args))


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.env = self.global_env
        for name, func in BUILTIN_FUNCTIONS.items():
            self.global_env.define(name, func)

        # Let higher-order builtins (map/filter/...) call back into UniLand.
        B.set_caller(self.call_value)

        # Persistent namespace for embedded `python { ... }` blocks.
        self.py_ns = {'__name__': 'uniland_embedded', 'uni': UniBridge(self)}
        self.global_env.define('pyeval', lambda a: self._pyeval(a))
        self.global_env.define('pyexec', lambda a: self._pyexec(a))
        self.global_env.define('py', lambda a: self._pyexec(a))

        # GUI builtins are registered lazily (tkinter import is deferred).
        try:
            from .gui import GUI_FUNCTIONS
            for name, func in GUI_FUNCTIONS.items():
                self.global_env.define(name, func)
        except Exception:
            pass

    # ---- embedded python -------------------------------------------------
    def _pyeval(self, args):
        if len(args) != 1 or not isinstance(args[0], str):
            raise UniLandError("pyeval() expects one string argument")
        try:
            return eval(args[0], self.py_ns)
        except Exception as e:
            raise UniLandError(f"Python error: {e}")

    def _pyexec(self, args):
        if len(args) != 1 or not isinstance(args[0], str):
            raise UniLandError("pyexec()/py() expects one string argument")
        try:
            exec(args[0], self.py_ns)
        except Exception as e:
            raise UniLandError(f"Python error: {e}")
        return None

    # ---- top level -------------------------------------------------------
    def interpret(self, program):
        for stmt in program.statements:
            self.execute(stmt)
        # Convenience: if a main() function exists, run it (no args).
        main = self.global_env.vars.get('main')
        if isinstance(main, UniFunction) and len(main.params) == 0:
            self.call_value(main, [])

    def call_value(self, fn, args, line=None):
        if isinstance(fn, UniFunction):
            if len(args) != len(fn.params):
                raise UniLandError(
                    f"{fn.name} expects {len(fn.params)} argument(s), got {len(args)}", line)
            call_env = Environment(parent=fn.closure)
            for param, arg in zip(fn.params, args):
                call_env.define(param, arg)
            old_env = self.env
            self.env = call_env
            try:
                self.execute(fn.body)
                return None
            except ReturnException as r:
                return r.value
            finally:
                self.env = old_env
        if callable(fn):
            return fn(args)
        raise UniLandError(f"Value of type {B.uland_typeof(fn)} is not callable", line)

    # ---- statements ------------------------------------------------------
    def execute(self, node):
        if isinstance(node, Block):
            old_env = self.env
            self.env = Environment(parent=old_env)
            try:
                for stmt in node.statements:
                    self.execute(stmt)
            finally:
                self.env = old_env

        elif isinstance(node, VariableDeclaration):
            self.env.define(node.name, self.evaluate(node.value), node.is_const)

        elif isinstance(node, FunctionDeclaration):
            fn = UniFunction(node.params, node.body, self.env, node.name)
            self.env.define(node.name, fn)

        elif isinstance(node, ReturnStatement):
            value = self.evaluate(node.value) if node.value is not None else None
            raise ReturnException(value)

        elif isinstance(node, IfStatement):
            if self.is_truthy(self.evaluate(node.condition)):
                self.execute(node.then_branch)
            elif node.else_branch is not None:
                self.execute(node.else_branch)

        elif isinstance(node, ForLoop):
            if node.init is not None:
                self.execute(node.init)
            while self.is_truthy(self.evaluate(node.condition)):
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass
                if node.update is not None:
                    self.execute(node.update)

        elif isinstance(node, ForInLoop):
            items = self._iterable(self.evaluate(node.iterable), node.line)
            old_env = self.env
            try:
                for item in items:
                    self.env = Environment(parent=old_env)
                    self.env.define(node.var, item)
                    try:
                        self.execute(node.body)
                    except BreakException:
                        break
                    except ContinueException:
                        continue
            finally:
                self.env = old_env

        elif isinstance(node, WhileLoop):
            while self.is_truthy(self.evaluate(node.condition)):
                try:
                    self.execute(node.body)
                except BreakException:
                    break
                except ContinueException:
                    pass

        elif isinstance(node, BreakStatement):
            raise BreakException()

        elif isinstance(node, ContinueStatement):
            raise ContinueException()

        elif isinstance(node, Assignment):
            self.exec_assignment(node)

        elif isinstance(node, ExpressionStatement):
            self.evaluate(node.expr)

        elif isinstance(node, PythonBlock):
            import textwrap
            self._pyexec([textwrap.dedent(node.code)])

        elif isinstance(node, TryCatch):
            try:
                self.execute(node.try_block)
            except UniLandError as e:
                if node.catch_block is not None:
                    old_env = self.env
                    self.env = Environment(parent=old_env)
                    if node.catch_var:
                        self.env.define(node.catch_var, e.message)
                    try:
                        self.execute(node.catch_block)
                    finally:
                        self.env = old_env
                else:
                    raise
            finally:
                if node.finally_block is not None:
                    self.execute(node.finally_block)

        elif isinstance(node, ThrowStatement):
            raise UniLandError(uland_str(self.evaluate(node.value)), node.line)

        else:
            raise UniLandError(f"Cannot execute node: {type(node).__name__}")

    def exec_assignment(self, node):
        op = node.op
        if op in ('++', '--'):
            current = self.evaluate(node.target)
            new_value = current + (1 if op == '++' else -1)
        elif op == '=':
            new_value = self.evaluate(node.value)
        else:
            current = self.evaluate(node.target)
            rhs = self.evaluate(node.value)
            new_value = self.apply_binary(op[0], current, rhs, node.line)
        self.assign_to(node.target, new_value, node.line)

    def assign_to(self, target, value, line):
        if isinstance(target, Identifier):
            self.env.set(target.name, value)
        elif isinstance(target, IndexExpression):
            obj = self.evaluate(target.obj)
            index = self.evaluate(target.index)
            if isinstance(obj, list):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise UniLandError("List index must be an integer", line)
                if index < 0 or index >= len(obj):
                    raise UniLandError(f"List index {index} out of range", line)
                obj[index] = value
            elif isinstance(obj, dict):
                obj[str(index)] = value
            else:
                raise UniLandError(f"Cannot assign by index into {B.uland_typeof(obj)}", line)
        elif isinstance(target, MemberExpression):
            obj = self.evaluate(target.obj)
            if isinstance(obj, dict):
                obj[target.name] = value
            else:
                raise UniLandError(f"Cannot assign field on {B.uland_typeof(obj)}", line)
        else:
            raise UniLandError("Invalid assignment target", line)

    # ---- expressions -----------------------------------------------------
    def evaluate(self, node):
        if isinstance(node, Literal):
            return node.value

        if isinstance(node, TemplateLiteral):
            out = []
            for part in node.parts:
                if isinstance(part, str):
                    out.append(part)
                else:
                    out.append(uland_str(self.evaluate(part)))
            return ''.join(out)

        if isinstance(node, Identifier):
            return self.env.get(node.name)

        if isinstance(node, BinaryOp):
            if node.op == '&&':
                left = self.evaluate(node.left)
                return self.evaluate(node.right) if self.is_truthy(left) else left
            if node.op == '||':
                left = self.evaluate(node.left)
                return left if self.is_truthy(left) else self.evaluate(node.right)
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return self.apply_binary(node.op, left, right, node.line)

        if isinstance(node, UnaryOp):
            val = self.evaluate(node.expr)
            if node.op == '-':
                return -val
            if node.op == '!':
                return not self.is_truthy(val)
            raise UniLandError(f"Unknown unary operator {node.op}", node.line)

        if isinstance(node, IndexExpression):
            obj = self.evaluate(node.obj)
            index = self.evaluate(node.index)
            if isinstance(obj, list):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise UniLandError("List index must be an integer", node.line)
                if index < 0:
                    index += len(obj)
                if index < 0 or index >= len(obj):
                    raise UniLandError(f"List index out of range (length {len(obj)})", node.line)
                return obj[index]
            if isinstance(obj, str):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise UniLandError("String index must be an integer", node.line)
                if index < 0:
                    index += len(obj)
                if index < 0 or index >= len(obj):
                    raise UniLandError("String index out of range", node.line)
                return obj[index]
            if isinstance(obj, dict):
                return obj.get(str(index))
            raise UniLandError(f"Cannot index {B.uland_typeof(obj)}", node.line)

        if isinstance(node, MemberExpression):
            obj = self.evaluate(node.obj)
            if isinstance(obj, dict):
                return obj.get(node.name)
            raise UniLandError(f"Cannot read field '{node.name}' of {B.uland_typeof(obj)}", node.line)

        if isinstance(node, CallExpression):
            fn = self.evaluate(node.callee)
            args = [self.evaluate(a) for a in node.args]
            return self.call_value(fn, args, node.line)

        if isinstance(node, FunctionExpression):
            return UniFunction(node.params, node.body, self.env)

        if isinstance(node, ArrayLiteral):
            return [self.evaluate(e) for e in node.elements]

        if isinstance(node, ObjectLiteral):
            obj = {}
            for key, value_node in node.pairs:
                obj[key] = self.evaluate(value_node)
            return obj

        raise UniLandError(f"Cannot evaluate node: {type(node).__name__}")

    def apply_binary(self, op, left, right, line=None):
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return uland_str(left) + uland_str(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op == '/':
            if right == 0:
                raise UniLandError("Division by zero", line)
            return left / right
        if op == '%':
            return left % right
        if op == '^':
            return left ** right
        if op == '==':
            return left == right
        if op == '!=':
            return left != right
        if op == '>':
            return left > right
        if op == '<':
            return left < right
        if op == '>=':
            return left >= right
        if op == '<=':
            return left <= right
        raise UniLandError(f"Unknown operator {op}", line)

    def _iterable(self, value, line):
        if isinstance(value, list):
            return list(value)
        if isinstance(value, str):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        raise UniLandError(f"Cannot iterate over {B.uland_typeof(value)}", line)

    def is_truthy(self, val):
        if val is None or val is False:
            return False
        if val is True:
            return True
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list, dict)):
            return len(val) > 0
        return True
