import string
import itertools

__version__ = "not yet, not yet"


class ParserError(Exception):
    def __init__(self, line_nr, col_nr, msg, content):
        line = content.splitlines(keepends=True)[line_nr]

        # TODO not sure what ruby version's super() does

        lines = [
            "parse error at line {line_nr}, col {col_nr}: {msg}".format(
                line_nr=line_nr + 1, col_nr=col_nr, msg=msg
            ),
            "",
            line.rstrip(),
            "\033[31m" + " " * max([col_nr - 1, 0]) + "↑" + "\033[0m",
        ]

        Exception.__init__(self, "\n".join(lines))


class Element(object):
    name = attributes = children = None

    def __init__(self, name, attributes, children):
        self.name = name
        self.attributes = attributes
        self.children = children

    def __repr__(self):
        return "Element({name}, {attributes}{children})".format(
            name=self.name,
            attributes=self._repr_attributes(),
            children=repr(self.children),
        )

    def _repr_attributes(self):
        """
        This isn't really ~necessary; I'm just papering over a difference
        between Python and Ruby representations to make it easier to see
        how the element trees compare
        """
        if not self.attributes:
            return ""
        else:
            return "{%s}" % ", ".join(
                ["%r=>%r" % (key, value) for key, value in self.attributes.items()]
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.name == other.name
            and self.children == other.children
            and self.attributes == other.attributes
        )


