from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from src.requirement_generator import generate_requirement_candidates
from src.rules import detect_ss_profile, product_sheet_checks, quality_checks

load_dotenv()


def build_sheet_summary(df: pd.DataFrame, sheet_name: str) -> Dict[str, object]:
    checks = quality_checks(df)
    columns = [str(c) for c in df.columns.tolist()]

    numeric_stats: Dict[str, Dict[str, float]] = {}
    numeric = df.select_dtypes(include="number")
    for col in numeric.columns[:10]:
        s = numeric[col].dropna()
        if not s.empty:
            numeric_stats[str(col)] = {
                "min": float(s.min()),
                "max": float(s.max()),
                "mean": float(s.mean()),
            }

    return {
        "sheet": sheet_name,
        "checks": checks,
        "columns": columns,
        "numeric_stats": numeric_stats,
    }


def summarize_workbook(sheets: Dict[str, pd.DataFrame]) -> List[Dict[str, object]]:
    summary = [build_sheet_summary(df, name) for name, df in sheets.items()]

    sheet_names = list(sheets.keys())
    ss_profile = detect_ss_profile(sheet_names)
    profile_entry: Dict[str, object] = {
        "workbook_profile": "S&S Requirements Tool",
        "profile": ss_profile,
    }

    if "Product 1" in sheets:
        profile_entry["product_1_checks"] = product_sheet_checks(sheets["Product 1"])

    profile_entry["draft_requirement_count"] = len(generate_requirement_candidates(sheets))

    summary.append(profile_entry)
    return summary


def ask_ai(question: str, workbook_summary: List[Dict[str, object]]) -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()

    if provider != "openai":
        return (
            "Provider is not set to openai yet. "
            "Set AI_PROVIDER=openai in .env or extend ask_ai for azure_openai/ollama."
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    if not api_key:
        return "OPENAI_API_KEY is missing in .env."

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are a business data analyst for service requirements assessment files. "
        "Use the workbook summary JSON to answer clearly with findings, risks, gaps, and actions."
    )

    user_prompt = (
        "Workbook summary JSON:\n"
        f"{workbook_summary}\n\n"
        f"Question: {question}\n\n"
        "Return concise bullet points with sections: Findings, Risks, Actions."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or "No response from model."
