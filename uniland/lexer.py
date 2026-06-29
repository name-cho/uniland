from .errors import UniLandError

# Only true structural keywords. Built-in functions (print, map, ...) are
# ordinary identifiers resolved as values at runtime — that keeps the core small.
KEYWORDS = {
    'let', 'const', 'func', 'fn', 'return', 'if', 'else', 'for', 'while',
    'break', 'continue', 'try', 'catch', 'finally', 'throw',
    'true', 'false', 'null', 'in', 'python',
}

# Multi-character operators, matched longest-first.
MULTI_OPS = ['==', '!=', '>=', '<=', '&&', '||', '++', '--',
             '+=', '-=', '*=', '/=', '%=', '=>']
SINGLE_OPS = set('+-*/%^=<>!&|')
PUNCT = set('(){}[],.;:')

# Newlines right after these do NOT end a statement (line continuation).
_CONT_OPS = SINGLE_OPS | {op for op in MULTI_OPS if op != '++' and op != '--'}


class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"


class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.i = 0
        self.n = len(source)
        self.line = 1
        self.col = 1
        # Stack of open brackets. Newlines are ignored only when the innermost
        # open bracket is '(' or '[' (line continuation inside calls/lists).
        # Inside '{ }' (blocks, object literals) newlines stay meaningful.
        self.brackets = []

    def _advance(self, count=1):
        for _ in range(count):
            if self.i < self.n:
                if self.source[self.i] == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.i += 1

    def _add(self, type_, value, line, col):
        self.tokens.append(Token(type_, value, line, col))

    def _last(self):
        return self.tokens[-1] if self.tokens else None

    def tokenize(self):
        src = self.source
        while self.i < self.n:
            c = src[self.i]

            # whitespace (not newline)
            if c in ' \t\r':
                self._advance()
                continue

            # newline -> maybe a statement terminator
            if c == '\n':
                self._maybe_newline()
                self._advance()
                continue

            # comments
            if src.startswith('//', self.i) or c == '#':
                while self.i < self.n and src[self.i] != '\n':
                    self._advance()
                continue
            if src.startswith('/*', self.i):
                while self.i < self.n and not src.startswith('*/', self.i):
                    self._advance()
                self._advance(2)
                continue

            line, col = self.line, self.col

            # double-quoted string
            if c == '"':
                self._read_string(line, col)
                continue

            # backtick template string
            if c == '`':
                self._read_template(line, col)
                continue

            # number
            if c.isdigit() or (c == '.' and self.i + 1 < self.n and src[self.i + 1].isdigit()):
                self._read_number(line, col)
                continue

            # identifier / keyword (allow unicode letters)
            if c.isalpha() or c == '_':
                self._read_word(line, col)
                continue

            # multi-char operators
            two = src[self.i:self.i + 2]
            if two in MULTI_OPS:
                self._add('OPERATOR', two, line, col)
                self._advance(2)
                continue

            # single-char operators
            if c in SINGLE_OPS:
                self._add('OPERATOR', c, line, col)
                self._advance()
                continue

            # punctuation
            if c in PUNCT:
                if c in '([{':
                    self.brackets.append(c)
                elif c in ')]}':
                    if self.brackets:
                        self.brackets.pop()
                self._add('PUNCTUATION', c, line, col)
                self._advance()
                continue

            raise UniLandError(f"Unexpected character {c!r}", line, col)

        self._strip_trailing_newline()
        self._add('EOF', '', self.line, self.col)
        return self.tokens

    def _maybe_newline(self):
        last = self._last()
        if last is None or last.type == 'NEWLINE':
            return
        if self.brackets and self.brackets[-1] in ('(', '['):
            return
        if last.type == 'OPERATOR' and last.value in _CONT_OPS:
            return
        if last.type == 'PUNCTUATION' and last.value in ('(', '[', '{', ',', '.', ':'):
            return
        self._add('NEWLINE', '\n', self.line, self.col)

    def _strip_trailing_newline(self):
        while self.tokens and self.tokens[-1].type == 'NEWLINE':
            self.tokens.pop()

    def _read_number(self, line, col):
        src = self.source
        start = self.i
        seen_dot = False
        while self.i < self.n:
            ch = src[self.i]
            if ch.isdigit():
                self._advance()
            elif ch == '.' and not seen_dot:
                seen_dot = True
                self._advance()
            else:
                break
        self._add('NUMBER', src[start:self.i], line, col)

    def _read_word(self, line, col):
        src = self.source
        start = self.i
        while self.i < self.n and (src[self.i].isalnum() or src[self.i] == '_'):
            self._advance()
        word = src[start:self.i]

        # python { ... } embedded block
        if word == 'python':
            j = self.i
            while j < self.n and src[j] in ' \t\r\n':
                j += 1
            if j < self.n and src[j] == '{':
                code = self._capture_python_block(j)
                self._add('PYBLOCK', code, line, col)
                return

        if word in KEYWORDS:
            self._add('KEYWORD', word, line, col)
        else:
            self._add('IDENTIFIER', word, line, col)

    def _capture_python_block(self, brace_index):
        """brace_index points at the opening '{'. Returns the raw inner code,
        consuming the input up to and including the matching '}'."""
        # advance to the opening brace
        while self.i < brace_index:
            self._advance()
        src = self.source
        self._advance()  # consume '{'
        start = self.i
        depth = 1
        while self.i < self.n and depth > 0:
            ch = src[self.i]
            # skip python string literals so braces inside them don't count
            if ch in ('"', "'"):
                if src.startswith(ch * 3, self.i):
                    quote = ch * 3
                    self._advance(3)
                    while self.i < self.n and not src.startswith(quote, self.i):
                        self._advance()
                    self._advance(3)
                else:
                    self._advance()
                    while self.i < self.n and src[self.i] != ch:
                        if src[self.i] == '\\':
                            self._advance()
                        self._advance()
                    self._advance()
                continue
            if ch == '#':
                while self.i < self.n and src[self.i] != '\n':
                    self._advance()
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
            self._advance()
        code = src[start:self.i]
        self._advance()  # consume closing '}'
        return code

    def _read_string(self, line, col):
        src = self.source
        self._advance()  # opening quote
        out = []
        while self.i < self.n and src[self.i] != '"':
            ch = src[self.i]
            if ch == '\\':
                self._advance()
                if self.i >= self.n:
                    break
                esc = src[self.i]
                out.append({'n': '\n', 't': '\t', 'r': '\r',
                            '"': '"', '\\': '\\', '0': '\0'}.get(esc, esc))
                self._advance()
            else:
                out.append(ch)
                self._advance()
        if self.i >= self.n:
            raise UniLandError("Unterminated string", line, col)
        self._advance()  # closing quote
        self._add('STRING', ''.join(out), line, col)

    def _read_template(self, line, col):
        """Backtick string. Stored raw (including {expr} markers); the parser
        splits it into literal/expression parts. Supports newlines and {{ }}."""
        src = self.source
        self._advance()  # opening backtick
        out = []
        while self.i < self.n and src[self.i] != '`':
            ch = src[self.i]
            if ch == '\\':
                self._advance()
                if self.i >= self.n:
                    break
                esc = src[self.i]
                out.append({'n': '\n', 't': '\t', 'r': '\r',
                            '`': '`', '\\': '\\', '{': '{', '}': '}'}.get(esc, esc))
                self._advance()
            else:
                out.append(ch)
                self._advance()
        if self.i >= self.n:
            raise UniLandError("Unterminated template string", line, col)
        self._advance()  # closing backtick
        self._add('TEMPLATE', ''.join(out), line, col)
