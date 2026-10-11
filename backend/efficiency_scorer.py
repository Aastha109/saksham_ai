"""
Saksham_AI Efficiency Scorer
Rule-based heuristic evaluator scoring prompts from 0 to 100 based on conciseness,
clarity, structure, format constraints, and follow-up prevention.
"""

from typing import Dict, Any, List
import re

# Comprehensive patterns for filler phrases and politeness bloat
FILLER_PATTERNS = [
    (r"\b(please\s+(kindly|can\s+you|could\s+you))\b", "Excessive politeness wrapper"),
    (r"\b(i\s+would\s+(really\s+)?like\s+(you\s+to|it\s+if\s+you))\b", "Conversational intent phrasing"),
    (r"\b(can\s+you\s+(please\s+)?help\s+me\s+(with|to)?)\b", "Conversational request wrapper"),
    (r"\b(i\s+am\s+hoping\s+you\s+can)\b", "Unnecessary preamble"),
    (r"\b(as\s+an\s+ai(\s+language\s+model)?)\b", "Redundant role meta-framing"),
    (r"\b(in\s+order\s+to\s+achieve\s+this)\b", "Verbose transition"),
    (r"\b(feel\s+free\s+to)\b", "Ambiguous permission phrase"),
    (r"\b(if\s+possible\s+could\s+you)\b", "Conditional hesitation"),
    (r"\b(do\s+your\s+best(\s+to)?)\b", "Empty qualitative filler"),
    (r"\b(thank\s+you\s+(so\s+much|in\s+advance|very\s+much)?)\b", "Politeness closing token waste"),
    (r"\b(i\s+need\s+you\s+to)\b", "Wordy preamble"),
    (r"\b(take\s+your\s+time)\b", "Non-actionable filler")
]

# Vague, low-information phrases that cause back-and-forth loops
VAGUE_PATTERNS = [
    (r"\b(make\s+it\s+(better|good|nice|cool|great))\b", "Vague qualitative goal without benchmark"),
    (r"\b(help\s+me\s+with\s+(this|my\s+thing|code))\b", "Undefined scope of work"),
    (r"\b(do\s+something\s+with)\b", "Missing target operation"),
    (r"\b(fix\s+it)\b", "Lacks error message or failure reproduction"),
    (r"\b(improve\s+this)\b", "Ambiguous optimization direction (speed vs readability vs format)"),
    (r"\b(write\s+whatever)\b", "Unconstrained generation")
]

# Strong imperative task verbs
STRONG_VERBS = [
    r"\b(extract|classify|generate|summarize|refactor|convert|parse|calculate|validate|translate|detect|compare|analyze|format|filter|deduplicate|transcribe|debug)\b"
]

# Output formatting indicators
FORMAT_INDICATORS = [
    r"\b(json|xml|markdown|csv|table|bullet\s+points|list|yaml|schema|array|string|boolean|code\s+block|regex)\b",
    r"```[a-z]*"
]

# Structure delimiters
STRUCTURE_DELIMITERS = [
    r"<[a-zA-Z_]+>.*?</[a-zA-Z_]+>",  # XML tags
    r"###?\s+(instructions|context|task|format|constraints|examples|rules)", # Markdown headers
    r"\b(task|context|constraints|output\s+format|format|rules):", # Key-value labels
    r"\[(instructions|context|input)\]" # Bracket tags
]


