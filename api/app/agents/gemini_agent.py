"""Gemini 2.0 Flash agent for text extraction, chat, and safety checks."""
import json
import logging
import re
from pathlib import Path

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent / "prompts"
_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
    return _model


def get_extraction_prompt() -> str:
    return (PROMPT_DIR / "extraction.md").read_text(encoding="utf-8")


def parse_json_from_response(response_text: str) -> dict | None:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


async def extract_from_text(text: str, client_name: str | None = None) -> dict | None:
    prompt = get_extraction_prompt()
    user_message = text
    if client_name:
        user_message = f"【対象クライアント: {client_name}】\n\n{text}"
    try:
        model = _get_model()
        response = model.generate_content(
            [{"role": "user", "parts": [prompt + "\n\n" + user_message]}],
            generation_config={"temperature": 0},
        )
        return parse_json_from_response(response.text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None


async def chat(message: str, history: list[dict] | None = None) -> str:
    manifesto = (PROMPT_DIR / "manifesto.md").read_text(encoding="utf-8")
    try:
        model = _get_model()
        messages = [{"role": "user", "parts": [
            manifesto + "\n\nあなたは障害福祉支援のアシスタントです。日本語で回答してください。"
        ]}]
        if history:
            for h in history:
                messages.append({"role": h.get("role", "user"), "parts": [h.get("content", "")]})
        messages.append({"role": "user", "parts": [message]})
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return f"エラーが発生しました: {e}"


async def check_safety_compliance(narrative: str, ng_actions: list) -> dict:
    if not ng_actions:
        return {"is_violation": False, "warning": None, "risk_level": "None"}
    safety_prompt = (PROMPT_DIR / "safety.md").read_text(encoding="utf-8")
    safety_prompt = safety_prompt.replace("{ng_actions}", json.dumps(ng_actions, ensure_ascii=False))
    safety_prompt = safety_prompt.replace("{narrative}", narrative)
    try:
        model = _get_model()
        response = model.generate_content(
            [{"role": "user", "parts": [safety_prompt]}],
            generation_config={"temperature": 0},
        )
        match = re.search(r"\{[^}]+\}", response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f"Safety check failed: {e}")
    return {"is_violation": False, "warning": None, "risk_level": "None"}
