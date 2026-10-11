"""
Saksham_AI Prompt Rewriter & Diff Engine
Generates tightened, high-efficiency prompt rewrites, produces visual diffs,
and calculates projected token and cost savings.
"""

from typing import Dict, Any, List
import re
import difflib
from backend.tokenizer import count_tokens
from backend.cost_engine import calculate_cost

# Common verbose phrases to compact imperatives
COMPACTION_RULES = [
    (r"\bplease\s+(kindly\s+)?(can\s+you\s+)?(help\s+me\s+)?(to\s+)?", ""),
    (r"\bi\s+(would\s+like|need|want)\s+(you\s+to\s+)?", ""),
    (r"\bi\s+am\s+looking\s+to\s+", ""),
    (r"\bi\s+am\s+hoping\s+you\s+can\s+", ""),
    (r"\bas\s+an\s+ai\s+(language\s+model\s*)?,\s*", ""),
    (r"\bfeel\s+free\s+to\s+", ""),
    (r"\bdo\s+your\s+best\s+to\s+", ""),
    (r"\bif\s+possible\s*,?\s*(could\s+you\s*)?", ""),
    (r"\btake\s+your\s+time\s+and\s+", ""),
    (r"\bmake\s+sure\s+(that\s+)?you\s+", "Ensure "),
    (r"\bin\s+order\s+to\s+achieve\s+this\s*,?\s*", ""),
    (r"\bcan\s+you\s+(please\s+)?", ""),
    (r"\bthank\s+you\s+(very\s+much|in\s+advance|so\s+much)?\s*\.?\s*", ""),
    (r"\blet\s+me\s+know\s+if\s+you\s+have\s+any\s+questions\s*\.?\s*", ""),
    (r"\bmake\s+it\s+better\b", "optimize for clarity, conciseness, and precision"),
    (r"\bmake\s+it\s+good\b", "optimize formatting and accuracy")
]


def heuristic_rewrite(prompt: str) -> str:
    """
    Applies deterministic compression rules to prune filler tokens,
    normalize repeated sentences, and sharpen prompt directives.
    """
    if not prompt or not prompt.strip():
        return ""

    text = prompt.strip()

    # 1. Apply compaction rules line by line or phrase by phrase
    for pattern, replacement in COMPACTION_RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 2. Capitalize first letter of sentences
    lines = text.split("\n")
    cleaned_lines = []
    seen_lines = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        # Deduplicate identical instruction lines
        normalized_line = stripped.lower()
        if normalized_line in seen_lines and len(stripped.split()) > 3:
            continue
        seen_lines.add(normalized_line)

        # Capitalize leading character
        stripped = stripped[0].upper() + stripped[1:] if len(stripped) > 1 else stripped.upper()
        # Clean double spaces
        stripped = re.sub(r"\s{2,}", " ", stripped)
        cleaned_lines.append(stripped)

    result = "\n".join(cleaned_lines).strip()

    # 3. Clean consecutive spaces or orphan punctuation
    result = re.sub(r"\s+([.,!?;:])", r"\1", result)
    result = re.sub(r"\n{3,}", "\n\n", result)

    # If the rewritten text is empty or identical, provide a structured template version
    if not result:
        return prompt.strip()

    return result


def compute_word_diff(original: str, rewritten: str) -> List[Dict[str, str]]:
    """
    Computes fine-grained word-by-word diff tags (added, removed, unchanged)
    for interactive visual rendering in UI.
    """
    orig_words = re.findall(r"\S+|\s+", original)
    rewr_words = re.findall(r"\S+|\s+", rewritten)

    matcher = difflib.SequenceMatcher(None, orig_words, rewr_words)
    diff_tokens: List[Dict[str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diff_tokens.append({
                "type": "equal",
                "text": "".join(orig_words[i1:i2])
            })
        elif tag == "delete":
            diff_tokens.append({
                "type": "removed",
                "text": "".join(orig_words[i1:i2])
            })
        elif tag == "insert":
            diff_tokens.append({
                "type": "added",
                "text": "".join(rewr_words[j1:j2])
            })
        elif tag == "replace":
            diff_tokens.append({
                "type": "removed",
                "text": "".join(orig_words[i1:i2])
            })
            diff_tokens.append({
                "type": "added",
                "text": "".join(rewr_words[j1:j2])
            })

    return diff_tokens


def generate_rewrite_report(
    original_prompt: str,
    model_key: str = "gpt-4o",
    custom_rewrite: str = None
) -> Dict[str, Any]:
    """
    Executes rewrite, measures token reduction and economic savings,
    and returns a side-by-side diff package.
    """
    original_prompt = original_prompt.strip()
    if not original_prompt:
        return {
            "original_prompt": "",
            "rewritten_prompt": "",
            "tokens_original": 0,
            "tokens_rewritten": 0,
            "tokens_saved": 0,
            "pct_token_reduction": 0.0,
            "cost_original_usd": 0.0,
            "cost_rewritten_usd": 0.0,
            "cost_saved_usd": 0.0,
            "savings_10k_requests_usd": 0.0,
            "diff_stream": [],
            "breakeven_explanation": "Enter a prompt to calculate rewrite savings."
        }

    rewritten_prompt = custom_rewrite if custom_rewrite is not None else heuristic_rewrite(original_prompt)

    # Token counts
    orig_stats = count_tokens(original_prompt, model_key)
    rewr_stats = count_tokens(rewritten_prompt, model_key)

    orig_tokens = orig_stats["token_count"]
    rewr_tokens = rewr_stats["token_count"]

    tokens_saved = max(0, orig_tokens - rewr_tokens)
    pct_reduction = round((tokens_saved / max(1, orig_tokens)) * 100, 1)

    # Cost calculations
    orig_cost = calculate_cost(orig_tokens, model_key)
    rewr_cost = calculate_cost(rewr_tokens, model_key)

    cost_orig = orig_cost["total_cost_estimate_usd"]
    cost_rewr = rewr_cost["total_cost_estimate_usd"]
    cost_saved = max(0.0, round(cost_orig - cost_rewr, 6))

    savings_10k = round(cost_saved * 10_000, 2)
    savings_100k = round(cost_saved * 100_000, 2)

    diff_stream = compute_word_diff(original_prompt, rewritten_prompt)

    # Interview Trade-off rationale:
    # A rewrite call itself costs tokens (~30-50 tokens for rewriter instruction).
    # If using LLM rewrite, breakeven is reached when prompt is called >= 2-3 times.
    # In heuristic/local mode, cost is $0.00 so breakeven is immediate!
    breakeven_explanation = (
        f"This rewrite trims {tokens_saved} input tokens ({pct_reduction}% reduction). "
        f"For batch processing or repeated system prompts, this saves ${savings_10k:,.2f} per 10k calls. "
        f"Because Saksham_AI uses a deterministic zero-cost local compression engine, savings are instantaneous with $0 overhead."
    )

    return {
        "original_prompt": original_prompt,
        "rewritten_prompt": rewritten_prompt,
        "tokens_original": orig_tokens,
        "tokens_rewritten": rewr_tokens,
        "tokens_saved": tokens_saved,
        "pct_token_reduction": pct_reduction,
        "cost_original_usd": cost_orig,
        "cost_rewritten_usd": cost_rewr,
        "cost_saved_usd": cost_saved,
        "savings_10k_requests_usd": savings_10k,
        "savings_100k_requests_usd": savings_100k,
        "diff_stream": diff_stream,
        "breakeven_explanation": breakeven_explanation
    }