def score_prompt(text: str) -> Dict[str, Any]:
    """
    Evaluates a prompt string and computes an efficiency score (0-100),
    identifies inefficiencies, and highlights positive attributes.
    """
    if not text or not text.strip():
        return {
            "score": 0,
            "rating": "Empty",
            "rating_color": "neutral",
            "issues": [],
            "positives": [],
            "follow_up_risk": "N/A",
            "deductions": {}
        }

    clean_text = text.strip()
    words = clean_text.split()
    word_count = len(words)
    lower_text = clean_text.lower()

    score = 85  # Starting baseline
    deductions = {
        "fillers": 0,
        "vagueness": 0,
        "redundancy": 0,
        "missing_format": 0,
        "unstructured_bloat": 0
    }
    bonuses = {
        "strong_verb": 0,
        "output_format": 0,
        "structured_delimiters": 0,
        "explicit_constraints": 0
    }

    issues: List[Dict[str, Any]] = []
    positives: List[Dict[str, Any]] = []

    # 1. Check for filler phrases
    filler_matches = []
    for pattern, desc in FILLER_PATTERNS:
        found = re.findall(pattern, lower_text)
        if found:
            for item in found:
                match_str = item[0] if isinstance(item, tuple) else item
                filler_matches.append((match_str, desc))

    if filler_matches:
        count = len(filler_matches)
        penalty = min(25, count * 5)
        deductions["fillers"] = penalty
        score -= penalty
        snippets = list({m[0] for m in filler_matches})[:4]
        issues.append({
            "code": "FILLER_PHRASES",
            "severity": "medium" if count < 3 else "high",
            "title": f"Contains {count} conversational filler phrase{'s' if count > 1 else ''}",
            "description": f"Conversational phrasing like '{', '.join(snippets)}' wastes tokens and conveys zero instruction to the model.",
            "suggestion": "Remove polite preambles and state direct imperative instructions."
        })
    else:
        positives.append({
            "title": "Zero Conversational Fluff",
            "description": "Direct and concise phrasing without unnecessary polite wrappers."
        })

    # 2. Check for vagueness
    vague_matches = []
    for pattern, desc in VAGUE_PATTERNS:
        found = re.findall(pattern, lower_text)
        if found:
            for item in found:
                match_str = item[0] if isinstance(item, tuple) else item
                vague_matches.append((match_str, desc))

    if vague_matches:
        count = len(vague_matches)
        penalty = min(25, count * 10)
        deductions["vagueness"] = penalty
        score -= penalty
        snippets = list({m[0] for m in vague_matches})
        issues.append({
            "code": "VAGUE_INTENT",
            "severity": "high",
            "title": "Vague or unconstrained directive detected",
            "description": f"Phrases like '{', '.join(snippets)}' lack measurable criteria and guarantee costly clarification rounds.",
            "suggestion": "Replace vague directives with explicit acceptance criteria and output boundaries."
        })

    # 3. Check for strong imperative task verb
    has_strong_verb = False
    for pat in STRONG_VERBS:
        if re.search(pat, lower_text):
            has_strong_verb = True
            break

    if has_strong_verb:
        bonuses["strong_verb"] = 5
        score += 5
        positives.append({
            "title": "Clear Imperative Task Verb",
            "description": "Clear action instruction provided (e.g. extract, classify, summarize, refactor)."
        })
    else:
        # If words > 15 and no strong verb
        if word_count > 12:
            penalty = 8
            deductions["vagueness"] += penalty
            score -= penalty
            issues.append({
                "code": "MISSING_TASK_VERB",
                "severity": "medium",
                "title": "Missing clear action verb",
                "description": "The prompt lacks an explicit imperative verb defining the precise transformation requested.",
                "suggestion": "Start your prompt with an active directive like 'Extract...', 'Classify...', or 'Refactor...'."
            })

    # 4. Check for redundant or duplicated sentences/clauses
    sentences = [s.strip().lower() for s in re.split(r"[.\n!?]+", clean_text) if len(s.strip().split()) > 3]
    seen_sentences = set()
    redundancies = 0
    for s in sentences:
        if s in seen_sentences:
            redundancies += 1
        else:
            seen_sentences.add(s)

    if redundancies > 0:
        penalty = min(20, redundancies * 10)
        deductions["redundancy"] = penalty
        score -= penalty
        issues.append({
            "code": "REDUNDANT_REPETITION",
            "severity": "high",
            "title": f"Detected {redundancies} duplicate sentence{'s' if redundancies > 1 else ''}",
            "description": "Repeating instructions wastes prompt tokens and does not reliably increase model compliance.",
            "suggestion": "Consolidate duplicate rules into a single bullet list."
        })

    # 5. Check for output formatting specification
    has_format = False
    for pat in FORMAT_INDICATORS:
        if re.search(pat, lower_text):
            has_format = True
            break

    if has_format:
        bonuses["output_format"] = 5
        score += 5
        positives.append({
            "title": "Explicit Output Format",
            "description": "Output structure is explicitly requested (e.g. JSON, table, markdown, schema)."
        })
    else:
        if word_count > 15:
            penalty = 10
            deductions["missing_format"] = penalty
            score -= penalty
            issues.append({
                "code": "MISSING_FORMAT",
                "severity": "medium",
                "title": "Unspecified output format",
                "description": "Without an explicit format specification, the model defaults to verbose conversational prose.",
                "suggestion": "Specify desired format: 'Return strictly valid JSON', 'Format as a markdown table', etc."
            })

    # 6. Check for structured delimiters
    has_structure = False
    for pat in STRUCTURE_DELIMITERS:
        if re.search(pat, clean_text, re.DOTALL | re.IGNORECASE):
            has_structure = True
            break

    if has_structure:
        bonuses["structured_delimiters"] = 8
        score += 8
        positives.append({
            "title": "Well-Structured Boundaries",
            "description": "Uses clean tags, headers, or delimiters separating instructions from context."
        })
    else:
        # Penalty if prompt is very long without structure
        if word_count > 120 and "\n" not in clean_text:
            penalty = 12
            deductions["unstructured_bloat"] = penalty
            score -= penalty
            issues.append({
                "code": "UNSTRUCTURED_WALL_OF_TEXT",
                "severity": "medium",
                "title": "Unstructured wall of text",
                "description": "Long unformatted text degrades model attention and increases hallucination risks.",
                "suggestion": "Separate context, instructions, and examples using markdown headers or tags."
            })

    # 7. Check for negative constraints
    if re.search(r"\b(do\s+not|never|avoid|must\s+not|forbidden|constraints?:)\b", lower_text):
        bonuses["explicit_constraints"] = 4
        score += 4
        positives.append({
            "title": "Clear Boundary Constraints",
            "description": "Specifies boundary conditions to prevent undesired outputs."
        })

    # Final score clamping
    final_score = max(5, min(100, score))

    # Determine Rating Label & Color
    if final_score >= 85:
        rating = "Optimal"
        rating_color = "emerald"
        follow_up_risk = "Low (< 5% probability)"
    elif final_score >= 70:
        rating = "Good"
        rating_color = "cyan"
        follow_up_risk = "Moderate (~15% probability)"
    elif final_score >= 50:
        rating = "Needs Work"
        rating_color = "amber"
        follow_up_risk = "High (~40% probability)"
    else:
        rating = "Inefficient"
        rating_color = "rose"
        follow_up_risk = "Very High (~70% probability)"

    return {
        "score": final_score,
        "rating": rating,
        "rating_color": rating_color,
        "follow_up_risk": follow_up_risk,
        "issues": issues,
        "positives": positives,
        "deductions": deductions,
        "bonuses": bonuses
    }
