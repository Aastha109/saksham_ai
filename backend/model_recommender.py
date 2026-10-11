"""
Saksham_AI Model Recommender
Classifies prompt task complexity and suggests the most cost-effective model,
avoiding expensive overkill on simple tasks.
"""

from typing import Dict, Any, List
import re
from backend.cost_engine import calculate_cost, get_model_pricing

SIMPLE_PATTERNS = [
    r"\b(extract|extraction|json|format|parse|convert|regex|classify|classification|sentiment|filter|deduplicate|tag|categorize|yes\s+or\s+no|true\s+or\s+false|alphabetize|capitalize|lookup|key-value)\b"
]

MODERATE_PATTERNS = [
    r"\b(summarize|summary|rewrite|paraphrase|draft|outline|email|bullet\s+points|explain\s+like|standard\s+qa|faq|product\s+description)\b"
]

COMPLEX_PATTERNS = [
    r"\b(architecture|architectural|system\s+design|mathematical\s+proof|theorem|formal\s+verification|security\s+audit|vulnerability\s+analysis|multi-step\s+reasoning|deep\s+analysis|complex\s+refactor|concurrency|database\s+deadlock|cryptography)\b"
]


def classify_task_complexity(prompt: str) -> Dict[str, Any]:
    """
    Classifies task into 'simple', 'moderate', or 'complex' using
    structural cues, keyword semantics, and prompt length.
    """
    text = prompt.lower().strip()
    words = text.split()
    word_count = len(words)

    simple_hits = sum(1 for p in SIMPLE_PATTERNS if re.search(p, text))
    moderate_hits = sum(1 for p in MODERATE_PATTERNS if re.search(p, text))
    complex_hits = sum(1 for p in COMPLEX_PATTERNS if re.search(p, text))

    # Decision tree logic
    if complex_hits > 0 or word_count > 600:
        complexity = "complex"
        reason = "Detected indicators of advanced multi-step reasoning, architectural design, or deep synthesis."
        confidence = 0.88
    elif simple_hits > 0 and word_count < 150:
        complexity = "simple"
        reason = "Deterministic transformation / extraction / classification with concise boundaries."
        confidence = 0.92
    elif moderate_hits > 0 or (word_count >= 80 and word_count <= 400):
        complexity = "moderate"
        reason = "Standard creative synthesis, summarization, or explanatory task."
        confidence = 0.85
    else:
        if word_count < 50:
            complexity = "simple"
            reason = "Short, single-objective prompt suitable for high-throughput compact models."
            confidence = 0.80
        else:
            complexity = "moderate"
            reason = "General instruction prompt requiring balanced nuance."
            confidence = 0.75

    return {
        "complexity": complexity,
        "reason": reason,
        "confidence": confidence,
        "word_count": word_count
    }


def recommend_model(
    prompt: str,
    current_model: str = "gpt-4o",
    input_tokens: int = 50
) -> Dict[str, Any]:
    """
    Evaluates current model choice vs recommended routing tier and computes delta savings.
    """
    classification = classify_task_complexity(prompt)
    complexity = classification["complexity"]

    # Recommended defaults per complexity tier
    if complexity == "simple":
        target_model = "gpt-4o-mini"
        alternative_models = ["gemini-1-5-flash", "claude-3-5-haiku"]
        guidance = "Simple classification, extraction, and formatting tasks achieve near-identical accuracy on compact models at ~94% lower cost."
    elif complexity == "moderate":
        target_model = "claude-3-5-haiku"
        alternative_models = ["gpt-4o-mini", "llama-3-3-70b"]
        guidance = "Standard summarization and content generation perform exceptionally well on fast sub-frontier models."
    else:  # complex
        target_model = "gpt-4o"
        alternative_models = ["claude-3-5-sonnet", "o3-mini"]
        guidance = "Requires advanced reasoning capabilities and extensive attention nuance; frontier flagship models are recommended."

    current_pricing = get_model_pricing(current_model)
    target_pricing = get_model_pricing(target_model)

    current_cost = calculate_cost(input_tokens, current_model)
    target_cost = calculate_cost(input_tokens, target_model)

    current_usd = current_cost["total_cost_estimate_usd"]
    target_usd = target_cost["total_cost_estimate_usd"]

    cost_saved_usd = max(0.0, current_usd - target_usd)
    pct_saved = round((cost_saved_usd / max(0.000001, current_usd)) * 100, 1) if current_usd > 0 else 0.0

    savings_10k = round(cost_saved_usd * 10_000, 2)
    is_downgrade_recommended = (target_usd < current_usd) and (current_model != target_model)

    return {
        "task_complexity": complexity,
        "classification_reason": classification["reason"],
        "confidence": classification["confidence"],
        "current_model": current_model,
        "current_model_name": current_pricing["name"],
        "recommended_model": target_model,
        "recommended_model_name": target_pricing["name"],
        "alternative_models": alternative_models,
        "is_downgrade_recommended": is_downgrade_recommended,
        "cost_difference_usd": round(cost_saved_usd, 6),
        "pct_cost_saved": pct_saved,
        "savings_10k_requests_usd": savings_10k,
        "guidance": guidance,
        "disclaimer": "Heuristic model recommendation. Benchmark prompt outputs with production test sets before live traffic re-routing."
    }
