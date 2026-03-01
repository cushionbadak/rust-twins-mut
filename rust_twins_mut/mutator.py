"""Core mutation logic: extract code from LLM responses and apply mutations."""

import re
import sys
import random
from pathlib import Path

# Import GPTOSSClient from the git submodule
sys.path.insert(0, str(Path(__file__).parent.parent / "gpt-oss-20b-google-cloud-call"))
from client import GPTOSSClient

from .prompts import prompt_dict


def extract_rust_code(response: str | None) -> str | None:
    """Extract Rust code from markdown ```rust blocks.

    Matches the original Rust-twins-481C/fuzz/llm.py behaviour:
    returns group(1) without stripping when a block is found,
    returns the raw response otherwise.
    """
    if not response:
        return None

    matched = re.search(r"```rust((.|\n)*?)```", response)
    if matched:
        return matched.group(1)
    return response


def mutate(client: GPTOSSClient, rust_code: str, mutator_name: str) -> str | None:
    """Apply a specific mutation to Rust code via the LLM.

    Args:
        client: GPTOSSClient instance.
        rust_code: Source Rust code to mutate.
        mutator_name: Key into prompt_dict (e.g. "flip_bit").

    Returns:
        Mutated Rust code string, or None on failure.
    """
    if mutator_name not in prompt_dict:
        raise ValueError(f"Unknown mutator: {mutator_name}. "
                         f"Available: {', '.join(prompt_dict.keys())}")

    prompt_template = prompt_dict[mutator_name]
    prompt = f"<s>{prompt_template.format(input=rust_code).strip()}"

    response = client.get_text(prompt)
    return extract_rust_code(response)


def random_mutate(client: GPTOSSClient, rust_code: str) -> tuple[str, str | None]:
    """Pick a random mutation and apply it.

    Returns:
        (mutator_name, mutated_code) tuple.
    """
    mutator_name = random.choice(list(prompt_dict.keys()))
    return mutator_name, mutate(client, rust_code, mutator_name)
