from .lexer import Lexer, Token
from .ast_nodes import *
from .errors import UniLandError

ASSIGN_OPS = {'=', '+=', '-=', '*=', '/=', '%='}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else Token('EOF', '', 0, 0)

    # ---- token helpers ---------------------------------------------------
    def peek(self, k=0):
        idx = self.pos + k
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token('EOF', '', 0, 0)

    def next_token(self):
        self.pos += 1
        self.current_token = self.peek()
        return self.current_token

    def expect(self, type_, value=None):
        t = self.current_token
        if t.type != type_ or (value is not None and t.value != value):
            want = value if value is not None else type_
            raise UniLandError(f"Expected {want}, got {t.type}('{t.value}')", t.line, t.column)
        self.next_token()
        return t

    def skip_newlines(self):
        while self.current_token.type == 'NEWLINE':
            self.next_token()

    def is_punct(self, value):
        t = self.current_token
        return t.type == 'PUNCTUATION' and t.value == value

    def is_kw(self, value):
        t = self.current_token
        return t.type == 'KEYWORD' and t.value == value

    def end_statement(self):
        t = self.current_token
        if t.type == 'PUNCTUATION' and t.value == ';':
            self.next_token()
            self.skip_newlines()
        elif t.type == 'NEWLINE':
            self.skip_newlines()
        elif t.type == 'EOF' or (t.type == 'PUNCTUATION' and t.value == '}'):
            pass
        else:
            raise UniLandError(f"Expected end of statement, got {t.type}('{t.value}')", t.line, t.column)

    # ---- entry points ----------------------------------------------------
    def parse(self):
        statements = []
        self.skip_newlines()
        while self.current_token.type != 'EOF':
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self.skip_newlines()
        return Program(statements)

    def parse_expression_only(self):
        """Parse a single expression (used for template interpolation)."""
        self.skip_newlines()
        return self.parse_expression()

    # ---- statements ------------------------------------------------------
    def parse_statement(self):
        self.skip_newlines()
        t = self.current_token

        if t.type == 'KEYWORD':
            if t.value in ('func', 'fn'):
                return self.parse_function_declaration()
            if t.value == 'if':
                return self.parse_if()
            if t.value == 'for':
                return self.parse_for()
            if t.value == 'while':
                return self.parse_while()
            if t.value == 'try':
                return self.parse_try()
        if t.type == 'PUNCTUATION' and t.value == '{':
            return self.parse_block()
        if t.type == 'PYBLOCK':
            self.next_token()
            node = PythonBlock(t.value, line=t.line)
            self.end_statement()
            return node

        node = self.parse_small()
        self.end_statement()
        return node

    def parse_small(self):
        """A statement without its own terminator (decl/return/assign/expr)."""
        t = self.current_token
        if t.type == 'KEYWORD':
            if t.value in ('let', 'const'):
                return self.parse_variable_declaration()
            if t.value == 'return':
                self.next_token()
                if self.current_token.type in ('NEWLINE', 'EOF') or self.is_punct(';') or self.is_punct('}'):
                    return ReturnStatement(None, line=t.line)
                return ReturnStatement(self.parse_expression(), line=t.line)
            if t.value == 'break':
                self.next_token()
                return BreakStatement(line=t.line)
            if t.value == 'continue':
                self.next_token()
                return ContinueStatement(line=t.line)
            if t.value == 'throw':
                self.next_token()
                return ThrowStatement(self.parse_expression(), line=t.line)

        expr = self.parse_expression()
        op = self.current_token
        if op.type == 'OPERATOR' and op.value in ASSIGN_OPS:
            self.next_token()
            value = self.parse_expression()
            return Assignment(expr, value, op.value, line=op.line)
        if op.type == 'OPERATOR' and op.value in ('++', '--'):
            self.next_token()
            return Assignment(expr, Literal(1), op.value, line=op.line)
        return ExpressionStatement(expr, line=t.line)

    def parse_block(self):
        self.expect('PUNCTUATION', '{')
        self.skip_newlines()
        statements = []
        while not self.is_punct('}') and self.current_token.type != 'EOF':
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self.skip_newlines()
        self.expect('PUNCTUATION', '}')
        return Block(statements)

    def parse_variable_declaration(self):
        is_const = self.current_token.value == 'const'
        self.next_token()
        ident = self.expect('IDENTIFIER')
        self.expect('OPERATOR', '=')
        value = self.parse_expression()
        return VariableDeclaration(ident.value, value, is_const, line=ident.line)

    def parse_function_declaration(self):
        self.next_token()
        name = self.expect('IDENTIFIER')
        params = self.parse_param_list()
        body = self.parse_block()
        return FunctionDeclaration(name.value, params, body, line=name.line)

    def parse_param_list(self):
        self.expect('PUNCTUATION', '(')
        self.skip_newlines()
        params = []
        if not self.is_punct(')'):
            while True:
                params.append(self.expect('IDENTIFIER').value)
                self.skip_newlines()
                if self.is_punct(','):
                    self.next_token()
                    self.skip_newlines()
                else:
                    break
        self.expect('PUNCTUATION', ')')
        return params

    def parse_if(self):
        line = self.current_token.line
        self.next_token()
        self.expect('PUNCTUATION', '(')
        condition = self.parse_expression()
        self.expect('PUNCTUATION', ')')
        then_branch = self.parse_block()
        else_branch = None
        self.skip_newlines()
        if self.is_kw('else'):
            self.next_token()
            self.skip_newlines()
            if self.is_kw('if'):
                else_branch = self.parse_if()
            else:
                else_branch = self.parse_block()
        return IfStatement(condition, then_branch, else_branch, line=line)

    def parse_for(self):
        line = self.current_token.line
        self.next_token()
        self.expect('PUNCTUATION', '(')

        if self._is_for_in():
            if self.is_kw('let') or self.is_kw('const'):
                self.next_token()
            var = self.expect('IDENTIFIER').value
            self.expect('KEYWORD', 'in')
            iterable = self.parse_expression()
            self.expect('PUNCTUATION', ')')
            body = self.parse_block()
            return ForInLoop(var, iterable, body, line=line)

        # classic C-style for
        if self.is_punct(';'):
            init = None
        else:
            init = self.parse_small()
        self.expect('PUNCTUATION', ';')
        condition = Literal(True) if self.is_punct(';') else self.parse_expression()
        self.expect('PUNCTUATION', ';')
        update = None if self.is_punct(')') else self.parse_small()
        self.expect('PUNCTUATION', ')')
        body = self.parse_block()
        return ForLoop(init, condition, update, body, line=line)

    def _is_for_in(self):
        # for (x in ...) or for (let x in ...)
        if self.is_kw('let') or self.is_kw('const'):
            return self.peek(1).type == 'IDENTIFIER' and self.peek(2).type == 'KEYWORD' and self.peek(2).value == 'in'
        if self.current_token.type == 'IDENTIFIER':
            return self.peek(1).type == 'KEYWORD' and self.peek(1).value == 'in'
        return False

    def parse_while(self):
        line = self.current_token.line
        self.next_token()
        self.expect('PUNCTUATION', '(')
        condition = self.parse_expression()
        self.expect('PUNCTUATION', ')')
        body = self.parse_block()
        return WhileLoop(condition, body, line=line)

    def parse_try(self):
        line = self.current_token.line
        self.next_token()
        try_block = self.parse_block()
        catch_var = None
        catch_block = None
        self.skip_newlines()
        if self.is_kw('catch'):
            self.next_token()
            if self.is_punct('('):
                self.next_token()
                catch_var = self.expect('IDENTIFIER').value
                self.expect('PUNCTUATION', ')')
            catch_block = self.parse_block()
        self.skip_newlines()
        finally_block = None
        if self.is_kw('finally'):
            self.next_token()
            finally_block = self.parse_block()
        return TryCatch(try_block, catch_var, catch_block, finally_block, line=line)

    # ---- expressions -----------------------------------------------------
    def parse_expression(self, min_prec=-2):
        left = self.parse_unary()
        while True:
            t = self.current_token
            if t.type != 'OPERATOR' or t.value not in PRECEDENCE:
                break
            prec = PRECEDENCE[t.value]
            if prec < min_prec:
                break
            self.next_token()
            self.skip_newlines()
            right = self.parse_expression(prec + 1)
            left = BinaryOp(left, t.value, right, line=t.line)
        return left

    def parse_unary(self):
        t = self.current_token
        if t.type == 'OPERATOR' and t.value in ('-', '!'):
            self.next_token()
            return UnaryOp(t.value, self.parse_unary(), line=t.line)
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            t = self.current_token
            if self.is_punct('('):
                self.next_token()
                self.skip_newlines()
                args = []
                if not self.is_punct(')'):
                    while True:
                        args.append(self.parse_expression())
                        self.skip_newlines()
                        if self.is_punct(','):
                            self.next_token()
                            self.skip_newlines()
                        else:
                            break
                self.expect('PUNCTUATION', ')')
                node = CallExpression(node, args, line=t.line)
            elif self.is_punct('['):
                self.next_token()
                index = self.parse_expression()
                self.expect('PUNCTUATION', ']')
                node = IndexExpression(node, index, line=t.line)
            elif self.is_punct('.'):
                self.next_token()
                name = self.expect('IDENTIFIER')
                node = MemberExpression(node, name.value, line=t.line)
            else:
                break
        return node

    def parse_primary(self):
        t = self.current_token

        # single-param arrow:  x => ...
        if t.type == 'IDENTIFIER' and self.peek(1).type == 'OPERATOR' and self.peek(1).value == '=>':
            self.next_token()  # ident
            self.next_token()  # =>
            return FunctionExpression([t.value], self.parse_arrow_body(), line=t.line)

        if t.type == 'NUMBER':
            self.next_token()
            val = float(t.value) if '.' in t.value else int(t.value)
            return Literal(val, line=t.line)

        if t.type == 'STRING':
            self.next_token()
            return Literal(t.value, line=t.line)

        if t.type == 'TEMPLATE':
            self.next_token()
            return self.build_template(t.value, t.line)

        if t.type == 'IDENTIFIER':
            self.next_token()
            return Identifier(t.value, line=t.line)

        if t.type == 'PYBLOCK':
            raise UniLandError("python {} block cannot be used as an expression", t.line, t.column)

        if t.type == 'KEYWORD':
            if t.value == 'true':
                self.next_token(); return Literal(True, line=t.line)
            if t.value == 'false':
                self.next_token(); return Literal(False, line=t.line)
            if t.value == 'null':
                self.next_token(); return Literal(None, line=t.line)
            if t.value in ('func', 'fn'):
                self.next_token()
                params = self.parse_param_list()
                return FunctionExpression(params, self.parse_block(), line=t.line)
            # other keywords used in expression position -> identifier-like
            self.next_token()
            return Identifier(t.value, line=t.line)

        if t.type == 'PUNCTUATION':
            if t.value == '(':
                params = self._try_arrow_params()
                if params is not None:
                    return FunctionExpression(params, self.parse_arrow_body(), line=t.line)
                self.next_token()
                self.skip_newlines()
                node = self.parse_expression()
                self.skip_newlines()
                self.expect('PUNCTUATION', ')')
                return node
            if t.value == '[':
                return self.parse_array()
            if t.value == '{':
                return self.parse_object()

        raise UniLandError(f"Unexpected token {t.type}('{t.value}')", t.line, t.column)

    def parse_array(self):
        line = self.current_token.line
        self.expect('PUNCTUATION', '[')
        self.skip_newlines()
        elements = []
        if not self.is_punct(']'):
            while True:
                elements.append(self.parse_expression())
                self.skip_newlines()
                if self.is_punct(','):
                    self.next_token()
                    self.skip_newlines()
                else:
                    break
        self.expect('PUNCTUATION', ']')
        return ArrayLiteral(elements, line=line)

    def parse_object(self):
        line = self.current_token.line
        self.expect('PUNCTUATION', '{')
        self.skip_newlines()
        pairs = []
        if not self.is_punct('}'):
            while True:
                key_tok = self.current_token
                if key_tok.type in ('IDENTIFIER', 'STRING'):
                    key = key_tok.value
                    self.next_token()
                else:
                    raise UniLandError("Expected identifier or string as object key", key_tok.line, key_tok.column)
                self.expect('PUNCTUATION', ':')
                value = self.parse_expression()
                pairs.append((key, value))
                self.skip_newlines()
                if self.is_punct(','):
                    self.next_token()
                    self.skip_newlines()
                else:
                    break
        self.skip_newlines()
        self.expect('PUNCTUATION', '}')
        return ObjectLiteral(pairs, line=line)

    def parse_arrow_body(self):
        self.skip_newlines()
        if self.is_punct('{'):
            return self.parse_block()
        expr = self.parse_expression()
        return Block([ReturnStatement(expr)])

    def _try_arrow_params(self):
        """If the upcoming tokens form '( params ) =>', consume them and return
        the param name list. Otherwise restore position and return None."""
        save = self.pos
        if not self.is_punct('('):
            return None
        self.next_token()
        params = []
        if not self.is_punct(')'):
            while True:
                if self.current_token.type != 'IDENTIFIER':
                    self._restore(save)
                    return None
                params.append(self.current_token.value)
                self.next_token()
                if self.is_punct(','):
                    self.next_token()
                    continue
                break
        if not self.is_punct(')'):
            self._restore(save)
            return None
        self.next_token()
        if not (self.current_token.type == 'OPERATOR' and self.current_token.value == '=>'):
            self._restore(save)
            return None
        self.next_token()
        return params

    def _restore(self, pos):
        self.pos = pos
        self.current_token = self.peek()

    def build_template(self, raw, line):
        parts = []
        buf = []
        i = 0
        n = len(raw)
        while i < n:
            ch = raw[i]
            if ch == '{' and i + 1 < n and raw[i + 1] == '{':
                buf.append('{'); i += 2; continue
            if ch == '}' and i + 1 < n and raw[i + 1] == '}':
                buf.append('}'); i += 2; continue
            if ch == '{':
                if buf:
                    parts.append(''.join(buf)); buf = []
                depth = 1
                j = i + 1
                expr_chars = []
                while j < n and depth > 0:
                    cj = raw[j]
                    if cj == '{':
                        depth += 1
                    elif cj == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    expr_chars.append(cj)
                    j += 1
                expr_src = ''.join(expr_chars).strip()
                sub_tokens = Lexer(expr_src).tokenize()
                sub_ast = Parser(sub_tokens).parse_expression_only()
                parts.append(sub_ast)
                i = j + 1
            else:
                buf.append(ch); i += 1
        if buf:
            parts.append(''.join(buf))
        return TemplateLiteral(parts, line=line)


PRECEDENCE = {
    '||': -1, '&&': -1,
    '==': 0, '!=': 0,
    '<': 1, '<=': 1, '>': 1, '>=': 1,
    '+': 2, '-': 2,
    '*': 3, '/': 3, '%': 3,
    '^': 4,
}
