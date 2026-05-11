"""llmjson CLI — Generate guaranteed-valid JSON from local LLMs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="llmjson",
        description="Generate guaranteed-valid JSON from local LLMs with zero retries.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_get_version()}")

    subparsers = parser.add_subparsers(dest="command")

    gen = subparsers.add_parser("generate", help="Generate JSON from a prompt and schema")
    gen.add_argument("--model", required=True, help="Hugging Face model ID")
    gen.add_argument("--schema", required=True, help="Path to JSON Schema file")
    gen.add_argument("--prompt", required=True, help="Prompt describing what to generate")
    gen.add_argument("--max-tokens", type=int, default=400, help="Max tokens (default: 400)")
    gen.add_argument("--verbose", action="store_true", help="Show token-by-token trace")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "generate":
        _cmd_generate(args)


def _cmd_generate(args: argparse.Namespace) -> None:
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    try:
        schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}", file=sys.stderr)
        sys.exit(1)

    from llmjson._schema_validator import validate_schema, UnsupportedSchemaError
    try:
        validate_schema(schema)
    except UnsupportedSchemaError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        import mlx_lm
    except ImportError:
        print(
            "Error: mlx-lm is required. Install with: pip install mlx-lm\n"
            "Note: llmjson requires Apple Silicon (M1/M2/M3/M4).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading model {args.model}...", file=sys.stderr)
    try:
        model, tokenizer = mlx_lm.load(args.model)
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        print("Make sure the model ID is correct. Example: mlx-community/Qwen2.5-14B-Instruct-4bit", file=sys.stderr)
        sys.exit(1)

    from llmjson._generate import generate_json
    result = generate_json(
        prompt=args.prompt,
        schema=schema,
        model=model,
        tokenizer=tokenizer,
        max_tokens=args.max_tokens,
        verbose=args.verbose,
    )

    print(result.text)

    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Valid: {result.is_valid}", file=sys.stderr)
        print(f"Steps: {result.steps}", file=sys.stderr)
        print(f"Violations: {result.violations}", file=sys.stderr)


def _get_version() -> str:
    try:
        from llmjson import __version__
        return __version__
    except ImportError:
        return "unknown"


if __name__ == "__main__":
    main()
