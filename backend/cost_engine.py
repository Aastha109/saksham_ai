"""
Saksham_AI Cost Engine Module
Calculates estimated and verifiable API costs based on model pricing tables.
Prices are stored per 1,000,000 tokens for both Input and Output.
"""

from typing import Dict, Any, Optional

# Default Model Pricing Table (USD per 1,000,000 tokens)
# Source: Official provider pricing pages (OpenAI, Anthropic, Google Cloud, Meta)
MODEL_PRICING: Dict[str, Dict[str, Any]] = {
    "gpt-4o": {
        "name": "GPT-4o (Omni)",
        "provider": "OpenAI",
        "tier": "flagship",
        "input_per_m": 2.50,
        "output_per_m": 10.00,
        "typical_output_tokens": 400,
        "description": "High-intelligence flagship multimodal model."
    },
    "gpt-4o-mini": {
        "name": "GPT-4o mini",
        "provider": "OpenAI",
        "tier": "compact",
        "input_per_m": 0.15,
        "output_per_m": 0.60,
        "typical_output_tokens": 300,
        "description": "Fast, cost-efficient small model for lightweight tasks."
    },
    "o1": {
        "name": "OpenAI o1",
        "provider": "OpenAI",
        "tier": "reasoning",
        "input_per_m": 15.00,
        "output_per_m": 60.00,
        "typical_output_tokens": 1200,
        "description": "Deep reasoning model with extensive internal chain of thought."
    },
    "o3-mini": {
        "name": "OpenAI o3-mini",
        "provider": "OpenAI",
        "tier": "reasoning_compact",
        "input_per_m": 1.10,
        "output_per_m": 4.40,
        "typical_output_tokens": 800,
        "description": "Cost-effective reasoning model for coding and logic."
    },
    "claude-3-5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "tier": "flagship",
        "input_per_m": 3.00,
        "output_per_m": 15.00,
        "typical_output_tokens": 450,
        "description": "Industry-leading reasoning, coding, and nuance."
    },
    "claude-3-5-haiku": {
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "tier": "compact",
        "input_per_m": 0.80,
        "output_per_m": 4.00,
        "typical_output_tokens": 300,
        "description": "Blazing fast execution with strong coding & formatting."
    },
    "gemini-1-5-pro": {
        "name": "Gemini 1.5 Pro",
        "provider": "Google",
        "tier": "flagship",
        "input_per_m": 1.25,
        "output_per_m": 5.00,
        "typical_output_tokens": 500,
        "description": "Massive 2M context window for multimodal and deep research."
    },
    "gemini-1-5-flash": {
        "name": "Gemini 1.5 Flash",
        "provider": "Google",
        "tier": "compact",
        "input_per_m": 0.075,
        "output_per_m": 0.30,
        "typical_output_tokens": 300,
        "description": "Extremely low latency and lowest cost per token."
    },
    "llama-3-3-70b": {
        "name": "Llama 3.3 70B",
        "provider": "Meta / Groq",
        "tier": "open_source",
        "input_per_m": 0.59,
        "output_per_m": 0.79,
        "typical_output_tokens": 350,
        "description": "High performance open weights on fast hosted inference."
    },
    "mistral-small": {
        "name": "Mistral Small 3",
        "provider": "Mistral AI",
        "tier": "compact",
        "input_per_m": 0.20,
        "output_per_m": 0.60,
        "typical_output_tokens": 300,
        "description": "Fast, latency-optimized enterprise multilingual model."
    }
}


def get_model_pricing(model_key: str) -> Dict[str, Any]:
    """Retrieve pricing config for a specific model key, defaulting to gpt-4o."""
    return MODEL_PRICING.get(model_key.lower(), MODEL_PRICING["gpt-4o"])


def calculate_cost(
    input_tokens: int,
    model_key: str = "gpt-4o",
    expected_output_tokens: Optional[int] = None,
    task_category: str = "general"
) -> Dict[str, Any]:
    """
    Computes prompt cost estimate with output bounds and scale projections.
    
    Formula:
      Cost = (input_tokens * input_price + output_tokens * output_price) / 1,000,000
    """
    pricing = get_model_pricing(model_key)
    input_rate = pricing["input_per_m"]
    output_rate = pricing["output_per_m"]

    # Calibrate expected output tokens by task category if not supplied
    if expected_output_tokens is None or expected_output_tokens <= 0:
        if task_category == "classification":
            expected_output = 20
        elif task_category == "extraction":
            expected_output = 120
        elif task_category == "formatting":
            expected_output = 180
        elif task_category == "coding":
            expected_output = 600
        elif task_category == "reasoning":
            expected_output = 900
        else:
            expected_output = pricing.get("typical_output_tokens", 350)
    else:
        expected_output = expected_output_tokens

    # Input-only cost (guaranteed pre-send figure)
    input_cost = (input_tokens * input_rate) / 1_000_000.0

    # Expected output cost
    expected_output_cost = (expected_output * output_rate) / 1_000_000.0

    # Total expected cost
    total_cost_estimate = input_cost + expected_output_cost

    # Min/Max range (e.g. short output vs comprehensive output)
    min_output = max(10, int(expected_output * 0.4))
    max_output = int(expected_output * 2.2)
    min_total_cost = input_cost + ((min_output * output_rate) / 1_000_000.0)
    max_total_cost = input_cost + ((max_output * output_rate) / 1_000_000.0)

    # Scale projections
    cost_per_10k = total_cost_estimate * 10_000
    cost_per_100k = total_cost_estimate * 100_000
    cost_per_1m = total_cost_estimate * 1_000_000

    return {
        "model_key": model_key,
        "model_name": pricing["name"],
        "provider": pricing["provider"],
        "input_tokens": input_tokens,
        "expected_output_tokens": expected_output,
        "input_price_per_m": input_rate,
        "output_price_per_m": output_rate,
        "input_cost_usd": round(input_cost, 6),
        "expected_output_cost_usd": round(expected_output_cost, 6),
        "total_cost_estimate_usd": round(total_cost_estimate, 6),
        "cost_range": {
            "min_usd": round(min_total_cost, 6),
            "max_usd": round(max_total_cost, 6),
            "min_output_tokens": min_output,
            "max_output_tokens": max_output
        },
        "scale_projections": {
            "cost_10k_requests_usd": round(cost_per_10k, 2),
            "cost_100k_requests_usd": round(cost_per_100k, 2),
            "cost_1m_requests_usd": round(cost_per_1m, 2)
        }
    }


def compare_all_models(input_tokens: int, expected_output_tokens: int = 350) -> Dict[str, Any]:
    """Generates a matrix comparing current prompt cost across all supported models."""
    comparison = {}
    for key in MODEL_PRICING:
        calc = calculate_cost(input_tokens, key, expected_output_tokens)
        comparison[key] = {
            "name": MODEL_PRICING[key]["name"],
            "provider": MODEL_PRICING[key]["provider"],
            "tier": MODEL_PRICING[key]["tier"],
            "total_cost_usd": calc["total_cost_estimate_usd"],
            "input_per_m": MODEL_PRICING[key]["input_per_m"],
            "output_per_m": MODEL_PRICING[key]["output_per_m"],
            "cost_10k_usd": calc["scale_projections"]["cost_10k_requests_usd"]
        }
    return comparison