class Parser(object):
    # ref:
    # IDENTIFIER_CHARS = Set.new(['a'..'z', 'A'..'Z', ['-', '_'], '0'..'9'].map(&:to_a).flatten)
    IDENTIFIER_CHARS = string.ascii_letters + "-_" + string.digits
    # using "raw" for what ruby impl calls "input"
    # because "input" is a builtin
    pos = col_nr = line_nr = length = raw = raw_chars = None

    def __init__(self, raw):
        self.raw = raw
        # TODO: ruby impl uses raw.chars.size here; not certain if len ~=
        self.length = len(raw)

        self.pos = 0
        self.col_nr = 0
        self.line_nr = 0

    def parse(self):
        res = []

        while self.pos < self.length:
            blank_pos = self.try_read_blank_line()
            if not blank_pos:
                break

            self.pos = blank_pos
            self.line_nr += 1
            self.col_nr = 0

        while self.pos < self.length:
            res.append(self.read_block_with_children())

        return res

    def try_read_blank_line(self):
        pos = self.pos

        while True:
            char = self.raw[pos]
            if char == " ":
                pos += 1
            elif char == None:
                return pos + 1
            elif char == "\n":
                return pos + 1
            else:
                return None

    # TODO: written out
    # def eof(self, pos):
    #     return pos >= self.length

    def advance(self):
        if self.raw[self.pos] == "\n":
            self.line_nr += 1
            self.col_nr = 0

        self.pos += 1
        self.col_nr += 1

    def read_char(self, expected_char):
        char = self.raw[self.pos]
        if char != expected_char:
            self.raise_parse_error(
                f"expected {repr(expected_char)}, but got {'EOF' if char == None else repr(char)}"
            )
        else:
            self.advance()
            return char

    def read_block_with_children(self, indentation=0):
        res = self.read_single_block()

        pending_blanks = 0
        while self.pos < self.length:
            blank_pos = self.try_read_blank_line()
            if blank_pos:
                self.pos = blank_pos
                self.line_nr += 1
                self.col_nr = 0
                pending_blanks += 1
            else:
                sub_indentation = self.detect_indentation()
                if sub_indentation < indentation + 1:
                    break

                self.read_indentation(indentation + 1)
                if self.try_read_block_start():
                    res.children.append(self.read_block_with_children(indentation + 1))
                else:
                    if len(res.children):
                        res.children.append("\n")

                    res.children.extend(["\n"] * pending_blanks)
                    pending_blanks = 0

                    res.children.extend(self.read_inline_content())
                    self.read_end_of_inline_content()

        return res

    # FIXME: ugly and duplicated
    def try_read_block_start(self):
        if self.raw[self.pos] == "#":
            next_char = self.raw[self.pos + 1]
            # TODO I suspect ruby impl uses faster numeric check?
            return next_char in string.ascii_lowercase
        else:
            return False

    def detect_indentation(self):
        indentation_chars = 0
        pos = self.pos

        while True:
            if self.raw[pos] == " ":
                pos += 1
                indentation_chars += 1
            else:
                break

        return indentation_chars / 2

    def read_indentation(self, indentation):
        for x in range(indentation):
            self.read_char(" ")
            self.read_char(" ")

    def read_single_block(self):
        self.read_char("#")
        identifier = self.read_identifier()

        attributes = self.read_attributes() if self.raw[self.pos] == "[" else {}

        if self.raw[self.pos] in (None, "\n"):
            self.advance()
            return Element(identifier, attributes, [])
        else:
            self.read_char(" ")
            content = self.read_inline_content()
            self.read_end_of_inline_content()
            return Element(identifier, attributes, content)

    def read_end_of_inline_content(self):
        char = self.raw[self.pos]
        if char in ("\n", None):
            return self.advance()
        elif char == "}":
            return self.raise_parse_error('unexpected } -- try escaping it as "%}"')
        else:
            return self.raise_parse_error("unexpected content")

    def read_identifier(self):
        a = self.read_identifier_head()
        b = self.read_identifier_tail()
        return f"{a}{b}"

    def read_identifier_head(self):
        char = self.raw[self.pos]
        if char in string.ascii_letters:
            self.advance()
            return char
        else:
            return self.raise_parse_error(
                f"expected an identifier, but got {repr(char)}"
            )

    def read_identifier_tail(self):
        res = ""

        while True:
            char = self.raw[self.pos]
            if char not in self.IDENTIFIER_CHARS:
                break

            self.advance()
            res += char

        return res

    def read_attributes(self):
        self.read_char("[")

        res = {}

        at_start = True
        while True:
            char = self.raw[self.pos]
            if char == "]":
                self.advance()
                break
            else:
                if not at_start:
                    self.read_char(",")

                key = self.read_attribute_key()
                if self.raw[self.pos] == "=":
                    self.read_char("=")
                    value = self.read_attribute_value()
                else:
                    value = key

                res[key] = value

                at_start = False

        return res

    def read_attribute_key(self):
        return self.read_identifier()

    def read_attribute_value(self):
        res = ""

        is_escaping = False
        while True:
            char = self.raw[self.pos]

            if is_escaping:
                if char in ("%", "]", ","):
                    self.advance()
                    res += char
                    is_escaping = False
                elif char == None:
                    self.raise_parse_error("unexpected file end in attribute value")
                elif char == "\n":
                    self.raise_parse_error("unexpected line break in attribute value")
                else:
                    self.raise_parse_error(
                        f'(expected "%", "," or "]" after "%", but got {repr(char)})'
                    )
            else:
                if char in ("]", ","):
                    break
                elif char == "%":
                    self.advance()
                    is_escaping = True
                elif char == None:
                    raise_parse_error("unexpected file end in attribute value")
                elif char == "\n":
                    raise_parse_error("unexpected line break in attribute value")
                else:
                    self.advance()
                    res += char

        return res

    def read_inline_content(self):
        res = []

        while True:
            char = self.raw[self.pos]
            if char in ("\n", None):
                break
            elif char == "}":
                break
            elif char == "%":
                self.advance()
                res.append(self.read_percent_body())
            else:
                res.append(self.read_string())

        return res

    def read_string(self):
        res = ""

        while True:
            char = self.raw[self.pos]
            if char in (None, "\n", "%", "}"):
                break
            else:
                self.advance()
                res += char

        return res

    def read_percent_body(self):
        char = self.raw[self.pos]
        if char in ("%", "}", "#"):
            self.advance()
            return char
        elif char in (None, "\n"):
            return self.raise_parse_error("expected something after %")
        else:
            return self.read_inline_element()

    def read_inline_element(self):
        name = self.read_identifier()
        attributes = self.read_attributes() if self.raw[self.pos] == "[" else {}

        self.read_char("{")
        contents = self.read_inline_content()
        self.read_char("}")

        return Element(name, attributes, contents)

    def raise_parse_error(self, msg):
        raise ParserError(self.line_nr, self.col_nr, msg, self.raw)


class UnhandledNode(Exception):
    def __init__(self, node):
        msg = None

        if isinstance(node, str):
            msg = "Unhandled string node"
        elif isinstance(node, Element):
            msg = f"Unhandled element node {repr(node.name)}"
        else:
            msg = f"Unhandled node #{repr(node)}"

        Exception.__init__(msg)


class Translator(object):
    @classmethod
    def translate(cls, nodes, context=None):
        context = context or {}
        return "".join(
            itertools.chain.from_iterable(
                map(lambda node: cls.handle(node, context), nodes)
            )
        )

    @classmethod
    def handle(cls, node, context=None):
        context = context or {}
        if isinstance(node, str):
            return cls.handle_string(node, context)
        elif isinstance(node, Element):
            return cls.handle_element(node, context)
        else:
            raise TypeError(f"Cannot handle {node.__class__}")

    @classmethod
    def handle_string(cls, string, _context):
        raise NotImplementedError()

    @classmethod
    def handle_element(cls, element, _context):
        raise NotImplementedError()

    @classmethod
    def handle_children(cls, node, context):
        return [cls.handle(child, context) for child in node.children]
