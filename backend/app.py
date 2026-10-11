"""
Saksham_AI FastAPI Main Application Server
Exposes high-speed real-time coaching endpoints, model comparisons,
rewrite diff generators, and BI analytics queries.
"""

import os
import io
import csv
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.tokenizer import count_tokens
from backend.cost_engine import calculate_cost, compare_all_models, MODEL_PRICING
from backend.efficiency_scorer import score_prompt
from backend.rewriter import generate_rewrite_report
from backend.model_recommender import recommend_model
from backend.impact_estimator import estimate_environmental_impact
from backend.database import (
    init_db, log_prompt_event, get_kpis, get_trend_data,
    get_model_distribution, get_team_breakdown, get_recent_logs
)

app = FastAPI(
    title="Saksham_AI API",
    description="Real-time LLM Prompt Coaching, Cost Analysis, and Environmental Impact Intelligence",
    version="2.0.0"
)

# Enable CORS for local development and extension integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Request Models
class AnalyzeRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o"
    expected_output_tokens: Optional[int] = None
    team: Optional[str] = "Core Engineering"
    user_id: Optional[str] = "developer"


class RewriteRequest(BaseModel):
    prompt: str
    model: str = "gpt-4o"


class LogPromptRequest(BaseModel):
    prompt: str
    rewritten_prompt: Optional[str] = ""
    model_used: str = "gpt-4o"
    recommended_model: Optional[str] = "gpt-4o-mini"
    task_category: Optional[str] = "general"
    input_tokens: int
    output_tokens: int = 250
    cost_usd: float
    savings_usd: float = 0.0
    efficiency_score: int
    carbon_g: float
    team: Optional[str] = "Core Engineering"
    user_id: Optional[str] = "developer"


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Saksham_AI Real-time Coaching Engine", "version": "2.0.0"}


@app.get("/api/models")
def list_models():
    """Return model pricing catalog."""
    return {"models": MODEL_PRICING}


@app.post("/api/analyze")
def analyze_prompt(payload: AnalyzeRequest):
    """
    Main real-time coaching endpoint.
    Called on debounced keystrokes (~300-500ms) to provide pre-send intelligence.
    """
    prompt = payload.prompt or ""
    model_key = payload.model or "gpt-4o"

    # 1. Token Counting
    token_stats = count_tokens(prompt, model_key)
    input_tokens = token_stats["token_count"]

    # 2. Efficiency Scoring
    efficiency = score_prompt(prompt)

    # 3. Model Recommendation & Task Classification
    recommendation = recommend_model(prompt, model_key, input_tokens)

    # 4. Cost Calculation (Current Model vs Recommended Model)
    cost_info = calculate_cost(
        input_tokens=input_tokens,
        model_key=model_key,
        expected_output_tokens=payload.expected_output_tokens,
        task_category=recommendation["task_complexity"]
    )

    # 5. Environmental Footprint
    pricing_info = MODEL_PRICING.get(model_key, MODEL_PRICING["gpt-4o"])
    tier = pricing_info.get("tier", "flagship")
    total_estimated_tokens = input_tokens + cost_info["expected_output_tokens"]
    environmental_impact = estimate_environmental_impact(total_estimated_tokens, tier)

    # 6. Rewrite Optimization Report & Diff
    rewrite_report = generate_rewrite_report(prompt, model_key)

    # 7. Model Pricing Matrix (comparison across all models)
    comparison_matrix = compare_all_models(input_tokens, cost_info["expected_output_tokens"])

    return {
        "tokens": token_stats,
        "cost": cost_info,
        "efficiency": efficiency,
        "recommendation": recommendation,
        "environmental_impact": environmental_impact,
        "rewrite": rewrite_report,
        "comparison_matrix": comparison_matrix
    }


@app.post("/api/rewrite")
def rewrite_prompt_endpoint(payload: RewriteRequest):
    """Generate optimized rewrite and fine-grained diff."""
    report = generate_rewrite_report(payload.prompt, payload.model)
    return report


@app.post("/api/log")
def log_prompt_endpoint(payload: LogPromptRequest):
    """Saves a prompt transaction into the SQL database."""
    log_id = log_prompt_event(
        prompt=payload.prompt,
        rewritten_prompt=payload.rewritten_prompt or "",
        model_used=payload.model_used,
        recommended_model=payload.recommended_model or "",
        task_category=payload.task_category or "general",
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        cost_usd=payload.cost_usd,
        savings_usd=payload.savings_usd,
        efficiency_score=payload.efficiency_score,
        carbon_g=payload.carbon_g,
        team=payload.team or "Core Engineering",
        user_id=payload.user_id or "developer"
    )
    return {"status": "success", "log_id": log_id, "message": "Logged to SQL database successfully."}


@app.get("/api/analytics/kpis")
def get_analytics_kpis():
    """Retrieve executive KPIs."""
    return get_kpis()


@app.get("/api/analytics/charts")
def get_analytics_charts():
    """Retrieve aggregated data for BI charts."""
    return {
        "trends": get_trend_data(30),
        "models": get_model_distribution(),
        "teams": get_team_breakdown()
    }


@app.get("/api/analytics/logs")
def get_analytics_logs(limit: int = 50, team: Optional[str] = None):
    """Retrieve tabular prompt audit history."""
    logs = get_recent_logs(limit=limit, team_filter=team)
    return {"logs": logs}


@app.get("/api/analytics/export")
def export_analytics_csv():
    """Exports SQLite usage history to CSV for Power BI / Excel import."""
    logs = get_recent_logs(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Log_ID", "Prompt_Hash", "Model_Used", "Recommended_Model", "Task_Category",
        "Input_Tokens", "Output_Tokens", "Total_Tokens", "Cost_USD", "Savings_USD",
        "Efficiency_Score", "Carbon_g", "Team", "User_ID", "Timestamp"
    ])
    
    for row in logs:
        writer.writerow([
            row["id"], row["prompt_hash"], row["model_used"], row["recommended_model"],
            row["task_category"], row["input_tokens"], row["output_tokens"],
            row["total_tokens"], row["cost_usd"], row["savings_usd"],
            row["efficiency_score"], row["carbon_g"], row["team"], row["user_id"],
            row["created_at"]
        ])
    
    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=saksham_ai_prompt_analytics.csv"}
    )


# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
