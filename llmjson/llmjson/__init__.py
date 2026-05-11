"""llmjson — 100% valid JSON from local LLMs with zero retries."""

__version__ = "0.1.0"

from llmjson._schema_validator import UnsupportedSchemaError, validate_schema
from llmjson._generate import GenerationResult


def generate(
    model_id: str,
    prompt: str,
    schema: dict,
    *,
    max_tokens: int = 400,
    verbose: bool = False,
) -> GenerationResult:
    """Generate guaranteed-valid JSON from a local LLM.

    Args:
        model_id: Hugging Face model ID (e.g. "mlx-community/Qwen2.5-14B-Instruct-4bit")
        prompt: The user prompt describing what JSON to generate
        schema: JSON Schema dict defining the expected output structure
        max_tokens: Maximum tokens to generate (default 400)
        verbose: Print token-by-token generation trace

    Returns:
        GenerationResult with .text (valid JSON string), .is_valid, .steps, .violations

    Raises:
        UnsupportedSchemaError: If the schema uses constructs outside the supported subset
    """
    validate_schema(schema)

    import mlx_lm
    model, tokenizer = mlx_lm.load(model_id)

    from llmjson._generate import generate_json
    return generate_json(
        prompt=prompt,
        schema=schema,
        model=model,
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        verbose=verbose,
    )
