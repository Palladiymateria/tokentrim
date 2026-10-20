"""tokentrim — Zero-dependency code and context condenser for LLM prompts."""

__version__ = "0.1.0"
__author__ = "Palladiy"

from tokentrim.ast_trimmer import trim_python_code
from tokentrim.polyglot_trimmer import trim_polyglot_code
from tokentrim.token_counter import estimate_tokens, TokenSavings

__all__ = [
    "trim_python_code",
    "trim_polyglot_code",
    "estimate_tokens",
    "TokenSavings",
    "__version__",
]
