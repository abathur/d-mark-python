"""
This suite (hopefully) tracks the following upstream suite:
spec/d-mark/element_node_spec.rb

Caution:
- initially translated by LLM--may be ~haunted
- LLM translated upstream's `describe` blocks into separate
  classes and even gave the first fixtures, but I flattened
  these back out (and combined the parser message stuff into
  a single test) because it didn't feel very idiomatic.
"""

import pytest
import dmark


@pytest.fixture
def name():
    return "para"


@pytest.fixture
def attributes():
    return {}


@pytest.fixture
def children():
    return ["Hello!"]


@pytest.fixture
def element_node(name, attributes, children):
    return dmark.Element(name, attributes, children)


# swapped double -> single quotes in these to square
# with python repr behavior
def test_repr_without_attributes(element_node):
    # element_node = dmark.Element("para", {}, ["Hello!"])
    assert repr(element_node) == "Element(para, ['Hello!'])"


def test_repr_with_attributes():
    element_node = dmark.Element("para", {"only": "web"}, ["Hello!"])
    assert repr(element_node) == "Element(para, {'only' => 'web'}, ['Hello!'])"


def test_when_other_is_not_an_element(element_node):
    other = "donkey"
    assert (element_node == other) is False


def test_when_other_does_not_differ(name, attributes, children):
    element_node = dmark.Element(name, attributes, children)
    other = dmark.Element(name, attributes, children)
    assert (element_node == other) is True


def test_when_other_differs_in_name(attributes, children):
    element_node = dmark.Element("para", attributes, children)
    other = dmark.Element("giraffe", attributes, children)
    assert (element_node == other) is False


def test_when_other_differs_in_attributes(name, children):
    element_node = dmark.Element(name, {}, children)
    other = dmark.Element(name, {"friend": "donkey"}, children)
    assert (element_node == other) is False


def test_when_other_differs_in_children(name, attributes):
    element_node = dmark.Element(name, attributes, ["Hello!"])
    other = dmark.Element(name, attributes, [])
    assert (element_node == other) is False
