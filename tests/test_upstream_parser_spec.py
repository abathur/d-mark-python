"""
This suite (hopefully) tracks the following upstream suite:
spec/d-mark/parser_spec.rb

Caution:
- initially translated by LLM--may be ~haunted
- LLM translated upstream's `describe` blocks into separate
  classes and even gave the first fixtures, but I flattened
  these back out (and combined the parser message stuff into
  a single test) because it didn't feel very idiomatic.
"""

import pytest
import dmark


# TODO: extract below into util.py if you need to carry
#       additional parser tests?
def parse(string):
    return dmark.Parser(string).parse()


def element(name, attributes, children):
    return dmark.Element(name, attributes, children)


def test_parser_error_messages():
    """
    This test covers all of upstream's
    `describe DMark::Parser::ParserError` block.

    It differs a little in form (not substance) to
    reduce duplication.
    """
    with pytest.raises(dmark.ParserError) as exc_info:
        parse("#p Stuff\n\n#p More stuff }")

    error = exc_info.value
    assert (
        error.message
        == 'parse error at line 3, col 15: unexpected } -- try escaping it as "%}"'
    )

    assert (
        error.fancy_message
        == 'parse error at line 3, col 15: unexpected } -- try escaping it as "%}"\n\n#p More stuff }\n\033[31m             ↑\033[0m'
    )

    assert error.fancy_message == error.extended_message


def test_parses():
    assert parse("") == []
    assert parse("#p") == [element("p", {}, [])]
    assert parse("#p hi") == [element("p", {}, ["hi"])]
    assert parse("#p hi %%") == [element("p", {}, ["hi ", "%"])]
    assert parse("#p hi %}") == [element("p", {}, ["hi ", "}"])]


def test_parses_element_with_name_containing_dash():
    assert parse("#intro-para hi") == [element("intro-para", {}, ["hi"])]


def test_parses_element_with_name_containing_underscore():
    assert parse("#intro_para hi") == [element("intro_para", {}, ["hi"])]


def test_parses_element_with_name_containing_uppercase_letters():
    assert parse("#IntroPara hi") == [element("IntroPara", {}, ["hi"])]


def test_does_not_parse_element_with_name_starting_with_dash():
    with pytest.raises(dmark.ParserError):
        parse("#-intro hi there")


def test_does_not_parse_element_with_name_starting_with_underscore():
    with pytest.raises(dmark.ParserError):
        parse("#_intro hi there")


def test_does_not_parse_element_with_name_starting_with_digit():
    with pytest.raises(dmark.ParserError):
        parse("#4ever best friends")


def test_parses_escaped_percent_in_block():
    assert parse("#p %%") == [element("p", {}, ["%"])]


def test_parses_escaped_brace_in_block():
    assert parse("#p %}") == [element("p", {}, ["}"])]


def test_parses_escaped_percent_in_inline_block():
    assert parse("#p %foo{%%}") == [element("p", {}, [element("foo", {}, ["%"])])]


def test_parses_escaped_brace_in_inline_block():
    assert parse("#p %foo{%}}") == [element("p", {}, [element("foo", {}, ["}"])])]


def test_parses_block_with_text_and_element_content():
    assert parse("#p hi %em{ho}") == [
        element("p", {}, ["hi ", element("em", {}, ["ho"])])
    ]


def test_parses_block_with_text_and_element_content_followed_by_newline():
    assert parse("#p hi %em{ho}\n") == [
        element("p", {}, ["hi ", element("em", {}, ["ho"])])
    ]


def test_parses_children():
    assert parse("#p hi %em{ho}\n  #p child p") == [
        element(
            "p",
            {},
            ["hi ", element("em", {}, ["ho"]), element("p", {}, ["child p"])],
        )
    ]


def test_parses_children_multiple_levels_deep():
    assert parse("#p hi %em{ho}\n  #p child p\n    #p subchild p") == [
        element(
            "p",
            {},
            [
                "hi ",
                element("em", {}, ["ho"]),
                element("p", {}, ["child p", element("p", {}, ["subchild p"])]),
            ],
        )
    ]


def test_ignores_blanks():
    assert parse("#p foo\n \n  #p bar\n  \n\n    #p qux") == [
        element("p", {}, ["foo", element("p", {}, ["bar", element("p", {}, ["qux"])])])
    ]


def test_reads_multiple_consecutive_blocks():
    assert parse("#p foo\n#p bar") == [
        element("p", {}, ["foo"]),
        element("p", {}, ["bar"]),
    ]


def test_includes_raw_content():
    assert parse("#p foo\n  donkey") == [element("p", {}, ["foo", "\n", "donkey"])]


def test_includes_raw_content_including_initial_indentation():
    assert parse("#p foo\n    donkey") == [element("p", {}, ["foo", "\n", "  donkey"])]


def test_includes_raw_content_from_multiple_lines():
    assert parse("#p foo\n    donkey\n  giraffe\n    zebra\n") == [
        element("p", {}, ["foo", "\n", "  donkey", "\n", "giraffe", "\n", "  zebra"])
    ]


def test_includes_empty_lines_in_raw_content():
    assert parse("#p foo\n\n  donkey\n\n    giraffe\n") == [
        element("p", {}, ["foo", "\n", "\n", "donkey", "\n", "\n", "  giraffe"])
    ]


def test_does_not_include_line_break_after_empty_block_element_and_before_data_lines():
    assert parse("#p\n  donkey\n") == [element("p", {}, ["donkey"])]


def test_parses_inline_element_in_data_lines():
    assert parse("#p\n  %em{donkey}") == [
        element("p", {}, [element("em", {}, ["donkey"])])
    ]


