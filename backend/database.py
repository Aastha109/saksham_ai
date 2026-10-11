"""
Saksham_AI Database & Analytics Layer
SQLite relational storage for prompt usage audit trail, cost accounting,
and business intelligence aggregations.
"""

import sqlite3
import hashlib
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_PATH = os.path.join(DB_DIR, "saksham.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes schema and runs seeding if table is empty."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_hash TEXT NOT NULL,
        prompt_preview TEXT NOT NULL,
        full_prompt TEXT,
        rewritten_prompt TEXT,
        model_used TEXT NOT NULL,
        recommended_model TEXT,
        task_category TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        savings_usd REAL NOT NULL DEFAULT 0.0,
        efficiency_score INTEGER NOT NULL,
        carbon_g REAL NOT NULL,
        team TEXT NOT NULL DEFAULT 'Engineering',
        user_id TEXT NOT NULL DEFAULT 'developer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    # Check if empty; if so, populate with 30-day realistic historical data
    cursor.execute("SELECT COUNT(*) FROM prompt_logs")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_sample_analytics_data(conn)

    conn.close()


def log_prompt_event(
    prompt: str,
    rewritten_prompt: str,
    model_used: str,
    recommended_model: str,
    task_category: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    savings_usd: float,
    efficiency_score: int,
    carbon_g: float,
    team: str = "Core Engineering",
    user_id: str = "current_user"
) -> int:
    """Logs an analyzed or sent prompt to SQL database."""
    conn = get_connection()
    cursor = conn.cursor()

    prompt_hash = hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()[:12]
    preview = prompt.strip()[:140] + ("..." if len(prompt.strip()) > 140 else "")

    total_tokens = input_tokens + output_tokens

    cursor.execute("""
        INSERT INTO prompt_logs (
            prompt_hash, prompt_preview, full_prompt, rewritten_prompt,
            model_used, recommended_model, task_category,
            input_tokens, output_tokens, total_tokens,
            cost_usd, savings_usd, efficiency_score, carbon_g,
            team, user_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        prompt_hash, preview, prompt, rewritten_prompt,
        model_used, recommended_model, task_category,
        input_tokens, output_tokens, total_tokens,
        cost_usd, savings_usd, efficiency_score, carbon_g,
        team, user_id
    ))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def get_kpis() -> Dict[str, Any]:
    """Retrieves high-level executive metrics for BI dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_prompts,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COALESCE(SUM(cost_usd), 0.0) as total_cost,
            COALESCE(SUM(savings_usd), 0.0) as total_savings,
            COALESCE(AVG(efficiency_score), 0.0) as avg_efficiency,
            COALESCE(SUM(carbon_g), 0.0) as total_carbon_g
        FROM prompt_logs
    """)
    row = cursor.fetchone()

    total_cost = round(row["total_cost"], 4)
    total_savings = round(row["total_savings"], 4)
    savings_roi_pct = round((total_savings / max(0.001, total_cost + total_savings)) * 100, 1)

    kpis = {
        "total_prompts": row["total_prompts"],
        "total_tokens": row["total_tokens"],
        "total_cost_usd": total_cost,
        "total_savings_usd": total_savings,
        "savings_roi_pct": savings_roi_pct,
        "avg_efficiency_score": round(row["avg_efficiency"], 1),
        "total_carbon_g": round(row["total_carbon_g"], 2),
        "co2e_avoided_kg": round((row["total_carbon_g"] * 0.35) / 1000.0, 3)
    }
    conn.close()
    return kpis


def get_trend_data(days: int = 30) -> List[Dict[str, Any]]:
    """Returns daily spend, savings, and prompt counts for trend visualization."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT 
            DATE(created_at) as log_date,
            COUNT(*) as prompt_count,
            ROUND(SUM(cost_usd), 4) as daily_spend,
            ROUND(SUM(savings_usd), 4) as daily_savings,
            ROUND(AVG(efficiency_score), 1) as avg_score
        FROM prompt_logs
        WHERE created_at >= DATE('now', '-{days} days')
        GROUP BY DATE(created_at)
        ORDER BY log_date ASC
    """)
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_model_distribution() -> List[Dict[str, Any]]:
    """Returns model breakdown by token share and cost."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            model_used,
            COUNT(*) as count,
            SUM(total_tokens) as total_tokens,
            ROUND(SUM(cost_usd), 4) as total_cost,
            ROUND(SUM(savings_usd), 4) as total_savings
        FROM prompt_logs
        GROUP BY model_used
        ORDER BY total_cost DESC
    """)
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_team_breakdown() -> List[Dict[str, Any]]:
    """Returns per-team usage, spend, and optimization performance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            team,
            COUNT(*) as prompt_count,
            ROUND(SUM(cost_usd), 4) as team_cost,
            ROUND(SUM(savings_usd), 4) as team_savings,
            ROUND(AVG(efficiency_score), 1) as avg_score
        FROM prompt_logs
        GROUP BY team
        ORDER BY team_cost DESC
    """)
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_recent_logs(limit: int = 50, team_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent prompt history rows for data exploration."""
    conn = get_connection()
    cursor = conn.cursor()
    if team_filter and team_filter != "all":
        cursor.execute("""
            SELECT * FROM prompt_logs 
            WHERE team = ?
            ORDER BY created_at DESC LIMIT ?
        """, (team_filter, limit))
    else:
        cursor.execute("""
            SELECT * FROM prompt_logs 
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def seed_sample_analytics_data(conn: sqlite3.Connection):
    """Generates 30 days of realistic multi-team prompt history for rich initial BI display."""
    cursor = conn.cursor()

    teams = ["Core Engineering", "Data & Analytics", "Product Ops", "Customer Success"]
    users = ["dev_arjun", "dev_sophia", "dev_marcus", "analyst_claire", "pm_david"]
    models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-5-haiku", "gemini-1-5-flash"]
    categories = ["simple", "moderate", "complex"]

    sample_prompts = [
        ("Please kindly help me extract the customer order ID and invoice date from this raw receipt text and return as JSON format", "simple", 75, "gpt-4o-mini", 28, 0.0003),
        ("Can you please give me a summary of our weekly sales performance meeting notes and make it look nice and clean with bullets", "moderate", 62, "claude-3-5-haiku", 145, 0.0018),
        ("Architect an event-driven microservices schema for distributed idempotent payment processing with saga orchestration", "complex", 94, "gpt-4o", 280, 0.0125),
        ("I would really like you to translate these 10 short UI strings from English to Spanish and German please kindly format as key value", "simple", 55, "gemini-1-5-flash", 92, 0.0002),
        ("Help me fix this bug in my python code it is not working make it better please thank you so much in advance", "moderate", 42, "gpt-4o", 110, 0.0022),
        ("Classify sentiment of these 5 product reviews as positive, neutral, or negative. Output strict JSON array.", "simple", 96, "gpt-4o-mini", 48, 0.00015),
        ("Perform a comprehensive security audit of this smart contract looking for reentrancy bugs, flash loan attack vectors, and integer overflows", "complex", 88, "claude-3-5-sonnet", 420, 0.0195)
    ]

    base_time = datetime.now() - timedelta(days=28)
    
    # Generate ~110 rows distributed across 28 days
    for day in range(28):
        current_date = base_time + timedelta(days=day)
        daily_count = random.randint(3, 7)
        for _ in range(daily_count):
            prompt_tpl, cat, base_score, rec_model, in_tok, base_cost = random.choice(sample_prompts)
            model_chosen = random.choice(models)
            
            # If they used a heavy model for a simple task, higher potential savings
            if cat == "simple" and "mini" not in model_chosen and "flash" not in model_chosen and "haiku" not in model_chosen:
                savings = round(base_cost * random.uniform(0.75, 0.92), 5)
            else:
                savings = round(base_cost * random.uniform(0.15, 0.40), 5)

            score = max(20, min(100, base_score + random.randint(-15, 12)))
            out_tok = random.randint(50, 450)
            tot_tok = in_tok + out_tok
            carb = round((tot_tok / 1000.0) * random.uniform(0.8, 2.2), 3)

            cursor.execute("""
                INSERT INTO prompt_logs (
                    prompt_hash, prompt_preview, full_prompt, rewritten_prompt,
                    model_used, recommended_model, task_category,
                    input_tokens, output_tokens, total_tokens,
                    cost_usd, savings_usd, efficiency_score, carbon_g,
                    team, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hashlib.md5(f"{day}_{_}".encode()).hexdigest()[:10],
                prompt_tpl[:120] + "...",
                prompt_tpl,
                prompt_tpl.replace("Please kindly ", "").replace("Can you please ", ""),
                model_chosen,
                rec_model,
                cat,
                in_tok,
                out_tok,
                tot_tok,
                round(base_cost * random.uniform(0.8, 1.4), 5),
                savings,
                score,
                carb,
                random.choice(teams),
                random.choice(users),
                (current_date + timedelta(hours=random.randint(8, 19), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S")
            ))

    conn.commit()
