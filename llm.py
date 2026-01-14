from __future__ import annotations
from typing import Dict, Any
import json

# Requires: pip install openai
try:
    from openai import OpenAI
    import streamlit as st
    import os
    
    # Try to get API key from Streamlit secrets first, then environment variable
    try:
        api_key = st.secrets["openai"]["api_key"]
    except (KeyError, AttributeError):
        api_key = os.getenv("OPENAI_API_KEY", "")
    
    if api_key:
        _client = OpenAI(api_key=api_key)
    else:
        _client = None
except Exception:
    _client = None

SYSTEM_PROMPT = (
    "You are a precise university academic advisor. You will be given: "
    "student info, degree progress summary, and a list of ELIGIBLE courses for the next term. "
    "Recommend a schedule close to the target credits, include 1-2 backups, and provide a short rationale.\n"
    "Rules:\n"
    "- Use ONLY the provided course IDs; do not invent IDs.\n"
    "- Prefer courses that reduce 'remaining' credits in degree progress.\n"
    "- Respect corequisite pairs: if a course requires a partner, include both in the schedule.\n"
    "- If exact target credits can't be reached, choose within ±1 credit when reasonable.\n"
    "Output strict JSON only with keys: schedule, backups, rationale."
)

def plan_with_llm(payload: Dict[str, Any], model: str = "gpt-4o-mini", temperature: float = 0.2) -> Dict[str, Any]:
    if _client is None:
        raise RuntimeError("OpenAI client not available. Did you `pip install openai` and set OPENAI_API_KEY?")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload)}
    ]
    resp = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        data = {"schedule": [], "backups": [], "rationale": "Model returned non-JSON content."}
    data.setdefault("schedule", [])
    data.setdefault("backups", [])
    data.setdefault("rationale", "")
    return data
