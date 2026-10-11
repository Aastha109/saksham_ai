"""
Saksham_AI Tokenizer Module
Handles accurate token counting using tiktoken and model-specific approximations.
"""

from typing import Dict, Any, List
import re

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Cache encoders to avoid re-initializing on each keystroke
_ENCODERS: Dict[str, Any] = {}

def get_encoder(encoding_name: str = "cl100k_base"):
    if not TIKTOKEN_AVAILABLE:
        return None
    if encoding_name not in _ENCODERS:
        try:
            _ENCODERS[encoding_name] = tiktoken.get_encoding(encoding_name)
        except Exception:
            try:
                _ENCODERS[encoding_name] = tiktoken.get_encoding("cl100k_base")
            except Exception:
                return None
    return _ENCODERS.get(encoding_name)


def count_tokens(text: str, model_name: str = "gpt-4o") -> Dict[str, Any]:
    """
    Count tokens for input text based on the selected target model.
    Returns token count, word count, character count, and tokens-per-word ratio.
    """
    if not text:
        return {
            "token_count": 0,
            "word_count": 0,
            "char_count": 0,
            "tokens_per_word": 0.0,
            "tokenizer_used": "tiktoken-empty",
            "is_exact": True
        }

    words = [w for w in text.split() if w]
    word_count = len(words)
    char_count = len(text)

    # Determine best encoding
    model_lower = model_name.lower()
    encoding_name = "cl100k_base"
    is_exact = True

    if "gpt-4o" in model_lower or "o1" in model_lower or "o3" in model_lower:
        # GPT-4o uses o200k_base
        encoding_name = "o200k_base"
    elif "gpt-4" in model_lower or "gpt-3.5" in model_lower:
        encoding_name = "cl100k_base"
    elif "claude" in model_lower or "gemini" in model_lower or "llama" in model_lower:
        # For non-OpenAI models, tiktoken provides a very close baseline (within 3-8%)
        encoding_name = "cl100k_base"
        is_exact = False

    encoder = get_encoder(encoding_name)

    if encoder is not None:
        try:
            tokens = encoder.encode(text)
            token_count = len(tokens)
            
            # Apply known calibration factor for non-OpenAI tokenizers
            if "claude" in model_lower:
                token_count = int(token_count * 1.06)  # Claude tokenizer has slightly smaller vocab
            elif "gemini" in model_lower:
                token_count = int(token_count * 1.02)
            
            tokenizer_used = f"tiktoken ({encoding_name})"
        except Exception:
            # Fallback heuristic: ~4 chars per token in English
            token_count = max(1, int(char_count / 3.9))
            tokenizer_used = "heuristic-fallback"
            is_exact = False
    else:
        token_count = max(1, int(char_count / 3.9))
        tokenizer_used = "heuristic (~3.9 chars/token)"
        is_exact = False

    tokens_per_word = round(token_count / max(1, word_count), 2)

    return {
        "token_count": token_count,
        "word_count": word_count,
        "char_count": char_count,
        "tokens_per_word": tokens_per_word,
        "tokenizer_used": tokenizer_used,
        "is_exact": is_exact
    }