def test_parses_empty_attributes():
    assert parse("#p[] hi") == [element("p", {}, ["hi"])]


def test_parses_single_attribute():
    assert parse("#p[foo=bar] hi") == [element("p", {"foo": "bar"}, ["hi"])]


def test_parses_attribute_with_dash():
    assert parse("#p[intended-audience=learner] hi") == [
        element("p", {"intended-audience": "learner"}, ["hi"])
    ]


def test_parses_attribute_with_numbers():
    assert parse("#p[is-over-9000=yup] hi") == [
        element("p", {"is-over-9000": "yup"}, ["hi"])
    ]


def test_parses_attribute_with_underscore():
    assert parse("#p[intended_audience=learner] hi") == [
        element("p", {"intended_audience": "learner"}, ["hi"])
    ]


def test_parses_attribute_with_uppercase_letters():
    assert parse("#p[IntendedAudience=learner] hi") == [
        element("p", {"IntendedAudience": "learner"}, ["hi"])
    ]


def test_does_not_parse_attributes_starting_with_dash():
    with pytest.raises(dmark.ParserError):
        parse("#p[-this=is dog] hello yes")


def test_does_not_parse_attributes_starting_with_underscore():
    with pytest.raises(dmark.ParserError):
        parse("#p[_this=is dog] hello yes")


def test_does_not_parse_attributes_starting_with_digit():
    with pytest.raises(dmark.ParserError):
        parse("#p[4this=is dog] hello yes")


def test_parses_single_valueless_attribute():
    assert parse("#p[foo] hi") == [element("p", {"foo": "foo"}, ["hi"])]


def test_parses_multiple_attributes():
    assert parse("#p[foo=bar,qux=donkey] hi") == [
        element("p", {"foo": "bar", "qux": "donkey"}, ["hi"])
    ]


def test_parses_multiple_valueless_attributes():
    assert parse("#p[foo,qux] hi") == [
        element("p", {"foo": "foo", "qux": "qux"}, ["hi"])
    ]


def test_parses_escaped_attributes():
    assert parse("#p[foo=%],bar=%%,donkey=%,] hi") == [
        element("p", {"foo": "]", "bar": "%", "donkey": ","}, ["hi"])
    ]


def test_parses_attributes_in_empty_block():
    assert parse("#p[foo=bar]\n  hi") == [element("p", {"foo": "bar"}, ["hi"])]


def test_parses_block_start_on_next_line_properly():
    assert parse("#p\n  this is not a child block.") == [
        element("p", {}, ["this is not a child block."])
    ]


def test_parses_block_start_on_next_line_with_spacey():
    assert parse("#p\n  foo.bar") == [element("p", {}, ["foo.bar"])]


def test_parses_child_block_without_content():
    assert parse("#ul\n  #li\n    #p You can.") == [
        element("ul", {}, [element("li", {}, [element("p", {}, ["You can."])])])
    ]


def test_parses_child_block_without_content_at_end():
    assert parse("#ul\n  #li") == [element("ul", {}, [element("li", {}, [])])]


def test_parses_child_block_with_attributes():
    assert parse("#ul\n  #li[foo]") == [
        element("ul", {}, [element("li", {"foo": "foo"}, [])])
    ]


def test_parses_document_starting_with_blank_lines():
    assert parse("  \n \n#p Hi!") == [element("p", {}, ["Hi!"])]


def test_parses_escaped_indented_line():
    assert parse("#listing\n  %#h1 Foo\n") == [element("listing", {}, ["#", "h1 Foo"])]


def test_parses_escaped_indented_line_with_attributes():
    assert parse("#listing\n  %#h1[donkey] Foo\n") == [
        element("listing", {}, ["#", "h1[donkey] Foo"])
    ]


def test_does_not_parse_percent_escapes():
    with pytest.raises(
        dmark.ParserError,
        match='parse error at line 1, col 43: expected "%", "," or "]" after "%", but got "3"',
    ):
        parse("#p %ref[url=https://github.com/pulls?q=is%3Aopen+user%3Ananoc]{eek}")


def test_does_not_parse_attribute_values_ending_with_eof():
    with pytest.raises(
        dmark.ParserError,
        match="parse error at line 1, col 18: unexpected file end in attribute value",
    ):
        parse("#p %ref[url=hello")


def test_does_not_parse_attribute_values_ending_with_line_break():
    with pytest.raises(
        dmark.ParserError,
        match="parse error at line 1, col 18: unexpected line break in attribute value",
    ):
        parse("#p %ref[url=hello\n")


def test_does_not_parse_escaped_attribute_values_ending_with_eof():
    with pytest.raises(
        dmark.ParserError,
        match="parse error at line 1, col 19: unexpected file end in attribute value",
    ):
        parse("#p %ref[url=hello%")


def test_does_not_parse_escaped_attribute_values_ending_with_line_break():
    with pytest.raises(
        dmark.ParserError,
        match="parse error at line 1, col 19: unexpected line break in attribute value",
    ):
        parse("#p %ref[url=hello%\n")


def test_does_not_parse_invalid_input():
    with pytest.raises(dmark.ParserError):
        parse("#")
    with pytest.raises(dmark.ParserError):
        parse("p")
    with pytest.raises(dmark.ParserError):
        parse("0")
    with pytest.raises(dmark.ParserError):
        parse("p0")
    with pytest.raises(dmark.ParserError):
        parse("#0")
    with pytest.raises(dmark.ParserError):
        parse("#p %")
    with pytest.raises(dmark.ParserError):
        parse("#p }")
