"""llmjson quickstart — generate valid JSON from a local LLM."""

from llmjson import generate

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string"},
        "active": {"type": "boolean"},
    },
}

result = generate(
    model_id="mlx-community/Qwen2.5-14B-Instruct-4bit",
    prompt="Generate a person profile for a software engineer named Alice.",
    schema=schema,
)

print(result.text)
print(f"Valid: {result.is_valid} | Steps: {result.steps}")
