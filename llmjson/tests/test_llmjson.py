"""Unit tests for the llmjson package — new code paths."""

import json
import pytest
import numpy as np

from llmjson._types import TokenType
from llmjson._token_mapper import TokenMapper
from llmjson._json_context import JSONContextTracker
from llmjson._vocab_scanner import (
    classify_decoded_token,
    VocabScanner,
    ANDGate,
    EmptyMaskError,
)
from llmjson._schema_validator import validate_schema, UnsupportedSchemaError
from llmjson._generate import _build_prompt


# ── 1. Package imports work ──────────────────────────────────────────────────

class TestPackageImports:
    def test_import_generate(self):
        from llmjson import generate, __version__
        assert callable(generate)
        assert __version__ == "0.1.0"

    def test_import_types(self):
        from llmjson._types import TokenType
        assert TokenType.LBRACE.value == 1

    def test_import_validator(self):
        from llmjson import validate_schema, UnsupportedSchemaError
        assert callable(validate_schema)


# ── 2. Schema Validator ──────────────────────────────────────────────────────

class TestSchemaValidator:
    def test_accepts_simple_object(self):
        validate_schema({"type": "object", "properties": {"name": {"type": "string"}}})

    def test_accepts_nested_object(self):
        validate_schema({
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}}
                }
            }
        })

    def test_accepts_array(self):
        validate_schema({"type": "array", "items": {"type": "string"}})

    def test_accepts_anyof(self):
        validate_schema({
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        })

    def test_accepts_all_primitive_types(self):
        for t in ("string", "integer", "number", "boolean", "null"):
            validate_schema({"type": t})

    def test_rejects_ref(self):
        with pytest.raises(UnsupportedSchemaError, match="\\$ref"):
            validate_schema({"$ref": "#/definitions/Foo"})

    def test_rejects_pattern_properties(self):
        with pytest.raises(UnsupportedSchemaError, match="patternProperties"):
            validate_schema({"patternProperties": {"^S_": {"type": "string"}}})

    def test_rejects_additional_properties(self):
        with pytest.raises(UnsupportedSchemaError, match="additionalProperties"):
            validate_schema({
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            })

    def test_rejects_nested_unsupported(self):
        with pytest.raises(UnsupportedSchemaError, match="name"):
            validate_schema({
                "type": "object",
                "properties": {
                    "name": {"$ref": "#/definitions/Name"}
                }
            })

    def test_error_message_includes_constructs(self):
        with pytest.raises(UnsupportedSchemaError) as exc_info:
            validate_schema({"$ref": "#/foo", "if": True})
        msg = str(exc_info.value)
        assert "$ref" in msg
        assert "if" in msg


# ── 3. AND Gate fail-fast on empty mask ──────────────────────────────────────

class TestANDGateEmptyMask:
    def test_raises_on_empty_mask(self):
        mapper = TokenMapper({0: TokenType.LBRACE})
        gate = ANDGate(mapper, vocab_size=10)
        logits = np.zeros(10, dtype=np.float32)
        with pytest.raises(EmptyMaskError):
            gate.apply(logits, {TokenType.NULL})

    def test_works_with_valid_mask(self):
        mapper = TokenMapper({0: TokenType.LBRACE, 5: TokenType.RBRACE})
        gate = ANDGate(mapper, vocab_size=10)
        logits = np.ones(10, dtype=np.float32)
        gated = gate.apply(logits, {TokenType.LBRACE})
        assert gated[0] == 1.0
        assert gated[5] == -np.inf


# ── 4. TokenMapper returns None for unknown IDs ─────────────────────────────

class TestTokenMapperOptional:
    def test_unknown_id_returns_none(self):
        mapper = TokenMapper({0: TokenType.LBRACE})
        assert mapper.id_to_type(999) is None

    def test_known_id_returns_type(self):
        mapper = TokenMapper({42: TokenType.STRING})
        assert mapper.id_to_type(42) == TokenType.STRING


# ── 5. JSONContextTracker works via llmjson package ──────────────────────────

class TestContextTrackerPackage:
    def test_simple_object(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        ctx = JSONContextTracker(schema)
        for ch in '{"name":"Alice"}':
            ctx.update(ch)
        assert ctx.is_complete()

    def test_array_of_strings(self):
        schema = {"type": "array", "items": {"type": "string"}}
        ctx = JSONContextTracker(schema)
        for ch in '["a","b"]':
            ctx.update(ch)
        assert ctx.is_complete()


# ── 6. classify_decoded_token coverage ───────────────────────────────────────

class TestClassifyToken:
    def test_structural_tokens(self):
        assert classify_decoded_token("{") == TokenType.LBRACE
        assert classify_decoded_token("}") == TokenType.RBRACE
        assert classify_decoded_token("[") == TokenType.LBRACKET
        assert classify_decoded_token("]") == TokenType.RBRACKET
        assert classify_decoded_token(":") == TokenType.COLON
        assert classify_decoded_token(",") == TokenType.COMMA
        assert classify_decoded_token('"') == TokenType.STRING

    def test_literals(self):
        assert classify_decoded_token("true") == TokenType.TRUE
        assert classify_decoded_token("false") == TokenType.FALSE
        assert classify_decoded_token("null") == TokenType.NULL

    def test_numbers(self):
        assert classify_decoded_token("42") == TokenType.NUMBER
        assert classify_decoded_token("-3.14") == TokenType.NUMBER
        assert classify_decoded_token(".") == TokenType.NUMBER

    def test_string_key(self):
        assert classify_decoded_token("name") == TokenType.STRING_KEY

    def test_empty_returns_none(self):
        assert classify_decoded_token("") is None
        assert classify_decoded_token("   ") is None


# ── 7. Chat template builder ────────────────────────────────────────────────

class TestBuildPrompt:
    def test_fallback_without_chat_template(self):
        class FakeTokenizer:
            pass
        tok = FakeTokenizer()
        result = _build_prompt(tok, "test prompt", {"type": "string"})
        assert "<|im_start|>" in result
        assert "test prompt" in result

    def test_uses_apply_chat_template_when_available(self):
        class FakeTokenizer:
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
                return "[CHAT]" + messages[1]["content"]
        tok = FakeTokenizer()
        result = _build_prompt(tok, "hello", {"type": "string"})
        assert result.startswith("[CHAT]")
        assert "hello" in result

    def test_falls_back_on_exception(self):
        class FakeTokenizer:
            def apply_chat_template(self, *a, **kw):
                raise RuntimeError("broken template")
        tok = FakeTokenizer()
        result = _build_prompt(tok, "test", {"type": "string"})
        assert "<|im_start|>" in result


# ── 8. CLI entry point exists ────────────────────────────────────────────────

class TestCLI:
    def test_cli_main_exists(self):
        from llmjson.cli import main
        assert callable(main)

    def test_cli_version(self):
        from llmjson.cli import _get_version
        assert _get_version() == "0.1.0"
