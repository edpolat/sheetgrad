import re

from sheetgrad.engine import Value

TOKEN_PATTERN = re.compile(
    r"""
    \s*(?:
        (?P<NUMBER>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
      | (?P<FUNC>[A-Za-z][A-Za-z0-9.]*(?=\())
      | (?P<CELL>\$?[A-Za-z]{1,3}\$?\d+)
      | (?P<OP>[-+*/^])
      | (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<COMMA>,)
      | (?P<COLON>:)
    )
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> list[tuple[str, str]]:
    text = text.strip()
    if text.startswith("="):
        text = text[1:]
    tokens = []
    pos = 0
    while pos < len(text):
        if text[pos:].strip() == "":
            break
        match = TOKEN_PATTERN.match(text, pos)
        if not match:
            raise ValueError(f"Anlaşılamayan karakter: {text[pos:]!r}")
        kind = match.lastgroup
        value = match.group(kind)
        if kind in ("CELL", "FUNC"):
            value = value.replace("$", "").upper()
        tokens.append((kind, value))
        pos = match.end()
    return tokens


def column_to_number(letters: str) -> int:
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - ord("A") + 1)
    return number


def number_to_column(number: int) -> str:
    letters = ""
    while number > 0:
        number, rest = divmod(number - 1, 26)
        letters = chr(ord("A") + rest) + letters
    return letters


def split_cell(ref: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    return match.group(1), int(match.group(2))


def expand_range(start: str, end: str) -> list[str]:
    col1, row1 = split_cell(start)
    col2, row2 = split_cell(end)
    c1, c2 = sorted((column_to_number(col1), column_to_number(col2)))
    r1, r2 = sorted((row1, row2))
    return [
        f"{number_to_column(c)}{r}"
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
    ]


def _flatten(args):
    values = []
    for arg in args:
        if isinstance(arg, list):
            values.extend(arg)
        else:
            values.append(arg)
    return values


def _sum(args):
    values = _flatten(args)
    total = Value(0.0)
    for v in values:
        total = total + v
    return total


def _average(args):
    values = _flatten(args)
    return _sum(values) / len(values)


def _single(name, args):
    if len(args) != 1 or isinstance(args[0], list):
        raise ValueError(f"{name} tek bir değer alır")
    return args[0]


FUNCTIONS = {
    "SUM": _sum,
    "AVERAGE": _average,
    "EXP": lambda args: _single("EXP", args).exp(),
    "LN": lambda args: _single("LN", args).log(),
}


class Parser:
    def __init__(self, tokens, get_cell):
        self.tokens = tokens
        self.pos = 0
        self.get_cell = get_cell

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def take(self, kind=None, value=None):
        token = self.peek()
        if token[0] is None:
            raise ValueError("Formül beklenmedik şekilde bitti")
        if kind is not None and token[0] != kind:
            raise ValueError(f"{kind} beklendi, {token[1]!r} geldi")
        if value is not None and token[1] != value:
            raise ValueError(f"{value!r} beklendi, {token[1]!r} geldi")
        self.pos += 1
        return token

    def parse(self):
        result = self.expression()
        if self.peek()[0] is not None:
            raise ValueError(f"Fazladan ifade: {self.peek()[1]!r}")
        if isinstance(result, list):
            raise ValueError("Aralık (A1:A3) sadece fonksiyon içinde kullanılabilir")
        return result

    # expression := term (('+' | '-') term)*
    def expression(self):
        left = self.term()
        while self.peek() in (("OP", "+"), ("OP", "-")):
            op = self.take()[1]
            right = self.term()
            left = left + right if op == "+" else left - right
        return left

    # term := power (('*' | '/') power)*
    def term(self):
        left = self.power()
        while self.peek() in (("OP", "*"), ("OP", "/")):
            op = self.take()[1]
            right = self.power()
            left = left * right if op == "*" else left / right
        return left

    # power := unary ('^' unary)*      Excel'de ^ soldan sağa hesaplanır
    def power(self):
        left = self.unary()
        while self.peek() == ("OP", "^"):
            self.take()
            right = self.unary()
            left = left ** right
        return left

    # unary := ('-' | '+') unary | primary      Excel'de eksi işareti ^'den önce gelir
    def unary(self):
        if self.peek() == ("OP", "-"):
            self.take()
            return -self.unary()
        if self.peek() == ("OP", "+"):
            self.take()
            return self.unary()
        return self.primary()

    # primary := NUMBER | CELL [':' CELL] | FUNC '(' args ')' | '(' expression ')'
    def primary(self):
        kind, value = self.peek()

        if kind == "NUMBER":
            self.take()
            return Value(float(value))

        if kind == "CELL":
            self.take()
            if self.peek()[0] == "COLON":
                self.take()
                end = self.take("CELL")[1]
                return [self.get_cell(ref) for ref in expand_range(value, end)]
            return self.get_cell(value)

        if kind == "FUNC":
            self.take()
            if value not in FUNCTIONS:
                raise NotImplementedError(f"Desteklenmeyen fonksiyon: {value}")
            self.take("LPAREN")
            args = []
            if self.peek()[0] != "RPAREN":
                args.append(self.expression())
                while self.peek()[0] == "COMMA":
                    self.take()
                    args.append(self.expression())
            self.take("RPAREN")
            return FUNCTIONS[value](args)

        if kind == "LPAREN":
            self.take()
            result = self.expression()
            self.take("RPAREN")
            return result

        raise ValueError(f"Beklenmeyen ifade: {value!r}")


def evaluate(text: str, get_cell) -> Value:
    return Parser(tokenize(text), get_cell).parse()