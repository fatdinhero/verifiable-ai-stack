# llmjson

100% valid JSON from local LLMs. Zero retries. Zero post-processing.

Constrained decoding on Apple Silicon via MLX. The model physically cannot produce invalid tokens.

## Install

```bash
pip install jsongate
```

Requires Python 3.9+ and Apple Silicon (M1/M2/M3/M4).

## Quick start

```python
from llmjson import generate

result = generate(
    model_id="mlx-community/Qwen2.5-14B-Instruct-4bit",
    prompt="Generate a person profile for a software engineer named Alice.",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"},
        }
    },
)

print(result.text)      # {"name": "Alice Chen", "age": 32, "email": "alice@eng.dev"}
print(result.is_valid)  # True
```

## CLI

```bash
llmjson generate \
    --model mlx-community/Qwen2.5-14B-Instruct-4bit \
    --schema person.schema.json \
    --prompt "Profile for Alice, a senior engineer"
```

## How it works

1. **VocabScanner** classifies every token in the model's vocabulary into JSON structural types (braces, strings, numbers, literals). Cached to disk per tokenizer.

2. **JSONContextTracker** is a stack-based state machine that follows the JSON being generated character by character. At each step it knows which token types are valid next.

3. **AND Gate** sets the logits of all structurally invalid tokens to negative infinity before the model selects the next token. The model can only choose from valid continuations.

Since every token is constrained to be structurally valid, the complete output is always valid JSON conforming to the schema.

## Benchmark results

80/80 trials passed across Qwen2.5-14B-Instruct-4bit and Llama-3.1-8B-Instruct-4bit. Multiple schema types: flat objects, nested objects, arrays, anyOf unions. Zero failures. Zero retries.

95% CI for true success rate: [95.5%, 100%] (Clopper-Pearson exact method).

## Supported schemas

The 100% guarantee applies to these JSON Schema constructs:

| Construct | Supported |
|-----------|-----------|
| Primitive types (string, number, integer, boolean, null) | Yes |
| Objects with typed properties | Yes |
| Arrays with typed items | Yes |
| Nested objects and arrays | Yes |
| anyOf / oneOf unions | Yes |
| $ref (JSON references) | No |
| patternProperties / additionalProperties | No |
| if / then / else | No |
| regex patterns, minLength, maxLength | No |

Unsupported constructs are rejected upfront with `UnsupportedSchemaError`.

## API

### `generate(model_id, prompt, schema, *, max_tokens=400, verbose=False)`

Returns a `GenerationResult` with:
- `.text` - the generated JSON string
- `.is_valid` - whether the output is valid JSON conforming to the schema
- `.steps` - number of generation steps

### `validate_schema(schema)`

Pre-checks a schema for unsupported constructs. Raises `UnsupportedSchemaError` with details.

## License

MIT
