"""
This suite (hopefully) tracks the following upstream suite:
spec/d-mark/translator_spec.rb

Caution:
- initially translated by LLM--may be ~haunted
- LLM translated upstream's `describe` blocks into separate
  classes and even gave the first fixtures, but I flattened
  these back out (and combined the parser message stuff into
  a single test) because it didn't feel very idiomatic.
"""

import pytest
import dmark


class TestTranslator:
    @pytest.fixture
    def translator(self):
        return dmark.Translator()

    @pytest.fixture
    def nodes(self):
        return [
            dmark.Element(
                "para",
                {"only": "web", "animal": "donkey"},
                [dmark.Element("em", {}, ["Hello"]), " world!"],
            )
        ]

    class TestClassMethodTranslate:
        def test_with_translator_base_class(self, nodes):
            with pytest.raises(
                dmark.UnhandledNode, match="Unhandled element node 'para'"
            ):
                dmark.Translator.translate(nodes)

        def test_with_custom_translator(self, nodes):
            class CustomTranslator(dmark.Translator):
                @classmethod
                def handle_string(cls, string, context):
                    return [string]

                @classmethod
                def handle_element(cls, element, context):
                    attrs = "".join(
                        " " + k + "=" + v for k, v in element.attributes.items()
                    )
                    return [
                        f"<{element.name}",
                        attrs,
                        ">",
                        cls.handle_children(element, context),
                        f"</{element.name}>",
                    ]

            result = CustomTranslator.translate(nodes)
            assert result == "<para only=web animal=donkey><em>Hello</em> world!</para>"

        def test_with_custom_translator_using_context(self, nodes):
            class CustomTranslator(dmark.Translator):
                @classmethod
                def handle_string(cls, string, context):
                    parent = context.get("kind", "")
                    return [string, f" [parent={parent}]"]

                @classmethod
                def handle_element(cls, element, context):
                    attrs = "".join(
                        " " + k + "=" + v for k, v in element.attributes.items()
                    )
                    new_context = {**context, "kind": element.name}
                    return [
                        f"<{element.name}",
                        attrs,
                        ">",
                        cls.handle_children(element, new_context),
                        f"</{element.name}>",
                    ]

            result = CustomTranslator.translate(nodes)
            assert (
                result
                == "<para only=web animal=donkey><em>Hello [parent=em]</em> world! [parent=para]</para>"
            )

        def test_with_unrecognised_type(self):
            with pytest.raises(TypeError, match="Cannot handle tuple"):
                dmark.Translator.translate([tuple()])

    class TestInstanceMethodTranslate:
        def test_with_translator_base_class(self, translator, nodes):
            with pytest.raises(
                dmark.UnhandledNode, match="Unhandled element node 'para'"
            ):
                translator.translate(nodes)

        def test_with_custom_translator(self, nodes):
            class CustomTranslator(dmark.Translator):
                @classmethod
                def handle_string(cls, string, context):
                    return [string]

                @classmethod
                def handle_element(cls, element, context):
                    attrs = "".join(
                        " " + k + "=" + v for k, v in element.attributes.items()
                    )
                    return [
                        f"<{element.name}",
                        attrs,
                        ">",
                        cls.handle_children(element, context),
                        f"</{element.name}>",
                    ]

            translator = CustomTranslator()
            result = translator.translate(nodes)
            assert result == "<para only=web animal=donkey><em>Hello</em> world!</para>"

        def test_with_custom_translator_using_context(self, nodes):
            class CustomTranslator(dmark.Translator):
                @classmethod
                def handle_string(cls, string, context):
                    parent = context.get("kind", "")
                    return [string, f" [parent={parent}]"]

                @classmethod
                def handle_element(cls, element, context):
                    attrs = "".join(
                        " " + k + "=" + v for k, v in element.attributes.items()
                    )
                    new_context = {**context, "kind": element.name}
                    return [
                        f"<{element.name}",
                        attrs,
                        ">",
                        cls.handle_children(element, new_context),
                        f"</{element.name}>",
                    ]

            translator = CustomTranslator()
            result = translator.translate(nodes)
            assert (
                result
                == "<para only=web animal=donkey><em>Hello [parent=em]</em> world! [parent=para]</para>"
            )

        def test_with_unrecognised_type(self, translator):
            with pytest.raises(TypeError, match="Cannot handle set"):
                translator.translate([set()])
