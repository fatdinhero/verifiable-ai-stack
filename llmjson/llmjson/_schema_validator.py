from __future__ import annotations


class UnsupportedSchemaError(Exception):
    pass


_UNSUPPORTED_KEYWORDS = frozenset({
    "$ref", "patternProperties", "additionalProperties",
    "if", "then", "else", "not",
    "dependentSchemas", "dependentRequired",
    "unevaluatedProperties", "unevaluatedItems",
    "prefixItems", "contains",
})

_SUPPORTED_TYPES = frozenset({
    "object", "array", "string", "integer", "number", "boolean", "null",
})


def validate_schema(schema: dict, _path: str = "") -> None:
    if not isinstance(schema, dict):
        return

    found = _UNSUPPORTED_KEYWORDS & schema.keys()
    if found:
        loc = f" at '{_path}'" if _path else ""
        raise UnsupportedSchemaError(
            f"Unsupported schema constructs{loc}: {', '.join(sorted(found))}. "
            f"llmjson supports: object, array, string, integer, number, boolean, null, anyOf, oneOf."
        )

    t = schema.get("type")
    if t and t not in _SUPPORTED_TYPES:
        loc = f" at '{_path}'" if _path else ""
        raise UnsupportedSchemaError(
            f"Unsupported type '{t}'{loc}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_TYPES))}."
        )

    if "properties" in schema:
        for key, sub in schema["properties"].items():
            validate_schema(sub, _path=f"{_path}.{key}" if _path else key)

    if "items" in schema:
        validate_schema(schema["items"], _path=f"{_path}[]")

    for kw in ("anyOf", "oneOf"):
        if kw in schema:
            for i, branch in enumerate(schema[kw]):
                validate_schema(branch, _path=f"{_path}.{kw}[{i}]")
